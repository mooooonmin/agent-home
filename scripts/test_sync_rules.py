"""sync_rules.py 테스트. 저장소 내용 대신 임시 폴더에 만든 가짜 claude-home을 원본으로 씁니다.

실행:  python -I -m unittest discover -s scripts -p "test_*.py"
"""
import contextlib
import hashlib
import importlib.util
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location("sync_rules", HERE / "sync_rules.py")
sync_rules = importlib.util.module_from_spec(spec)
sys.modules["sync_rules"] = sync_rules  # dataclass가 모듈을 찾을 수 있게 등록
spec.loader.exec_module(sync_rules)

BLOCK = f"{sync_rules.BLOCK_START}\n## 공통 규칙\n\n- 규칙 하나\n{sync_rules.BLOCK_END}"
LEGACY_TEXT = "# 기본 규칙\n\n- claude-home에서 복사한 그대로\n"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class Workspace:
    """가짜 claude-home(source)과 대상 폴더(target), 가짜 홈(home)."""

    def __enter__(self):
        self._dir = tempfile.TemporaryDirectory()
        base = Path(self._dir.name)
        self.source, self.target, self.home = base / "claude-home", base / "my-app", base / "home"
        self.target.mkdir()
        self.home.mkdir()
        write(self.source / "AGENTS.md", f"# claude-home\n\n안내\n\n{BLOCK}\n")
        write(self.source / ".claude/rules/lang/python.md", "# Python 규칙\n")
        write(self.source / ".claude/rules/lang/go.md", "# Go 규칙\n")
        write(self.source / ".claude/rules/translation.md", "# 번역 규칙\n")
        for name in sync_rules.COMMON_RULE_FILES:
            write(self.source / ".claude/rules" / name, f"# {name}\n")
        for name in ("update-docs", "translate-chapter", "review-translation", "research"):
            write(self.source / f".agents/skills/{name}/SKILL.md", f"---\nname: {name}\ndescription: 설명\n---\n")
        for script in sync_rules.CHECK_SCRIPTS:
            write(self.source / "templates/ci" / script, f"# {script}\n")
        for _, template in sync_rules.AGENT_SETTINGS:
            write(self.source / template, '{"hooks": "python -I scripts/agent_hooks.py"}\n')
        known = frozenset({hashlib.sha256(LEGACY_TEXT.encode("utf-8")).hexdigest()})
        self._patches = [
            mock.patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": "", "CODEX_HOME": ""}),
            mock.patch.object(sync_rules, "KNOWN_LEGACY_SHA256", known),
        ]
        for patch in self._patches:
            patch.start()
        return self

    def __exit__(self, *exc):
        for patch in self._patches:
            patch.stop()
        self._dir.cleanup()


def changed(plan, base):
    return {c.path.relative_to(base).as_posix(): c.note for c in plan.changes}


def deleted(plan, base):
    return sorted(c.path.relative_to(base).as_posix() for c in plan.changes if c.content is None)


class MergeBlockTest(unittest.TestCase):
    def test_표시_사이만_바꾸고_저장소_안내는_남긴다(self):
        old = f"# 앱\n\n저장소 안내\n\n{sync_rules.BLOCK_START}\n옛 규칙\n{sync_rules.BLOCK_END}\n\n뒤쪽 메모\n"
        merged = sync_rules.merge_block(old, BLOCK)
        self.assertIn("저장소 안내", merged)
        self.assertIn("뒤쪽 메모", merged)
        self.assertIn("규칙 하나", merged)
        self.assertNotIn("옛 규칙", merged)

    def test_표시가_없으면_맨_아래에_붙인다(self):
        merged = sync_rules.merge_block("# 내 Codex 설정\n", BLOCK)
        self.assertTrue(merged.startswith("# 내 Codex 설정\n\n"))
        self.assertTrue(merged.endswith(f"{sync_rules.BLOCK_END}\n"))

    def test_표시가_한쪽만_있으면_덧붙이지_않고_멈춘다(self):
        half = f"# 앱\n\n{sync_rules.BLOCK_START}\n옛 규칙\n\n프로젝트 메모\n"
        with self.assertRaises(ValueError):
            sync_rules.merge_block(half, BLOCK)

    def test_원본에_표시가_없으면_실패한다(self):
        with self.assertRaises(ValueError):
            sync_rules.extract_block("# 표시 없음\n")


class ProjectTest(unittest.TestCase):
    def test_빈_프로젝트에_규칙_스킬_검사도구를_넣는다(self):
        with Workspace() as ws:
            plan = sync_rules.plan_project(ws.source, ws.target, {"python"})
            paths = changed(plan, ws.target)
            for expected in (
                "AGENTS.md", "CLAUDE.md", ".claude/rules/lang/python.md",
                ".claude/rules/code.md", ".claude/rules/writing-docs.md",
                ".agents/skills/update-docs/SKILL.md", ".claude/skills/update-docs/SKILL.md",
                "scripts/repo_checks.py", "scripts/agent_hooks.py", ".claude/settings.json", ".codex/hooks.json",
            ):
                self.assertIn(expected, paths)
            self.assertNotIn(".claude/rules/lang/go.md", paths)
            self.assertNotIn(".claude/rules/translation.md", paths)

    def test_미리보기는_파일을_쓰지_않는다(self):
        with Workspace() as ws:
            sync_rules.plan_project(ws.source, ws.target, {"python"})
            self.assertEqual(list(ws.target.iterdir()), [])

    def test_반영한_뒤_다시_돌리면_바꿀_것이_없다(self):
        with Workspace() as ws:
            sync_rules.apply(sync_rules.plan_project(ws.source, ws.target, {"python", sync_rules.TRANSLATION}))
            again = sync_rules.plan_project(ws.source, ws.target, set())
            self.assertEqual(again.changes, [])
            self.assertEqual(again.warnings, [])

    def test_줄바꿈만_다른_AGENTS_md는_바꾸지_않는다(self):
        with Workspace() as ws:
            sync_rules.apply(sync_rules.plan_project(ws.source, ws.target, set()))
            agents = ws.target / "AGENTS.md"
            agents.write_bytes(agents.read_bytes().replace(b"\n", b"\r\n"))
            self.assertNotIn("AGENTS.md", changed(sync_rules.plan_project(ws.source, ws.target, set()), ws.target))

    def test_이미_있는_언어와_번역_규칙은_계속_갱신한다(self):
        with Workspace() as ws:
            write(ws.target / ".claude/rules/lang/go.md", "# 옛 Go 규칙\n")
            write(ws.target / ".claude/rules/translation.md", "# 옛 번역 규칙\n")
            paths = changed(sync_rules.plan_project(ws.source, ws.target, set()), ws.target)
            self.assertIn(".claude/rules/lang/go.md", paths)
            self.assertIn(".claude/rules/translation.md", paths)
            self.assertIn(".agents/skills/translate-chapter/SKILL.md", paths)

    def test_원본에_없는_스킬_파일은_지운다(self):
        with Workspace() as ws:
            write(ws.target / ".agents/skills/update-docs/references/old.md", "옛 참고\n")
            write(ws.target / ".claude/skills/update-docs/references/old.md", "옛 참고\n")
            plan = sync_rules.plan_project(ws.source, ws.target, set())
            self.assertEqual(
                deleted(plan, ws.target),
                [".agents/skills/update-docs/references/old.md", ".claude/skills/update-docs/references/old.md"],
            )

    def test_claude_home_사본_그대로인_예전_규칙과_명령어만_지운다(self):
        with Workspace() as ws:
            write(ws.target / ".claude/rules/basics.md", LEGACY_TEXT)
            write(ws.target / ".claude/commands/update-docs.md", LEGACY_TEXT)
            write(ws.target / ".claude/rules/git.md", LEGACY_TEXT + "- 이 프로젝트만의 브랜치 규칙\n")
            plan = sync_rules.plan_project(ws.source, ws.target, set())
            self.assertEqual(deleted(plan, ws.target), [".claude/commands/update-docs.md", ".claude/rules/basics.md"])
            self.assertEqual(len(plan.warnings), 1)
            self.assertIn("git.md", plan.warnings[0])

    def test_가져오기_줄이_없는_CLAUDE_md는_고치지_않고_알린다(self):
        with Workspace() as ws:
            write(ws.target / "CLAUDE.md", "# 내 프로젝트\n")
            plan = sync_rules.plan_project(ws.source, ws.target, set())
            self.assertNotIn("CLAUDE.md", changed(plan, ws.target))
            self.assertEqual(len(plan.warnings), 1)
            self.assertIn("@AGENTS.md", plan.warnings[0])

    def test_이미_있는_설정은_덮어쓰지_않고_훅이_없으면_알린다(self):
        with Workspace() as ws:
            write(ws.target / ".claude/settings.json", '{"permissions": {}}\n')
            plan = sync_rules.plan_project(ws.source, ws.target, set())
            paths = changed(plan, ws.target)
            self.assertNotIn(".claude/settings.json", paths)
            self.assertIn(".codex/hooks.json", paths)
            self.assertEqual(len(plan.warnings), 1)
            self.assertIn("settings.json", plan.warnings[0])

    def test_상대_경로로_가져오는_CLAUDE_md도_인정한다(self):
        with Workspace() as ws:
            write(ws.target / "CLAUDE.md", "@./AGENTS.md \n")
            self.assertEqual(sync_rules.plan_project(ws.source, ws.target, set()).warnings, [])


class UserTest(unittest.TestCase):
    def test_사용자_설정에_넣고_내_Codex_지시는_남긴다(self):
        with Workspace() as ws:
            write(ws.home / ".codex/AGENTS.md", "# 내 지시\n")
            write(ws.home / ".claude/rules/coding.md", LEGACY_TEXT)
            write(ws.home / ".claude/commands/research.md", LEGACY_TEXT)
            sync_rules.apply(sync_rules.plan_user(ws.source, ws.home))
            codex = (ws.home / ".codex/AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("# 내 지시", codex)
            self.assertIn("규칙 하나", codex)
            self.assertTrue((ws.home / ".claude/rules/claude-home.md").is_file())
            self.assertTrue((ws.home / ".claude/rules/lang/python.md").is_file())
            self.assertTrue((ws.home / ".agents/skills/research/SKILL.md").is_file())
            self.assertTrue((ws.home / ".claude/skills/research/SKILL.md").is_file())
            self.assertFalse((ws.home / ".claude/rules/coding.md").exists())
            self.assertFalse((ws.home / ".claude/commands/research.md").exists())

    def test_이름만_같은_내_파일은_지우지_않는다(self):
        with Workspace() as ws:
            write(ws.home / ".claude/rules/git.md", "# 내가 쓴 git 규칙\n")
            plan = sync_rules.plan_user(ws.source, ws.home)
            sync_rules.apply(plan)
            self.assertTrue((ws.home / ".claude/rules/git.md").is_file())
            self.assertEqual(len(plan.warnings), 1)


class MirrorTest(unittest.TestCase):
    def test_원본에_없는_사본_스킬은_지운다(self):
        with Workspace() as ws:
            write(ws.source / ".claude/skills/old/SKILL.md", "옛 스킬\n")
            write(ws.source / ".claude/skills/research/extra.md", "원본에 없는 파일\n")
            plan = sync_rules.plan_mirror(ws.source)
            self.assertIn(".claude/skills/research/SKILL.md", changed(plan, ws.source))
            self.assertEqual(
                deleted(plan, ws.source), [".claude/skills/old/SKILL.md", ".claude/skills/research/extra.md"]
            )
            sync_rules.apply(plan)  # 같은 파일을 두 번 지우려 하지 않는지도 확인


class CliTest(unittest.TestCase):
    def test_target_없이_lang을_주면_멈춘다(self):
        with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
            sync_rules.main(["--user", "--lang", "python"])


if __name__ == "__main__":
    unittest.main()

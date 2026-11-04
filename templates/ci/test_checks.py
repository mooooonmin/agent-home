"""repo_checks.py와 check_doc_links.py 자체를 검사하는 테스트입니다.

실행:  python3 -m unittest discover -s scripts -p "test_*.py"
"""
import importlib.util
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


doc_links = load("check_doc_links")
repo_checks = load("repo_checks")


class TempRepo:
    """git이 없는 임시 폴더. 두 스크립트 모두 폴더 탐색으로 대체합니다."""

    def __enter__(self):
        self._dir = tempfile.TemporaryDirectory()
        self.root = Path(self._dir.name)
        return self

    def __exit__(self, *exc):
        self._dir.cleanup()

    def write(self, rel, text):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


class DocLinksTest(unittest.TestCase):
    def errors(self, repo):
        root = str(repo.root)
        return [e for rel in doc_links.list_markdown(root, []) for e in doc_links.check(root, rel)]

    def test_한국어_제목_앵커와_중복_제목은_통과한다(self):
        with TempRepo() as repo:
            repo.write("a.md", "# 함수는 한 가지 일만 해야 합니다\n## Setup (v2)\n## Setup (v2)\n")
            repo.write("sub/b.md", "[가](../a.md#함수는-한-가지-일만-해야-합니다)\n[나](../a.md#setup-v2-1)\n")
            self.assertEqual(self.errors(repo), [])

    def test_없는_파일과_없는_앵커를_찾는다(self):
        with TempRepo() as repo:
            repo.write("a.md", "# 제목\n")
            repo.write("b.md", "[x](nope.md)\n[y](a.md#없는-제목)\n")
            errors = self.errors(repo)
            self.assertEqual(len(errors), 2)
            self.assertIn("없는 파일", errors[0])
            self.assertIn("없는 제목 앵커", errors[1])

    def test_이모지로_시작하는_제목_앵커를_맞춘다(self):
        with TempRepo() as repo:
            repo.write("a.md", "## ⚠️ 먼저 읽어 주세요 — 사용 범위\n")
            repo.write("b.md", "[x](a.md#️-먼저-읽어-주세요--사용-범위)\n")
            self.assertEqual(self.errors(repo), [])

    def test_UTF8이_아닌_문서는_멈추지_않고_알린다(self):
        with TempRepo() as repo:
            (repo.root / "utf16.md").write_text("# 제목\n", encoding="utf-16")
            errors = self.errors(repo)
            self.assertEqual(len(errors), 1)
            self.assertIn("UTF-8", errors[0])

    def test_코드_블록과_외부_링크는_건너뛴다(self):
        with TempRepo() as repo:
            repo.write("a.md", "`[x](nope.md)`\n```\n[y](nope2.md)\n```\n[z](https://example.com/none)\n")
            self.assertEqual(self.errors(repo), [])


class RepoChecksTest(unittest.TestCase):
    def test_고정하지_않은_의존성을_찾는다(self):
        with TempRepo() as repo:
            repo.write("requirements.txt", "requests==2.32.3\nfastapi>=0.110\n# 주석\n-r base.txt\n")
            errors = repo_checks.check_pinned_requirements(repo.root, ["requirements.txt"])
            self.assertEqual(len(errors), 1)
            self.assertIn("fastapi", errors[0])

    def test_latest_태그를_찾는다(self):
        with TempRepo() as repo:
            repo.write("compose.yml", "services:\n  db:\n    image: postgres:latest\n  app:\n    image: app:1.2.0\n")
            repo.write("Dockerfile", "FROM python:latest\n")
            errors = repo_checks.check_latest_tags(repo.root, ["compose.yml", "Dockerfile"])
            self.assertEqual(len(errors), 2)

    def test_생성_산출물을_찾는다(self):
        files = [
            "src/app.py", "src/__pycache__/app.cpython-312.pyc", "node_modules/x/index.js", "README.md",
            "logs/run.txt", "web/src/app/system/logs/page.tsx",
        ]
        errors = repo_checks.check_generated(files)
        self.assertEqual(len(errors), 3)
        self.assertFalse(any("page.tsx" in e for e in errors))

    def test_병합_충돌_표시를_찾는다(self):
        with TempRepo() as repo:
            repo.write("a.py", "x = 1\n<<<<<<< HEAD\ny = 2\n=======\ny = 3\n>>>>>>> feature\n")
            errors = repo_checks.check_conflict_markers(repo.root, ["a.py"])
            self.assertEqual(len(errors), 2)

    def test_문서_검사에서만_뺀_폴더도_생성물은_검사한다(self):
        with TempRepo() as repo:
            repo.write("templates/a.md", "[자리표시](<경로>.md)\n")
            repo.write("templates/__pycache__/x.pyc", "")
            errors = repo_checks.run_all(repo.root, [], ["templates"])
            self.assertEqual(len(errors), 1)
            self.assertIn("__pycache__", errors[0])

    def test_Codex_한도를_넘는_AGENTS_md를_찾는다(self):
        with TempRepo() as repo:
            repo.write("AGENTS.md", "가" * 8000)  # 한글 한 글자 = 3바이트
            repo.write("pkg/AGENTS.md", "가" * 4000)
            errors = repo_checks.check_agents_md_size(repo.root, ["AGENTS.md", "pkg/AGENTS.md"])
            self.assertEqual(len(errors), 1)
            self.assertIn("pkg/AGENTS.md", errors[0])

    def test_AGENTS_md를_가져오지_않는_CLAUDE_md를_찾는다(self):
        with TempRepo() as repo:
            repo.write("AGENTS.md", "# 안내\n")
            repo.write("CLAUDE.md", "# 다른 지시\n")
            repo.write("ok/AGENTS.md", "# 안내\n")
            repo.write("ok/CLAUDE.md", "@./AGENTS.md \n")
            repo.write("solo/CLAUDE.md", "# AGENTS.md 없음\n")
            files = ["AGENTS.md", "CLAUDE.md", "ok/AGENTS.md", "ok/CLAUDE.md", "solo/CLAUDE.md"]
            errors = repo_checks.check_claude_imports_agents(repo.root, files)
            self.assertEqual(len(errors), 1)
            self.assertTrue(errors[0].startswith("CLAUDE.md:"))

    def test_위쪽_CLAUDE_md에_가려진_하위_AGENTS_md를_찾는다(self):
        with TempRepo() as repo:
            repo.write("AGENTS.md", "# 안내\n")
            repo.write("CLAUDE.md", "@AGENTS.md\n")
            repo.write("pkg/AGENTS.md", "# 하위 안내\n")
            repo.write("other/AGENTS.md", "# CLAUDE.md 없는 저장소 일부\n")
            files = ["AGENTS.md", "CLAUDE.md", "pkg/AGENTS.md", "other/AGENTS.md"]
            errors = repo_checks.check_claude_imports_agents(repo.root, files)
            self.assertEqual(len(errors), 2)
            self.assertTrue(all("위쪽 폴더의 CLAUDE.md" in e for e in errors))

    def test_CLAUDE_md가_없으면_AGENTS_md만으로_통과한다(self):
        with TempRepo() as repo:
            repo.write("AGENTS.md", "# 안내\n")
            repo.write("pkg/AGENTS.md", "# 하위 안내\n")
            self.assertEqual(repo_checks.check_claude_imports_agents(repo.root, ["AGENTS.md", "pkg/AGENTS.md"]), [])

    def test_스킬_원본과_사본이_다르면_알린다(self):
        with TempRepo() as repo:
            repo.write(".agents/skills/a/SKILL.md", "원본\n")
            repo.write(".claude/skills/a/SKILL.md", "고친 사본\n")
            repo.write(".agents/skills/b/SKILL.md", "원본\n")
            repo.write(".claude/skills/c/SKILL.md", "원본 없음\n")
            files = [".agents/skills/a/SKILL.md", ".claude/skills/a/SKILL.md", ".agents/skills/b/SKILL.md",
                     ".claude/skills/c/SKILL.md"]
            errors = repo_checks.check_skill_mirror(repo.root, files)
            self.assertEqual(len(errors), 3)

    def test_한쪽_스킬_폴더만_쓰면_검사하지_않는다(self):
        with TempRepo() as repo:
            repo.write(".agents/skills/a/SKILL.md", "원본\n")
            self.assertEqual(repo_checks.check_skill_mirror(repo.root, [".agents/skills/a/SKILL.md"]), [])

    def test_훅_설정이_가리키는_스크립트가_없으면_알린다(self):
        with TempRepo() as repo:
            repo.write(".claude/settings.json", '{"args": ["-I", "${CLAUDE_PROJECT_DIR}/scripts/agent_hooks.py"]}')
            repo.write(".codex/hooks.json", '{"command": "python -I scripts/agent_hooks.py pre-bash"}')
            files = [".claude/settings.json", ".codex/hooks.json"]
            self.assertEqual(len(repo_checks.check_hook_scripts(repo.root, files)), 2)
            repo.write("scripts/agent_hooks.py", "")
            self.assertEqual(repo_checks.check_hook_scripts(repo.root, files), [])

    def test_깨끗한_저장소는_통과한다(self):
        with TempRepo() as repo:
            repo.write("README.md", "# 프로젝트\n\n[문서](docs/guide.md)\n")
            repo.write("docs/guide.md", "# 안내\n")
            repo.write("requirements.txt", "requests==2.32.3\n")
            self.assertEqual(repo_checks.run_all(repo.root, []), [])


if __name__ == "__main__":
    unittest.main()

"""new_project.py 테스트. 실제 claude-home 템플릿으로 임시 폴더에 프로젝트를 만들고,
만들어진 프로젝트에서 저장소 검사가 통과하는지 확인합니다. 규칙·템플릿을 고친 뒤 새 프로젝트가 깨지지 않게 하는 안전장치입니다.

실행:  python -I -m unittest discover -s scripts -p "test_*.py"
"""
import contextlib
import importlib.util
import io
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location("new_project", HERE / "new_project.py")
new_project = importlib.util.module_from_spec(spec)
sys.modules["new_project"] = new_project  # dataclass가 모듈을 찾을 수 있게 등록
spec.loader.exec_module(new_project)

SOURCE = new_project.SOURCE_ROOT
TODAY = "2026-01-02"
# AGENTS.md 한도(200줄) 안에서 자리표시를 실제 내용으로 채울 여유 20줄을 남깁니다.
MAX_GENERATED_AGENTS_LINES = 180


def request_for(parent: Path, language: str, translation: bool = False) -> "new_project.ProjectRequest":
    return new_project.ProjectRequest("demo-app", language, "시험용 앱", translation, parent / "demo-app")


def run_in(project: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-I", *args], cwd=project, capture_output=True, text=True, encoding="utf-8")


class NewProjectTest(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.parent = Path(self._dir.name)

    def tearDown(self):
        self._dir.cleanup()

    def test_미리보기는_아무것도_만들지_않고_실제로_만들_파일과_같다(self):
        request = request_for(self.parent, "python")
        planned = {c.path for c in new_project.preview(SOURCE, request, TODAY).changes}
        self.assertFalse(request.target.exists())
        created = {c.path for c in new_project.create(SOURCE, request, TODAY).changes}
        self.assertEqual(planned, created)

    def test_모든_언어와_번역_조합에서_만든_프로젝트가_검사를_통과하고_저장소_안내를_채울_여유가_있다(self):
        for language in sorted(new_project.LANGUAGE_SETUPS):
            for translation in (False, True):
                with self.subTest(language=language, translation=translation):
                    parent = self.parent / f"{language}-{translation}"
                    parent.mkdir()
                    request = request_for(parent, language, translation)
                    plan = new_project.create(SOURCE, request, TODAY)
                    self.assertEqual(plan.warnings, [])
                    subprocess.run(["git", "add", "-A"], cwd=request.target, check=True)  # 문서 링크 검사는 추적 파일만 봄
                    result = run_in(request.target, "scripts/repo_checks.py")
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    lines = (request.target / "AGENTS.md").read_text(encoding="utf-8").count("\n")
                    self.assertLessEqual(lines, MAX_GENERATED_AGENTS_LINES)

    def test_공통_규칙의_커밋_type_목록과_검사의_목록이_같다(self):
        request = request_for(self.parent, "python")
        new_project.create(SOURCE, request, TODAY)
        agents = (request.target / "AGENTS.md").read_text(encoding="utf-8")
        line = next(line for line in agents.splitlines() if "type은 `" in line)
        listed = re.findall(r"`([a-z]+)`", line.split("type은", 1)[1].split("이고", 1)[0])
        spec = importlib.util.spec_from_file_location("project_repo_checks", request.target / "scripts/repo_checks.py")
        checks = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(checks)
        self.assertEqual(tuple(listed), checks.COMMIT_TYPES)

    def test_만든_프로젝트의_검사_도구와_훅_테스트가_통과한다(self):
        request = request_for(self.parent, "typescript")
        new_project.create(SOURCE, request, TODAY)
        for pattern in ("test_checks.py", "test_agent_hooks.py"):
            result = run_in(request.target, "-m", "unittest", "discover", "-s", "scripts", "-p", pattern)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_저장소_안내에_이름_설명_명령이_채워지고_공통_규칙이_붙는다(self):
        request = request_for(self.parent, "go")
        new_project.create(SOURCE, request, TODAY)
        agents = (request.target / "AGENTS.md").read_text(encoding="utf-8")
        self.assertTrue(agents.startswith("# demo-app\n\n시험용 앱\n"))
        self.assertIn("go test -race ./...", agents)
        self.assertIn(new_project.sync_rules.BLOCK_START, agents)
        for placeholder in ("<저장소 이름>", new_project.DESCRIPTION_PLACEHOLDER, "<테스트>", "번역 저장소라면"):
            self.assertNotIn(placeholder, agents)
        self.assertEqual(
            subprocess.run(["git", "symbolic-ref", "--short", "HEAD"], cwd=request.target,
                           capture_output=True, text=True).stdout.strip(),
            "main",
        )

    def test_번역_저장소에는_번역_규칙과_스킬을_넣는다(self):
        request = request_for(self.parent, "python", translation=True)
        new_project.create(SOURCE, request, TODAY)
        for rel in ("TRANSLATION.md", ".claude/rules/translation.md", ".agents/skills/translate-chapter/SKILL.md"):
            self.assertTrue((request.target / rel).is_file(), rel)
        self.assertIn("번역 저장소라면", (request.target / "AGENTS.md").read_text(encoding="utf-8"))

    def test_실행_계획_목록은_템플릿을_채워_만든다(self):
        request = request_for(self.parent, "python")
        new_project.create(SOURCE, request, TODAY)
        text = (request.target / "docs/exec-plans/README.md").read_text(encoding="utf-8")
        self.assertIn(f"| [초기 구축](active/0001-initial-setup.md) | 뼈대, 검사, 문서를 갖춘 첫 동작 버전 | {TODAY} |", text)
        self.assertNotIn("<제목>", text)

    def test_템플릿_모양이_바뀌면_멈춘다(self):
        with self.assertRaises(ValueError):
            new_project.fill("# 바뀐 템플릿\n", {"<제목>": "초기 구축"})

    def test_비어_있지_않은_폴더에는_만들지_않는다(self):
        request = request_for(self.parent, "python")
        request.target.mkdir()
        (request.target / "keep.txt").write_text("기존 파일\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            new_project.create(SOURCE, request, TODAY)

    def test_잘못된_이름은_거절한다(self):
        with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
            new_project.parse_request(["--name", "../escape", "--language", "python"])


if __name__ == "__main__":
    unittest.main()

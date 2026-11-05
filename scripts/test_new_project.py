"""new_project.py 테스트. 실제 claude-home 템플릿으로 임시 폴더에 프로젝트를 만들고,
만들어진 프로젝트에서 저장소 검사가 통과하는지 확인합니다. 규칙·템플릿을 고친 뒤 새 프로젝트가 깨지지 않게 하는 안전장치입니다.

실행:  python -I -m unittest discover -s scripts -p "test_*.py"
"""
import contextlib
import importlib.util
import io
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
TRANSLATION = new_project.sync_rules.TRANSLATION


def request_for(parent: Path, language: str, translation: bool = False) -> "new_project.ProjectRequest":
    rule_sets = frozenset({language} | ({TRANSLATION} if translation else set()))
    return new_project.ProjectRequest("demo-app", language, "시험용 앱", rule_sets, parent / "demo-app")


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

    def test_모든_언어와_번역_조합에서_만든_프로젝트가_저장소_검사를_통과한다(self):
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

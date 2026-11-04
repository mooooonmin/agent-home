"""agent_hooks.py 테스트. 저장소 상태와 Stop 훅은 임시 git 저장소를 만들어 확인합니다.

실행:  python3 -I -m unittest discover -s scripts -p "test_agent_hooks.py"
"""
import contextlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location("agent_hooks", HERE / "agent_hooks.py")
hooks = importlib.util.module_from_spec(spec)
sys.modules["agent_hooks"] = hooks  # dataclass가 모듈을 찾을 수 있게 등록
spec.loader.exec_module(hooks)

KNOWN_REMOTE = frozenset({"origin/main", "origin/master", "origin/feat/x"})
ON_MAIN = hooks.RepoState(branch="main", has_commits=True, remote_branches=KNOWN_REMOTE)
ON_FEATURE = hooks.RepoState(branch="feat/x", has_commits=True, remote_branches=KNOWN_REMOTE)


def reason(command: str, state: hooks.RepoState) -> str | None:
    return next((r for call in hooks.git_calls(command) if (r := hooks.blocked_reason(call, state))), None)


class GitCallsTest(unittest.TestCase):
    def test_이어진_명령과_환경_변수와_C_옵션을_읽는다(self):
        calls = hooks.git_calls("cd app && GIT_TRACE=0 git -C sub commit -m '메시지' ; ls | git push origin x")
        self.assertEqual([(c.directory, c.subcommand) for c in calls], [("sub", "commit"), (None, "push")])

    def test_heredoc_본문의_명령은_무시한다(self):
        command = "git commit -F - <<'EOF'\n제목\n\ngit push origin main 은 하지 않음\nEOF"
        self.assertEqual([c.subcommand for c in hooks.git_calls(command)], ["commit"])


class BlockedReasonTest(unittest.TestCase):
    def test_main에서_커밋하면_막는다(self):
        self.assertIsNotNone(reason("git commit -m x", ON_MAIN))

    def test_첫_커밋은_main이라도_허용한다(self):
        self.assertIsNone(reason("git commit -m init", hooks.RepoState(branch="main", has_commits=False)))

    def test_작업_브랜치의_커밋과_푸시는_허용한다(self):
        self.assertIsNone(reason("git commit -m x && git push -u origin feat/x", ON_FEATURE))

    def test_main으로_가는_푸시를_막는다(self):
        for command in (
            "git push origin main", "git push origin HEAD:main", "git push origin +feat/x:refs/heads/master",
            "git push --all origin", "git push --set-upstream origin main",
        ):
            with self.subTest(command=command):
                self.assertIsNotNone(reason(command, ON_FEATURE))

    def test_main에서_대상_없이_푸시하면_막는다(self):
        self.assertIsNotNone(reason("git push", ON_MAIN))
        self.assertIsNotNone(reason("git push origin HEAD", ON_MAIN))

    def test_원격에_아직_없는_기본_브랜치로의_첫_푸시는_허용한다(self):
        new_repo = hooks.RepoState(branch="main", has_commits=True)
        self.assertIsNone(reason("git push -u origin main", new_repo))
        self.assertIsNotNone(reason("git push upstream main", hooks.RepoState("main", True, frozenset({"upstream/main"}))))

    def test_옵션_값은_대상으로_보지_않는다(self):
        self.assertIsNone(reason("git push -o main origin feat/x", ON_FEATURE))


class TempGitRepo:
    def __enter__(self):
        self._dir = tempfile.TemporaryDirectory()
        self.root = Path(self._dir.name)
        self.git("init", "-q", "-b", "main")
        return self

    def __exit__(self, *exc):
        self._dir.cleanup()

    def git(self, *args):
        subprocess.run(["git", "-c", "user.name=test", "-c", "user.email=test@example.com", *args],
                       cwd=self.root, check=True, capture_output=True)

    def commit(self, name="README.md"):
        (self.root / name).write_text("# 시험\n", encoding="utf-8")
        self.git("add", name)
        self.git("commit", "-q", "-m", "init")


def run_main(argv, payload) -> tuple[int, str]:
    stderr = io.StringIO()
    with mock.patch("sys.stdin", io.StringIO(json.dumps(payload))), contextlib.redirect_stderr(stderr):
        return hooks.main(argv), stderr.getvalue()


class RepoHookTest(unittest.TestCase):
    def test_저장소_상태를_읽는다(self):
        with TempGitRepo() as repo:
            self.assertEqual(hooks.read_repo_state(repo.root), hooks.RepoState(branch="main", has_commits=False))
            repo.commit()
            self.assertEqual(hooks.read_repo_state(repo.root), hooks.RepoState(branch="main", has_commits=True))

    def test_pre_bash는_막을_때_종료_코드_2와_이유를_낸다(self):
        with TempGitRepo() as repo:
            repo.commit()
            payload = {"tool_name": "Bash", "tool_input": {"command": "git commit -m x"}, "cwd": str(repo.root)}
            code, message = run_main(["pre-bash"], payload)
            self.assertEqual(code, hooks.EXIT_BLOCK)
            self.assertIn("main", message)

    def test_JSON이_아닌_입력은_막지_않는다(self):
        with mock.patch("sys.stdin", io.StringIO("not json")):
            self.assertEqual(hooks.main(["pre-bash"]), hooks.EXIT_ALLOW)

    def test_stop은_바뀐_파일이_있고_검사가_실패하면_막는다(self):
        with TempGitRepo() as repo:
            repo.commit()
            (repo.root / "check.py").write_text("import sys\nprint('문제 1개')\nsys.exit(1)\n", encoding="utf-8")
            code, message = run_main(["stop", "check.py"], {"cwd": str(repo.root)})
            self.assertEqual(code, hooks.EXIT_BLOCK)
            self.assertIn("문제 1개", message)

    def test_stop은_이미_한_번_막았으면_다시_막지_않는다(self):
        with TempGitRepo() as repo:
            (repo.root / "check.py").write_text("raise SystemExit(1)\n", encoding="utf-8")
            code, _ = run_main(["stop", "check.py"], {"cwd": str(repo.root), "stop_hook_active": True})
            self.assertEqual(code, hooks.EXIT_ALLOW)

    def test_stop은_바뀐_파일이_없거나_검사_도구가_없으면_넘어간다(self):
        with TempGitRepo() as repo:
            (repo.root / "check.py").write_text("raise SystemExit(1)\n", encoding="utf-8")
            repo.git("add", "check.py")
            repo.git("commit", "-q", "-m", "검사 추가")
            self.assertEqual(run_main(["stop", "check.py"], {"cwd": str(repo.root)})[0], hooks.EXIT_ALLOW)
            (repo.root / "new.txt").write_text("바뀜\n", encoding="utf-8")
            self.assertEqual(run_main(["stop", "missing.py"], {"cwd": str(repo.root)})[0], hooks.EXIT_ALLOW)


if __name__ == "__main__":
    unittest.main()

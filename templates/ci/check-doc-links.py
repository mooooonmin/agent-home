#!/usr/bin/env python3
"""마크다운 문서의 내부 링크·이미지·앵커가 실제로 있는지 검사합니다.

- 상대 경로 링크와 이미지(`[t](path)`, `![a](path)`, `<img src="path">`)가 존재하는 파일을 가리키는지
- 앵커 링크(`#heading`, `other.md#heading`)가 대상 문서의 실제 제목을 가리키는지 (GitHub slug 규칙)

외부 URL은 검사하지 않습니다(네트워크 없이 항상 같은 결과). 코드 블록과 인라인 코드 안은 건너뜁니다.
표준 라이브러리만 씁니다.

실행:  python3 -I check-doc-links.py [--exclude 폴더 ...]
깨진 참조가 있으면 종료 코드 1로 끝납니다.
"""
import argparse
import os
import re
import subprocess
import sys
from urllib.parse import unquote

LINK = re.compile(r"!?\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
IMG_TAG = re.compile(r"<img\b[^>]*?\bsrc=[\"']([^\"']+)[\"']", re.IGNORECASE)
HEADING = re.compile(r"^ {0,3}(#{1,6})\s+(.*?)\s*#*\s*$")
HTML_ANCHOR = re.compile(r"<a\s+[^>]*?(?:name|id)=[\"']([^\"']+)[\"']", re.IGNORECASE)
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
INLINE_CODE = re.compile(r"`+[^`]*`+")
EXTERNAL = re.compile(r"^(?:[a-z][a-z0-9+.-]*:|//)", re.IGNORECASE)


def list_markdown(root, excludes):
    try:
        out = subprocess.run(
            ["git", "ls-files", "-z", "--", "*.md"], cwd=root, capture_output=True, check=True
        ).stdout.decode("utf-8")
        files = [f for f in out.split("\0") if f]
    except (OSError, subprocess.CalledProcessError):
        files = []
        for d, dirs, names in os.walk(root):
            dirs[:] = [x for x in dirs if not x.startswith(".") or x == ".claude"]
            files += [os.path.relpath(os.path.join(d, n), root) for n in names if n.endswith(".md")]
    norm = [f.replace("\\", "/") for f in files]
    return [f for f in norm if not any(f == e or f.startswith(e.rstrip("/") + "/") for e in excludes)]


def lines_outside_code(text):
    fence = None
    for no, line in enumerate(text.splitlines(), 1):
        m = FENCE.match(line)
        if m:
            mark = m.group(1)
            if fence is None:
                fence = mark[0]
            elif mark[0] == fence:
                fence = None
            continue
        if fence is None:
            yield no, line


def slugify(title):
    title = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", title)  # [text](url) -> text
    title = re.sub(r"<[^>]+>", "", title)  # HTML 태그
    title = title.replace("`", "").replace("*", "")
    title = title.strip().lower()
    title = re.sub(r"[^\w\- ]", "", title)
    return title.replace(" ", "-")


_anchor_cache = {}


def anchors_of(path):
    if path not in _anchor_cache:
        seen, result = {}, set()
        with open(path, encoding="utf-8") as f:
            text = f.read()
        for _, line in lines_outside_code(text):
            m = HEADING.match(line)
            if m:
                base = slugify(m.group(2))
                n = seen.get(base, 0)
                seen[base] = n + 1
                result.add(base if n == 0 else f"{base}-{n}")
            result.update(a.lower() for a in HTML_ANCHOR.findall(line))
        _anchor_cache[path] = result
    return _anchor_cache[path]


def check(root, rel):
    errors = []
    path = os.path.join(root, rel)
    with open(path, encoding="utf-8") as f:
        text = f.read()
    for no, line in lines_outside_code(text):
        line = INLINE_CODE.sub("", line)
        for target in LINK.findall(line) + IMG_TAG.findall(line):
            if EXTERNAL.match(target):
                continue
            target_path, _, anchor = target.partition("#")
            target_path = unquote(target_path)
            if target_path:
                base = root if target_path.startswith("/") else os.path.dirname(path)
                dest = os.path.normpath(os.path.join(base, target_path.lstrip("/")))
                if not os.path.exists(dest):
                    errors.append(f"{rel}:{no}: 없는 파일 -> {target}")
                    continue
            else:
                dest = path
            if anchor and dest.endswith(".md") and os.path.isfile(dest):
                if unquote(anchor).lower() not in anchors_of(dest):
                    errors.append(f"{rel}:{no}: 없는 제목 앵커 -> {target}")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=".", help="저장소 루트 (기본: 현재 폴더)")
    parser.add_argument("--exclude", nargs="*", default=[], help="검사하지 않을 폴더")
    args = parser.parse_args()
    root = os.path.abspath(args.root)
    sys.stdout.reconfigure(encoding="utf-8")  # Windows 콘솔에서 한글이 깨지지 않게

    files = list_markdown(root, args.exclude)
    errors = [e for rel in files for e in check(root, rel)]
    for e in errors:
        print(e)
    print(f"문서 {len(files)}개 검사, 깨진 참조 {len(errors)}개")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

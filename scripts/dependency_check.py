#!/usr/bin/env python3
"""
PostToolUse 훅: .py 파일 저장 후 requirements.txt 동기화 검사

새로운 import 문이 추가됐는데 requirements.txt에 없으면 경고합니다.
"ModuleNotFoundError: No module named 'xxx'" 를 미리 방지합니다.
"""

import ast
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path("C:/Users/정화민/Desktop/IR센터 MCP")
REQUIREMENTS = PROJECT_ROOT / "requirements.txt"

# 표준 라이브러리 + 무시할 패키지 (설치 불필요)
STDLIB_AND_IGNORE = {
    "os", "sys", "re", "json", "io", "pathlib", "datetime", "math",
    "collections", "itertools", "functools", "typing", "copy", "shutil",
    "subprocess", "contextlib", "importlib", "traceback", "abc", "dataclasses",
    "ast", "inspect", "warnings", "logging", "time", "random", "string",
    "hashlib", "base64", "urllib", "http", "email", "html", "xml",
    "report_app",  # 내부 패키지
    "__future__",
}

# pip 패키지명과 import 이름이 다른 경우 매핑
IMPORT_TO_PACKAGE = {
    "PIL":        "Pillow",
    "cv2":        "opencv-python",
    "sklearn":    "scikit-learn",
    "dotenv":     "python-dotenv",
    "docx":       "python-docx",
    "yaml":       "PyYAML",
    "bs4":        "beautifulsoup4",
}

def get_imports_from_file(file_path: Path) -> set[str]:
    """파일에서 최상위 import 이름 목록을 추출한다."""
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
    except SyntaxError:
        return set()

    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split(".")[0])
    return imports


def get_requirements() -> set[str]:
    """requirements.txt에서 패키지명(소문자) 목록을 반환한다."""
    if not REQUIREMENTS.exists():
        return set()
    pkgs = set()
    for line in REQUIREMENTS.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            # 버전 지정자 제거: pandas>=2.0.0 → pandas
            name = line.split(">=")[0].split("<=")[0].split("==")[0].split("!=")[0].strip()
            pkgs.add(name.lower())
    return pkgs


try:
    raw = sys.stdin.buffer.read().decode("utf-8", errors="replace")
    data = json.loads(raw)
    tool_input = data.get("tool_input", {})
    file_path  = tool_input.get("file_path", "")

    if not file_path or not file_path.endswith(".py"):
        sys.exit(0)

    src = Path(file_path)
    if not src.exists():
        sys.exit(0)

    imports   = get_imports_from_file(src)
    installed = get_requirements()
    missing   = []

    for imp in imports:
        if imp in STDLIB_AND_IGNORE:
            continue
        # import 이름 → pip 패키지명 변환
        pkg_name = IMPORT_TO_PACKAGE.get(imp, imp).lower()
        if pkg_name not in installed:
            missing.append((imp, IMPORT_TO_PACKAGE.get(imp, imp)))

    if missing:
        print(f"\n{'='*55}", file=sys.stderr)
        print(f"[의존성 경고 ⚠] {src.name}", file=sys.stderr)
        print(f"  아래 패키지가 requirements.txt에 없습니다:", file=sys.stderr)
        for imp, pkg in missing:
            print(f"    import {imp}  →  pip install {pkg}", file=sys.stderr)
        print(f"  → requirements.txt에 추가하거나", file=sys.stderr)
        print(f"    scripts/auto_pip_install.py 가 자동 처리합니다.", file=sys.stderr)
        print(f"{'='*55}\n", file=sys.stderr)
    else:
        print(f"[의존성 검사 ✓] {src.name} — requirements.txt 동기화 정상", file=sys.stderr)

except Exception as e:
    print(f"[의존성 검사 오류] {e}", file=sys.stderr)

sys.exit(0)

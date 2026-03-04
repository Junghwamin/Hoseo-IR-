"""
Windows 설치 프로그램 빌드 스크립트

Embedded Python 3.11을 다운로드하고, 의존성을 설치한 뒤,
앱 파일을 복사하여 Inno Setup용 빌드 디렉토리를 구성한다.

사용법:
    python installer/windows/build_windows.py

결과:
    build/windows/ 디렉토리에 설치 프로그램 소스가 생성된다.
    이후 Inno Setup으로 setup.iss를 컴파일하면 .exe 인스톨러가 만들어진다.
"""

import os
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

# ---------------------------------------------------------------------------
# 설정 상수
# ---------------------------------------------------------------------------
PYTHON_VERSION = "3.11.9"
PYTHON_ZIP_URL = (
    f"https://www.python.org/ftp/python/{PYTHON_VERSION}/"
    f"python-{PYTHON_VERSION}-embed-amd64.zip"
)
GET_PIP_URL = "https://bootstrap.pypa.io/get-pip.py"

# 프로젝트 루트 (이 스크립트 기준 2단계 상위)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BUILD_DIR = PROJECT_ROOT / "build" / "windows"
PYTHON_DIR = BUILD_DIR / "python-embed"
APP_DIR = BUILD_DIR / "app"
DIST_DIR = PROJECT_ROOT / "dist" / "windows"


# ---------------------------------------------------------------------------
# 1. Embedded Python 다운로드 및 설정
# ---------------------------------------------------------------------------
def download_python():
    """python.org에서 Embedded Python zip을 다운로드하고 압축 해제한다."""
    zip_path = BUILD_DIR / f"python-{PYTHON_VERSION}-embed-amd64.zip"

    if PYTHON_DIR.exists():
        print(f"  [건너뜀] {PYTHON_DIR} 이미 존재")
        return

    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    print(f"  다운로드: {PYTHON_ZIP_URL}")
    urllib.request.urlretrieve(PYTHON_ZIP_URL, str(zip_path))

    print(f"  압축 해제: {PYTHON_DIR}")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(PYTHON_DIR)

    zip_path.unlink()
    print("  Embedded Python 다운로드 완료")


def enable_site_packages():
    """python311._pth를 수정하여 site-packages와 앱 루트 경로를 활성화한다.

    Embedded Python은 ._pth 파일로 sys.path를 제어한다.
    '..' 경로를 추가해야 python-embed/의 부모(=HoseoIRPortal/)에서
    report_app 패키지를 import할 수 있다.
    """
    pth_files = list(PYTHON_DIR.glob("python*._pth"))
    if not pth_files:
        raise FileNotFoundError("python*._pth 파일을 찾을 수 없습니다.")

    pth_file = pth_files[0]
    content = pth_file.read_text(encoding="utf-8")

    # import site 활성화
    if "#import site" in content:
        content = content.replace("#import site", "import site")
        print(f"  {pth_file.name}: import site 활성화 완료")

    # '..' 경로 추가 → python-embed의 부모(HoseoIRPortal/) = 앱 루트
    if ".." not in content.splitlines():
        content = content.rstrip("\n") + "\n..\n"
        print(f"  {pth_file.name}: '..' 경로 추가 (앱 루트 접근용)")

    pth_file.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# 2. pip 설치
# ---------------------------------------------------------------------------
def install_pip():
    """get-pip.py를 다운로드하여 Embedded Python에 pip를 설치한다."""
    python_exe = PYTHON_DIR / "python.exe"
    scripts_dir = PYTHON_DIR / "Scripts"

    if (scripts_dir / "pip.exe").exists():
        print("  [건너뜀] pip 이미 설치됨")
        return

    get_pip_path = BUILD_DIR / "get-pip.py"
    print(f"  다운로드: {GET_PIP_URL}")
    urllib.request.urlretrieve(GET_PIP_URL, str(get_pip_path))

    print("  pip 설치 중...")
    subprocess.run(
        [str(python_exe), str(get_pip_path), "--no-warn-script-location"],
        check=True,
        cwd=str(PYTHON_DIR),
    )

    get_pip_path.unlink()
    print("  pip 설치 완료")


# ---------------------------------------------------------------------------
# 3. 의존성 설치
# ---------------------------------------------------------------------------
def install_dependencies():
    """requirements.txt의 패키지를 Embedded Python에 설치한다."""
    python_exe = PYTHON_DIR / "python.exe"
    req_file = PROJECT_ROOT / "requirements.txt"

    print("  의존성 설치 중... (수 분 소요)")
    subprocess.run(
        [
            str(python_exe), "-m", "pip", "install",
            "-r", str(req_file),
            "--no-warn-script-location",
        ],
        check=True,
        cwd=str(PYTHON_DIR),
    )
    print("  의존성 설치 완료")


# ---------------------------------------------------------------------------
# 4. 앱 파일 복사
# ---------------------------------------------------------------------------
def copy_app_files():
    """프로젝트 앱 파일을 빌드 디렉토리에 복사한다."""
    if APP_DIR.exists():
        shutil.rmtree(APP_DIR)

    APP_DIR.mkdir(parents=True, exist_ok=True)

    # report_app/ 패키지
    shutil.copytree(
        PROJECT_ROOT / "report_app",
        APP_DIR / "report_app",
        ignore=shutil.ignore_patterns("__pycache__"),
    )

    # config/ 디렉토리
    shutil.copytree(
        PROJECT_ROOT / "config",
        APP_DIR / "config",
    )

    # .streamlit/ 설정
    shutil.copytree(
        PROJECT_ROOT / ".streamlit",
        APP_DIR / ".streamlit",
    )

    # 전처리 스크립트
    shutil.copy2(
        PROJECT_ROOT / "전임교원_연구실적_전처리.py",
        APP_DIR / "전임교원_연구실적_전처리.py",
    )

    # requirements.txt
    shutil.copy2(
        PROJECT_ROOT / "requirements.txt",
        APP_DIR / "requirements.txt",
    )

    # output 디렉토리 + 기존 CSV 데이터 복사
    (APP_DIR / "output" / "reports").mkdir(parents=True, exist_ok=True)
    for csv_name in ["전체_대학_데이터.csv", "충청권_순위.csv"]:
        src = PROJECT_ROOT / "output" / csv_name
        if src.exists():
            shutil.copy2(src, APP_DIR / "output" / csv_name)
            print(f"  데이터 포함: output/{csv_name}")

    # Raw data 디렉토리 생성 (빈 폴더)
    (APP_DIR / "Raw data").mkdir(parents=True, exist_ok=True)

    # .env 템플릿 생성 (빈 API Key)
    env_template = APP_DIR / ".env"
    if not env_template.exists():
        env_template.write_text(
            "# OpenAI API Key (앱 사이드바에서도 설정 가능)\n"
            "OPENAI_API_KEY=\n",
            encoding="utf-8",
        )
        print("  .env 템플릿 생성 완료")

    # 런처 복사
    launcher_src = Path(__file__).parent / "launcher.pyw"
    if launcher_src.exists():
        shutil.copy2(launcher_src, APP_DIR / "launcher.pyw")

    # 아이콘 복사
    icon_src = Path(__file__).parent / "icon.ico"
    if icon_src.exists():
        shutil.copy2(icon_src, APP_DIR / "icon.ico")

    print("  앱 파일 복사 완료")


# ---------------------------------------------------------------------------
# 5. 최종 빌드 디렉토리 조립
# ---------------------------------------------------------------------------
def assemble_build():
    """Embedded Python과 앱 파일을 하나의 설치 디렉토리로 조립한다."""
    final_dir = BUILD_DIR / "HoseoIRPortal"

    if final_dir.exists():
        shutil.rmtree(final_dir)

    final_dir.mkdir(parents=True, exist_ok=True)

    # Embedded Python 복사
    shutil.copytree(PYTHON_DIR, final_dir / "python-embed", dirs_exist_ok=True)

    # 앱 파일 복사 (최상위에 배치)
    for item in APP_DIR.iterdir():
        dest = final_dir / item.name
        if item.is_dir():
            shutil.copytree(item, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(item, dest)

    # dist 디렉토리 생성
    DIST_DIR.mkdir(parents=True, exist_ok=True)

    print(f"  최종 빌드 디렉토리: {final_dir}")
    print("  조립 완료")


# ---------------------------------------------------------------------------
# 메인
# ---------------------------------------------------------------------------
def main():
    print("=" * 60)
    print("  IR센터 연구실적 분석 포털 - Windows 빌드")
    print("=" * 60)

    print("\n[1/5] Embedded Python 다운로드...")
    download_python()

    print("\n[2/5] site-packages 활성화...")
    enable_site_packages()

    print("\n[3/5] pip 설치...")
    install_pip()

    print("\n[4/5] 의존성 설치...")
    install_dependencies()

    print("\n[5/5] 앱 파일 복사 및 조립...")
    copy_app_files()
    assemble_build()

    print("\n" + "=" * 60)
    print("  빌드 완료!")
    print(f"  빌드 디렉토리: {BUILD_DIR / 'HoseoIRPortal'}")
    print("  다음 단계: Inno Setup으로 setup.iss를 컴파일하세요.")
    print("=" * 60)


if __name__ == "__main__":
    main()

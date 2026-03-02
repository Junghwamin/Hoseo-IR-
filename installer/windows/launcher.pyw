"""
호서대학교 IR센터 연구실적 분석 포털 - Windows 런처

바탕화면 아이콘에서 실행되는 진입점.
콘솔 창 없이 Streamlit 서버를 시작하고 기본 브라우저를 연다.

.pyw 확장자로 pythonw.exe가 실행하므로 콘솔 창이 표시되지 않는다.
"""

import os
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path


def find_free_port(start=8501, end=8510):
    """사용 가능한 포트를 찾는다. 8501부터 시도."""
    for port in range(start, end + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return start  # 모두 실패 시 기본값 반환


def wait_for_server(port, timeout=60):
    """Streamlit 서버가 응답할 때까지 대기한다."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return True
        except (ConnectionRefusedError, OSError):
            time.sleep(0.5)
    return False


def main():
    # 앱 디렉토리 = 런처가 위치한 디렉토리
    app_dir = Path(__file__).resolve().parent
    python_exe = app_dir / "python-embed" / "python.exe"
    app_py = app_dir / "report_app" / "app.py"

    # Python 실행파일 존재 확인
    if not python_exe.exists():
        import ctypes
        ctypes.windll.user32.MessageBoxW(
            0,
            f"Python을 찾을 수 없습니다.\n경로: {python_exe}",
            "IR센터 포털 - 오류",
            0x10,
        )
        return

    # 사용 가능한 포트 찾기
    port = find_free_port()

    # 환경 변수 설정
    env = os.environ.copy()
    env["PYTHONPATH"] = str(app_dir)
    env["PYTHONUTF8"] = "1"  # 한글 경로 대응
    env["STREAMLIT_SERVER_HEADLESS"] = "true"
    env["STREAMLIT_SERVER_PORT"] = str(port)
    env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"

    # Streamlit 서버 시작 (콘솔 창 숨김)
    CREATE_NO_WINDOW = 0x08000000
    proc = subprocess.Popen(
        [
            str(python_exe), "-m", "streamlit", "run",
            str(app_py),
            "--server.headless", "true",
            "--server.port", str(port),
        ],
        cwd=str(app_dir),
        env=env,
        creationflags=CREATE_NO_WINDOW,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # 서버 준비 대기 후 브라우저 열기
    if wait_for_server(port):
        webbrowser.open(f"http://localhost:{port}")
    else:
        import ctypes
        ctypes.windll.user32.MessageBoxW(
            0,
            "앱 서버 시작에 실패했습니다.\n잠시 후 다시 시도해 주세요.",
            "IR센터 포털 - 오류",
            0x10,
        )
        proc.terminate()
        return

    # 서버 프로세스가 종료될 때까지 대기
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()


if __name__ == "__main__":
    main()

@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo  ========================================
echo    호서대학교 정화민 - 연구실적 분석 포털
echo  ========================================
echo.
echo  앱을 시작합니다... 잠시 기다려주세요.
echo  브라우저가 자동으로 열립니다.
echo.
echo  종료하려면 이 창을 닫으세요.
echo  ========================================
echo.

where streamlit >nul 2>&1
if %errorlevel% equ 0 (
    streamlit run report_app/app.py
) else (
    echo  [오류] streamlit이 설치되어 있지 않습니다.
    echo  다음 명령으로 설치해 주세요:
    echo     pip install -r requirements.txt
)
pause

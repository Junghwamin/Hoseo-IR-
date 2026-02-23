@echo off
chcp 65001 >nul
cd /d "C:\Users\정화민\Desktop\IR센터 MCP"
set PYTHONPATH=C:\Users\정화민\Desktop\IR센터 MCP;%PYTHONPATH%
echo.
echo  ========================================
echo    호서대학교 IR센터 연구실적 분석 포털
echo  ========================================
echo.
echo  앱을 시작합니다... 잠시 기다려주세요.
echo  브라우저가 자동으로 열립니다.
echo.
echo  종료하려면 이 창을 닫으세요.
echo  ========================================
echo.
"C:\Users\정화민\AppData\Local\Programs\Python\Python311\Scripts\streamlit.exe" run report_app/app.py
pause

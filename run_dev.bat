@echo off
echo ===============================
echo Starting Academic Insights (DEV)
echo ===============================

echo.
echo [1] Starting Backend...
start "BACKEND" cmd /k "cd /d C:\Users\Lenovo\Desktop\RoboAIAPaths\academics_insights\backend && bac_env\Scripts\activate && uvicorn app:app --reload"

echo.
echo [2] Starting Frontend...
start "FRONTEND" cmd /k "cd /d C:\Users\Lenovo\Desktop\RoboAIAPaths\academics_insights\frontend && fro_env\Scripts\activate && streamlit run streamlit_app.py"

echo.
echo Backend and Frontend launched in separate windows.
pause

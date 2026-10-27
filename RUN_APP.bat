@echo off
title AI Academic Decision System - IFHE
cd /d "c:\Users\edulakanti karthik\OneDrive\Desktop\24STUCHH010302\sp profest"

echo ================================================
echo   AI Academic Decision System - IFHE Portal
echo ================================================
echo.
echo  Starting server... please wait...
echo  App will open at: http://localhost:8501
echo.
echo  KEEP THIS WINDOW OPEN while using the app.
echo  Press CTRL+C to stop the server.
echo ================================================
echo.

"c:\Users\edulakanti karthik\OneDrive\Desktop\24STUCHH010302\sp profest\.venv\Scripts\python.exe" -m streamlit run "c:\Users\edulakanti karthik\OneDrive\Desktop\24STUCHH010302\sp profest\app.py" --server.port=8501 --server.headless=false

echo.
echo Server stopped.
pause

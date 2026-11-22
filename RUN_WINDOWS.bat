@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    py -3.12 -m venv .venv
    if errorlevel 1 goto failed
)
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements.txt
if errorlevel 1 goto failed
".venv\Scripts\python.exe" manage.py migrate --noinput
if errorlevel 1 goto failed
echo Open http://127.0.0.1:8000/ in your browser. Press Ctrl+C to stop.
".venv\Scripts\python.exe" manage.py runserver 127.0.0.1:8000 --noreload
if errorlevel 1 goto failed
exit /b 0
:failed
echo Setup or startup failed. Check the message above. Python 3.12 with the Windows py launcher is required.
pause
exit /b 1

@echo off
uv venv
call .venv\Scripts\activate
uv pip install -r requirements.txt
python manage.py migrate
python manage.py import_assets
echo.
echo Done. Run: run_server.bat
pause

@echo off
echo Installing AEROX Backend Dependencies...
echo This may take 5-10 minutes...
echo.

pip install --upgrade pip
pip install -r requirements.txt

echo.
echo ========================================
echo Installation complete!
echo ========================================
echo.
echo To start the backend, run:
echo python -m uvicorn api.main:app --reload --port 8000
echo.
pause

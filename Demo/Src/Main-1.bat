@echo off

REM Check if the Python file exists
if exist "web_scraper.py" (
    echo Found web_scraper.py, running the script...
    python web_scraper.py
) else (
    echo ERROR: web_scraper.py not found in the current directory!
    echo Please make sure the file exists in the same folder as this batch file.
)

pause
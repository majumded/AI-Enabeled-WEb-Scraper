@echo off

REM Check if the Python file exists
if exist "gui_date_extraction.py" (
    echo Found gui_date_extraction.py, running the script...
    python gui_date_extraction.py
) else (
    echo ERROR: gui_date_extraction.py not found in the current directory!
    echo Please make sure the file exists in the same folder as this batch file.
)

pause
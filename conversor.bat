@echo off
cd /d "%~dp0converter"
call ".venv311\Scripts\activate.bat"
python script.py
pause

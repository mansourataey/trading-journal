@echo off
title Trading Journal

cd /d "%~dp0"

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate

echo Installing dependencies...
pip install -r requirements.txt

echo Starting Trading Journal...
uvicorn app.main:app --reload

pause
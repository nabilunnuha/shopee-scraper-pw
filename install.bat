@echo off

REM Membuat virtual environment (venv)
py -m venv venv

REM Mengaktifkan virtual environment (venv)
call venv\Scripts\activate

REM Menginstal paket-paket yang dibutuhkan
pip install playwright rich pydantic requests pymongo

REM Menginstal Playwright dan browser yang diperlukan
playwright install

python.exe -m pip install --upgrade pip
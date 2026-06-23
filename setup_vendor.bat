@echo off
title Setup Tesseract portable - Anonymiseur AT
setlocal

if exist "vendor\tesseract\tesseract.exe" (
    echo [OK] Tesseract deja present dans vendor\tesseract\
    pause
    exit /b 0
)

set TESS_LOCAL="%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"
set TESS_PF1="C:\Program Files\Tesseract-OCR\tesseract.exe"
set TESS_PF2="C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"

set TESS_SRC=
if exist %TESS_LOCAL% set TESS_SRC=%LOCALAPPDATA%\Programs\Tesseract-OCR
if exist %TESS_PF1% set TESS_SRC=C:\Program Files\Tesseract-OCR
if exist %TESS_PF2% set TESS_SRC=C:\Program Files (x86)\Tesseract-OCR

if "%TESS_SRC%"=="" (
    echo [ERREUR] Tesseract introuvable sur ce poste.
    echo Installez-le : winget install UB-Mannheim.TesseractOCR
    echo Ou telechargez : https://github.com/UB-Mannheim/tesseract/wiki
    pause
    exit /b 1
)

echo [INFO] Source : %TESS_SRC%
echo [INFO] Copie vers vendor\tesseract\ ...
mkdir vendor\tesseract 2>nul
xcopy /E /I /Y /Q "%TESS_SRC%\*.exe" vendor\tesseract\ >nul
xcopy /E /I /Y /Q "%TESS_SRC%\*.dll" vendor\tesseract\ >nul
xcopy /E /I /Y /Q "%TESS_SRC%\tessdata" vendor\tesseract\tessdata\ >nul

if exist vendor\tesseract\tesseract.exe (
    echo [OK] Tesseract copie dans vendor\tesseract\
    vendor\tesseract\tesseract.exe --version 2>&1 | findstr tesseract
) else (
    echo [ERREUR] Copie echouee.
    exit /b 1
)
pause

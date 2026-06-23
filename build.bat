@echo off
title Build - Anonymiseur.exe
setlocal

echo ==============================================
echo   Build de l'executable Anonymiseur.exe
echo ==============================================
echo.

python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] PyInstaller non trouve. Lancez install.bat d'abord.
    pause
    exit /b 1
)

if not exist "vendor\tesseract\tesseract.exe" (
    echo [INFO] Tesseract portable absent de vendor\tesseract\
    echo        L'exe fonctionnera mais l'OCR ne sera pas autonome.
    echo        Telechargez Tesseract portable :
    echo        https://github.com/UB-Mannheim/tesseract/wiki
    echo        et copiez le dossier dans vendor\tesseract\
    echo.
)

echo [1/3] Nettoyage...
if exist build  rmdir /s /q build
if exist dist   rmdir /s /q dist

echo [2/3] Compilation (2-5 minutes)...
python -m PyInstaller anonymizer.spec --clean --noconfirm
if errorlevel 1 (
    echo [ERREUR] Compilation echouee.
    pause
    exit /b 1
)

if exist "dist\Anonymiseur.exe" (
    echo.
    echo [3/3] Succes !
    echo ==============================================
    echo   Executable : dist\Anonymiseur.exe
    echo ==============================================
) else (
    echo [ERREUR] L'executable n'a pas ete cree.
)

pause

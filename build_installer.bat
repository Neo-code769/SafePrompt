@echo off
title Build Installer - Anonymiseur AT
setlocal

set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist %ISCC% set ISCC="C:\Program Files\Inno Setup 6\ISCC.exe"
if not exist %ISCC% set ISCC="%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"

if not exist %ISCC% (
    echo [ERREUR] Inno Setup 6 non trouve.
    echo Telechargez : https://jrsoftware.org/isdl.php
    echo Ou : winget install JRSoftware.InnoSetup
    pause
    exit /b 1
)

if not exist "dist\Anonymiseur.exe" (
    echo [ERREUR] dist\Anonymiseur.exe absent. Lancez build.bat d'abord.
    pause
    exit /b 1
)

echo Compilation de l'installeur...
%ISCC% installer\anonymiseur.iss
if errorlevel 1 (
    echo [ERREUR] Compilation Inno Setup echouee.
    pause
    exit /b 1
)

echo.
echo Calcul du hash SHA-256...
python -c "import hashlib,glob,pathlib; files=glob.glob('installer/Output/Anonymiseur-Setup-*.exe'); [open('installer/Output/SHA256SUMS.txt','w').write(hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest()+'  '+pathlib.Path(f).name+'\n') or print('SHA256: '+hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest()+'  '+pathlib.Path(f).name) for f in files]"

echo.
echo ==============================================
echo   Installeur cree : installer\Output\
echo   Hash SHA-256    : installer\Output\SHA256SUMS.txt
echo ==============================================
pause

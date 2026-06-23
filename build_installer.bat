@echo off
title Build Installer - Anonymiseur AT
setlocal

set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

if not exist %ISCC% (
    echo [ERREUR] Inno Setup 6 non trouve.
    echo Telechargez : https://jrsoftware.org/isdl.php
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
echo ==============================================
echo   Installeur cree : installer\Output\
echo ==============================================
pause

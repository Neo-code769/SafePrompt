@echo off
title Installation des dependances - Anonymiseur AT
setlocal

echo ==============================================
echo   Installation des dependances Python
echo ==============================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python introuvable. Installez Python 3.10+ et relancez.
    pause
    exit /b 1
)

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 ( echo [ERREUR] pip install a echoue & pause & exit /b 1 )

echo.
echo [spaCy] Telechargement du modele francais...
python -m spacy download fr_core_news_md
if errorlevel 1 ( echo [AVERTISSEMENT] Modele spaCy non installe - NER desactive )

echo.
echo [Tests] Execution de la suite pytest...
python -m pytest -q
if errorlevel 1 (
    echo [AVERTISSEMENT] Certains tests ont echoue.
)

echo.
echo ==============================================
echo   Installation terminee
echo.
echo   Lancer (dev)       : python app.py
echo   Construire l'exe   : build.bat
echo   Builder l'installeur : build_installer.bat (Inno Setup requis)
echo ==============================================
pause

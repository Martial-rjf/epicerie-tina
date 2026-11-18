@echo off
title Mise à jour - Application Boulangerie
color 0A

echo ============================================================
echo        MISE A JOUR DE L'APPLICATION BOULANGERIE
echo ============================================================
echo.

:: Vérifier si le dossier "update" existe
if not exist "update" (
    echo ❌ Dossier "update" introuvable !
    echo.
    echo Créez un dossier "update" dans ce meme dossier
    echo et placez-y le nouveau fichier "run.exe"
    echo.
    pause
    exit /b
)

:: Vérifier si le nouveau fichier existe
if not exist "update\run.exe" (
    echo ❌ Fichier "update\run.exe" introuvable !
    echo.
    echo Placez le nouveau fichier "run.exe" dans le dossier "update"
    echo.
    pause
    exit /b
)

:: Sauvegarde automatique de la base de données
echo 📁 Sauvegarde de la base de donnees...
if exist "db.sqlite3" (
    copy "db.sqlite3" "db_backup_%date:~6,4%%date:~3,2%%date:~0,2%.sqlite3"
    echo ✅ Sauvegarde effectuee : db_backup_%date:~6,4%%date:~3,2%%date:~0,2%.sqlite3
) else (
    echo ⚠️ Aucune base de donnees trouvee
)
echo.

:: Arrêter l'application si elle tourne
echo 🔄 Arret de l'application en cours...
taskkill /f /im run.exe 2>nul
echo ✅ Application arretee
echo.

:: Remplacer l'ancien fichier
echo 📦 Remplacement de l'application...
copy /y "update\run.exe" "run.exe.new"
if errorlevel 1 (
    echo ❌ Erreur lors de la copie !
    pause
    exit /b
)

:: Supprimer l'ancien et renommer le nouveau
del /f "run.exe" 2>nul
move "run.exe.new" "run.exe"
echo ✅ Application remplacee avec succes
echo.

:: Nettoyer le dossier update
rd /s /q "update" 2>nul
echo 🧹 Dossier "update" nettoie
echo.

:: Afficher la version
if exist "version.txt" (
    echo.
    echo 📋 Version actuelle :
    type "version.txt"
    echo.
)

echo ============================================================
echo ✅ Mise a jour terminee avec succes !
echo ============================================================
echo.
echo 🔄 L'application va redemarrer automatiquement...
echo.
timeout /t 3 /nobreak >nul

:: Lancer la nouvelle version
start run.exe

echo.
echo 🎯 L'application est lancee !
echo 📌 Allez sur http://127.0.0.1:8000
echo.
pause
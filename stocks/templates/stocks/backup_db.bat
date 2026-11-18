@echo off
title Sauvegarde - Application Boulangerie
color 0E

echo        SAUVEGARDEecho ============================================================
 DE LA BASE DE DONNEES
echo ============================================================
echo.

if not exist "db.sqlite3" (
    echo ❌ Aucune base de donnees trouvee !
    pause
    exit /b
)

set DATE_SAUV=%date:~6,4%%date:~3,2%%date:~0,2%
copy "db.sqlite3" "db_backup_%DATE_SAUV%.sqlite3"

if errorlevel 1 (
    echo ❌ Erreur lors de la sauvegarde !
) else (
    echo ✅ Sauvegarde reussie : db_backup_%DATE_SAUV%.sqlite3
)

echo.
echo 📁 Emplacement des sauvegardes : %cd%
echo.
pause
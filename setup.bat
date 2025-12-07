@echo off
echo 🚀 Installation du système de surveillance proactive pour Windows...

REM Créer la structure de dossiers
if not exist "data\logs" mkdir "data\logs"
if not exist "data\graphs" mkdir "data\graphs"
if not exist "src" mkdir "src"

REM Vérifier si Python est installé
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python n'est pas installé. Veuillez installer Python 3.8+.
    pause
    exit /b 1
)

REM Installer les dépendances
echo 📦 Installation des dépendances...
pip install -r requirements.txt

echo.
echo ✅ Installation terminée!
echo.
echo 📊 Pour démarrer la surveillance:
echo    python main.py
echo.
echo 📋 Pour voir les logs:
echo    type data\logs\monitoring.log
echo.
pause
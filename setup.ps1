# setup.ps1
Write-Host "🚀 Installation du système de surveillance proactive pour Windows..." -ForegroundColor Green

# Créer la structure de dossiers
$directories = @("data", "data\logs", "data\graphs", "src")
foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir
        Write-Host "✓ Créé : $dir" -ForegroundColor Yellow
    }
}

# Vérifier Python
try {
    python --version 2>&1 | Out-Null
    Write-Host "✓ Python détecté" -ForegroundColor Green
} catch {
    Write-Host "❌ Python n'est pas installé. Veuillez installer Python 3.8+" -ForegroundColor Red
    Read-Host "Appuyez sur Entrée pour quitter"
    exit 1
}

# Installer les dépendances
Write-Host "📦 Installation des dépendances..." -ForegroundColor Cyan
pip install psutil matplotlib pandas numpy seaborn plotly flask PyYAML schedule

# Créer fichiers de base
$configYaml = @"
services:
  - nginx
  - mysql
  - ssh
  - cron

thresholds:
  cpu_warning: 80
  cpu_critical: 90
  memory_warning: 75
  memory_critical: 90
  disk_warning: 80
  disk_critical: 95

monitoring_interval: 60
log_level: INFO

database:
  path: "data/monitoring.db"
  log_path: "data/logs/monitoring.log"

auto_actions:
  enabled: true
  restart_service: true
  clear_temp_files: true
  notify: false
"@

Set-Content -Path "config.yaml" -Value $configYaml

# Créer __init__.py vide
New-Item -ItemType File -Path "src\__init__.py" -Force

Write-Host "`n✅ Installation terminée!" -ForegroundColor Green
Write-Host "`n📊 Pour démarrer la surveillance:" -ForegroundColor Cyan
Write-Host "   python main.py" -ForegroundColor Yellow
Write-Host "`n🌐 Pour le tableau de bord web:" -ForegroundColor Cyan
Write-Host "   python dashboard\app.py" -ForegroundColor Yellow
Write-Host "   puis ouvrir http://localhost:5000" -ForegroundColor Yellow
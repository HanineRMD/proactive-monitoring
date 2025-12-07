#!/bin/bash

echo "🚀 Installation du système de surveillance proactive..."

# Créer la structure de dossiers
mkdir -p data/logs data/graphs src dashboard/{templates,static}

# Installer les dépendances
pip install -r requirements.txt

# Donner les permissions d'exécution
chmod +x main.py

# Initialiser la base de données
python3 -c "
from src.db_manager import DatabaseManager
db = DatabaseManager()
print('✅ Base de données initialisée')
"

# Créer un service systemd
sudo tee /etc/systemd/system/proactive-monitor.service << EOF
[Unit]
Description=Système de Surveillance Proactive
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/venv/bin/python $(pwd)/main.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Démarrer le service
sudo systemctl daemon-reload
sudo systemctl enable proactive-monitor
sudo systemctl start proactive-monitor

echo "✅ Installation terminée!"
echo "📊 Tableau de bord: http://localhost:5000"
echo "📋 Logs: sudo journalctl -u proactive-monitor -f"
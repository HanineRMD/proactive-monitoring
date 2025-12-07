#!/usr/bin/env python3
"""
Script principal de surveillance et auto-réparation
"""

import sys
import os
import time
import schedule
from datetime import datetime

# Ajouter le répertoire src au chemin Python
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.monitor import SystemMonitor
from src.db_manager import DatabaseManager
from src.auto_healer import AutoHealer
from src.visualizer import DataVisualizer
from src.config import Config

class MonitoringSystem:
    def __init__(self):
        self.config = Config()
        self.monitor = SystemMonitor()
        self.db = DatabaseManager(self.config.db_path)
        self.healer = AutoHealer(self.db)
        self.visualizer = DataVisualizer(self.config.db_path)
        
        # État du système
        self.incident_count = 0
        self.action_count = 0
        
    def monitoring_cycle(self):
        """Exécute un cycle complet de surveillance"""
        print(f"[{datetime.now()}] Début cycle surveillance...")
        
        try:
            # 1. Collecter les métriques
            metrics = self.monitor.get_system_metrics()
            
            # 2. Sauvegarder dans la base
            self.db.save_metrics(metrics)
            
            # 3. Détecter les anomalies
            anomalies = self.monitor.detect_anomalies(metrics)
            
            # 4. Traiter chaque anomalie
            for anomaly in anomalies:
                self.incident_count += 1
                self.db.log_anomaly(anomaly)
                
                # Journaliser
                self.monitor.logger.warning(f"Anomalie détectée: {anomaly}")
                
                # Auto-réparation
                if self.config.config.get('auto_actions', {}).get('enabled', True):
                    response = self.healer.handle_anomaly(anomaly)
                    if response['actions_taken']:
                        self.action_count += len(response['actions_taken'])
                        self.monitor.logger.info(f"Actions: {response['actions_taken']}")
            
            # 5. Générer des graphiques toutes les heures
            current_minute = datetime.now().minute
            if current_minute == 0:  # Toutes les heures à :00
                self.generate_reports()
            
            print(f"[{datetime.now()}] Cycle terminé. Incidents: {len(anomalies)}")
            
        except Exception as e:
            print(f"Erreur dans le cycle de surveillance: {e}")
            self.monitor.logger.error(f"Erreur dans le cycle de surveillance: {e}")
    
    def generate_reports(self):
        """Génère les rapports et graphiques"""
        print(f"[{datetime.now()}] Génération des rapports...")
        
        try:
            # Générer les graphiques pour les dernières 24h
            charts = self.visualizer.generate_all_charts(hours=24)
            
            # Journaliser
            self.monitor.logger.info(f"Graphiques générés: {list(charts.keys())}")
            
        except Exception as e:
            self.monitor.logger.error(f"Erreur génération rapports: {e}")
            print(f"Erreur génération rapports: {e}")
    
    def start(self):
        """Démarre le système de surveillance"""
        print("=" * 60)
        print("🚀 Démarrage du système de surveillance proactive")
        print(f"📊 Services surveillés: {', '.join(self.config.services)}")
        print(f"⏱️  Intervalle: {self.config.monitoring_interval} secondes")
        print("=" * 60)
        
        # Créer les dossiers nécessaires
        os.makedirs('data/logs', exist_ok=True)
        os.makedirs('data/graphs', exist_ok=True)
        
        # Premier cycle immédiat
        self.monitoring_cycle()
        
        # Planifier les cycles suivants
        schedule.every(self.config.monitoring_interval).seconds.do(self.monitoring_cycle)
        
        # Planifier un rapport quotidien à minuit
        schedule.every().day.at("00:00").do(self.generate_reports)
        
        # Boucle principale
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n\nArrêt du système de surveillance...")
            self.shutdown()
    
    def shutdown(self):
        """Arrête proprement le système"""
        print("Sauvegarde des données...")
        print(f"Résumé: {self.incident_count} incidents, {self.action_count} actions")
        print("Au revoir! 👋")

def main():
    """Fonction principale"""
    system = MonitoringSystem()
    system.start()

if __name__ == "__main__":
    main()
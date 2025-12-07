import sqlite3
from datetime import datetime
import json
import os

class DatabaseManager:
    def __init__(self, db_path='data/monitoring.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialise la base de données avec les tables nécessaires"""
        # Créer le dossier si nécessaire
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table pour les métriques système
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                cpu_percent REAL,
                memory_percent REAL,
                memory_used_gb REAL,
                memory_total_gb REAL,
                disk_percent REAL,
                disk_used_gb REAL,
                disk_total_gb REAL,
                disk_free_gb REAL
            )
        ''')
        
        # Table pour l'état des services
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS service_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                service_name TEXT,
                is_active BOOLEAN
            )
        ''')
        
        # Table pour les anomalies
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS anomalies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                anomaly_type TEXT,
                level TEXT,
                details TEXT,
                resolved BOOLEAN DEFAULT 0
            )
        ''')
        
        # Table pour les actions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                action_type TEXT,
                details TEXT,
                success BOOLEAN
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_metrics(self, metrics):
        """Sauvegarde les métriques système"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Sauvegarder métriques système
        cursor.execute('''
            INSERT INTO system_metrics 
            (timestamp, cpu_percent, memory_percent, memory_used_gb, 
             memory_total_gb, disk_percent, disk_used_gb, disk_total_gb, disk_free_gb)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            metrics['timestamp'],
            metrics['cpu_percent'],
            metrics['memory']['percent'],
            metrics['memory']['used_gb'],
            metrics['memory']['total_gb'],
            metrics['disk']['percent'],
            metrics['disk']['used_gb'],
            metrics['disk']['total_gb'],
            metrics['disk']['free_gb']
        ))
        
        # Sauvegarder état des services
        for service, status in metrics['services'].items():
            cursor.execute('''
                INSERT INTO service_status (timestamp, service_name, is_active)
                VALUES (?, ?, ?)
            ''', (metrics['timestamp'], service, 1 if status else 0))
        
        conn.commit()
        conn.close()
    
    def log_anomaly(self, anomaly):
        """Enregistre une anomalie"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO anomalies (timestamp, anomaly_type, level, details)
            VALUES (?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            anomaly['type'],
            anomaly.get('level', 'WARNING'),
            json.dumps(anomaly)
        ))
        
        conn.commit()
        conn.close()
    
    def log_action(self, action):
        """Enregistre une action corrective"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO actions (timestamp, action_type, details, success)
            VALUES (?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            action['type'],
            json.dumps(action),
            action.get('success', False)
        ))
        
        conn.commit()
        conn.close()
    
    def get_recent_metrics(self, hours=24):
        """Récupère les métriques des dernières heures"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM system_metrics 
            WHERE timestamp >= datetime('now', ?)
            ORDER BY timestamp
        ''', (f'-{hours} hours',))
        
        rows = cursor.fetchall()
        conn.close()
        
        return rows
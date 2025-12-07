import psutil
import subprocess
import time
import logging
from datetime import datetime
import os
import sys

# Import relatif
try:
    from .config import Config
except ImportError:
    # Pour les tests directs
    from config import Config

class SystemMonitor:
    def __init__(self):
        self.config = Config()
        self.setup_logging()
        
    def setup_logging(self):
        """Configure le logging"""
        log_path = self.config.config.get('database', {}).get('log_path', 'data/logs/monitoring.log')
        
        # Créer le dossier logs si nécessaire
        log_dir = os.path.dirname(log_path)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        logging.basicConfig(
            filename=log_path,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def check_service(self, service_name):
        """Vérifie l'état d'un service - version améliorée pour Windows"""
        try:
            if os.name == 'nt':  # Windows
                # Pour les processus Windows (.exe)
                service_lower = service_name.lower()
                
                # Cas spéciaux
                if service_lower == 'system':
                    return True  # Toujours présent sur Windows
                
                # Recherche dans les processus
                for proc in psutil.process_iter(['name']):
                    try:
                        proc_name = proc.info['name'].lower()
                        if proc_name == service_lower:
                            return True
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                # Pour explorer.exe, vérifier aussi s'il y a au moins un processus Windows actif
                if service_lower == 'explorer.exe':
                    for proc in psutil.process_iter(['name']):
                        try:
                            if 'explorer' in proc.info['name'].lower():
                                return True
                        except:
                            continue
                
                # Pour svchost.exe, vérifier s'il existe au moins un svchost
                if service_lower == 'svchost.exe':
                    for proc in psutil.process_iter(['name']):
                        try:
                            if 'svchost' in proc.info['name'].lower():
                                return True
                        except:
                            continue
                
                # Pour SearchIndexer.exe
                if service_lower == 'searchindexer.exe':
                    for proc in psutil.process_iter(['name']):
                        try:
                            if 'searchindexer' in proc.info['name'].lower():
                                return True
                        except:
                            continue
                
                return False
            else:  # Linux/Unix
                result = subprocess.run(
                    ['systemctl', 'is-active', service_name],
                    capture_output=True,
                    text=True,
                    shell=True
                )
                is_active = result.stdout.strip() == 'active'
                return is_active
        except Exception as e:
            self.logger.error(f"Erreur vérification service {service_name}: {e}")
            return False
    
    def get_cpu_usage(self):
        """Récupère l'utilisation CPU"""
        return psutil.cpu_percent(interval=1)
    
    def get_memory_usage(self):
        """Récupère l'utilisation mémoire"""
        memory = psutil.virtual_memory()
        return {
            'percent': memory.percent,
            'used_gb': memory.used / (1024**3),
            'total_gb': memory.total / (1024**3)
        }
    
    def get_disk_usage(self, path=None):
        """Récupère l'utilisation disque"""
        if path is None:
            path = 'C:\\' if os.name == 'nt' else '/'
        
        disk = psutil.disk_usage(path)
        return {
            'percent': disk.percent,
            'used_gb': disk.used / (1024**3),
            'total_gb': disk.total / (1024**3),
            'free_gb': disk.free / (1024**3)
        }
    
    def get_system_metrics(self):
        """Récupère toutes les métriques système"""
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'cpu_percent': self.get_cpu_usage(),
            'memory': self.get_memory_usage(),
            'disk': self.get_disk_usage(),
            'services': {}
        }
        
        # Vérifier l'état des services
        for service in self.config.services:
            metrics['services'][service] = self.check_service(service)
        
        return metrics
    
    def detect_anomalies(self, metrics):
        """Détecte les anomalies basées sur les seuils"""
        anomalies = []
        thresholds = self.config.thresholds
        
        # Vérifier CPU
        cpu_value = metrics['cpu_percent']
        cpu_critical = thresholds.get('cpu_critical', 85)
        cpu_warning = thresholds.get('cpu_warning', 70)
        
        if cpu_value > cpu_critical:
            anomalies.append({
                'type': 'CPU',
                'level': 'CRITICAL',
                'value': cpu_value,
                'threshold': cpu_critical
            })
        elif cpu_value > cpu_warning:
            anomalies.append({
                'type': 'CPU',
                'level': 'WARNING',
                'value': cpu_value,
                'threshold': cpu_warning
            })
        
        # Vérifier mémoire
        memory_value = metrics['memory']['percent']
        memory_critical = thresholds.get('memory_critical', 85)
        memory_warning = thresholds.get('memory_warning', 70)
        
        if memory_value > memory_critical:
            anomalies.append({
                'type': 'MEMORY',
                'level': 'CRITICAL',
                'value': memory_value,
                'threshold': memory_critical
            })
        elif memory_value > memory_warning:
            anomalies.append({
                'type': 'MEMORY',
                'level': 'WARNING',
                'value': memory_value,
                'threshold': memory_warning
            })
        
        # Vérifier disque
        disk_value = metrics['disk']['percent']
        disk_critical = thresholds.get('disk_critical', 90)
        disk_warning = thresholds.get('disk_warning', 80)
        
        if disk_value > disk_critical:
            anomalies.append({
                'type': 'DISK',
                'level': 'CRITICAL',
                'value': disk_value,
                'threshold': disk_critical
            })
        elif disk_value > disk_warning:
            anomalies.append({
                'type': 'DISK',
                'level': 'WARNING',
                'value': disk_value,
                'threshold': disk_warning
            })
        
        # Vérifier services
        for service, status in metrics['services'].items():
            if not status:
                anomalies.append({
                    'type': 'SERVICE',
                    'level': 'CRITICAL',
                    'service': service,
                    'status': 'INACTIVE'
                })
        
        return anomalies


# Test direct si le fichier est exécuté seul
if __name__ == "__main__":
    print("Test du moniteur système...")
    monitor = SystemMonitor()
    
    print("Services configurés:", monitor.config.services)
    print("Seuils:", monitor.config.thresholds)
    print()
    
    # Tester la vérification des services
    for service in monitor.config.services:
        status = monitor.check_service(service)
        print(f"{service}: {'ACTIF' if status else 'INACTIF'}")
    
    print()
    
    # Tester les métriques
    metrics = monitor.get_system_metrics()
    print(f"CPU: {metrics['cpu_percent']}%")
    print(f"Mémoire: {metrics['memory']['percent']}%")
    print(f"Disque: {metrics['disk']['percent']}%")
    
    print()
    
    # Tester la détection d'anomalies
    anomalies = monitor.detect_anomalies(metrics)
    print(f"Anomalies détectées: {len(anomalies)}")
    for anomaly in anomalies:
        print(f"  - {anomaly}")
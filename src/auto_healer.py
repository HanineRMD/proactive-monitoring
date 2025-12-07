import subprocess
import shutil
import os
import tempfile
import logging
import time

class AutoHealer:
    def __init__(self, db_manager):
        self.db = db_manager
        self.logger = logging.getLogger(__name__)
    
    def restart_service(self, service_name):
        """Tente de redémarrer un service"""
        try:
            if os.name == 'nt':  # Windows
                # Pour Windows, on pourrait utiliser net start/stop
                # Pour simplifier, on retourne False
                self.logger.warning(f"Redémarrage de service non supporté sur Windows pour {service_name}")
                return False
            else:  # Linux/Unix
                result = subprocess.run(
                    ['sudo', 'systemctl', 'restart', service_name],
                    capture_output=True,
                    text=True
                )
                
                success = result.returncode == 0
                action = {
                    'type': 'SERVICE_RESTART',
                    'service': service_name,
                    'success': success,
                    'output': result.stdout
                }
                
                self.db.log_action(action)
                self.logger.info(f"Redémarrage service {service_name}: {success}")
                return success
                
        except Exception as e:
            self.logger.error(f"Erreur redémarrage {service_name}: {e}")
            return False
    
    def clear_temp_files(self):
        """Nettoie les fichiers temporaires"""
        try:
            freed_space = 0
            if os.name == 'nt':  # Windows
                temp_dirs = [tempfile.gettempdir(), os.environ.get('TEMP', ''), os.environ.get('TMP', '')]
            else:  # Linux/Unix
                temp_dirs = ['/tmp', '/var/tmp', tempfile.gettempdir()]
            
            for temp_dir in temp_dirs:
                if temp_dir and os.path.exists(temp_dir):
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            try:
                                filepath = os.path.join(root, file)
                                if os.path.isfile(filepath):
                                    # Supprimer les fichiers de plus de 7 jours
                                    if os.path.getmtime(filepath) < (time.time() - 7*86400):
                                        file_size = os.path.getsize(filepath)
                                        os.remove(filepath)
                                        freed_space += file_size
                            except:
                                continue
            
            action = {
                'type': 'CLEAN_TEMP_FILES',
                'freed_space_mb': freed_space / (1024*1024),
                'success': True
            }
            
            self.db.log_action(action)
            self.logger.info(f"Nettoyage fichiers temporaires: {freed_space/1024**2:.2f} MB libérés")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur nettoyage fichiers: {e}")
            return False
    
    def kill_high_cpu_processes(self, threshold=80):
        """Arrête les processus utilisant trop de CPU"""
        try:
            import psutil
            killed = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                try:
                    if proc.info['cpu_percent'] is not None and proc.info['cpu_percent'] > threshold:
                        p = psutil.Process(proc.info['pid'])
                        p.terminate()
                        killed.append(proc.info['name'])
                except:
                    continue
            
            action = {
                'type': 'KILL_HIGH_CPU',
                'processes_killed': killed,
                'threshold': threshold
            }
            
            self.db.log_action(action)
            return killed
            
        except Exception as e:
            self.logger.error(f"Erreur gestion CPU: {e}")
            return []
    
    def handle_anomaly(self, anomaly):
        """Traite une anomalie détectée"""
        response = {
            'anomaly': anomaly,
            'actions_taken': [],
            'resolved': False
        }
        
        if anomaly['type'] == 'SERVICE':
            if anomaly['status'] == 'INACTIVE':
                success = self.restart_service(anomaly['service'])
                response['actions_taken'].append(f"Redémarrage service {anomaly['service']}")
                response['resolved'] = success
        
        elif anomaly['type'] == 'DISK':
            if anomaly['level'] == 'CRITICAL':
                success = self.clear_temp_files()
                response['actions_taken'].append("Nettoyage fichiers temporaires")
                response['resolved'] = success
        
        elif anomaly['type'] == 'CPU':
            if anomaly['level'] == 'CRITICAL':
                # Prioriser les processus gourmands en CPU
                killed = self.kill_high_cpu_processes()
                if killed:
                    response['actions_taken'].append(f"Arrêt processus CPU intensifs: {', '.join(killed)}")
        
        return response
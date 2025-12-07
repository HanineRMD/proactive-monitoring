import yaml
import os

class Config:
    def __init__(self, config_file='config.yaml'):
        # Vérifier si le fichier config existe
        if not os.path.exists(config_file):
            print(f"Fichier {config_file} non trouvé. Création d'une configuration par défaut...")
            self.create_default_config(config_file)
        
        with open(config_file, 'r') as f:
            self.config = yaml.safe_load(f)
    
    def create_default_config(self, config_file):
        """Crée une configuration par défaut"""
        default_config = {
            'services': ['nginx', 'mysql', 'ssh'],
            'thresholds': {
                'cpu_warning': 80,
                'cpu_critical': 90,
                'memory_warning': 75,
                'memory_critical': 90,
                'disk_warning': 80,
                'disk_critical': 95
            },
            'monitoring_interval': 60,
            'log_level': 'INFO',
            'database': {
                'path': 'data/monitoring.db',
                'log_path': 'data/logs/monitoring.log'
            },
            'auto_actions': {
                'enabled': True,
                'restart_service': True,
                'clear_temp_files': True,
                'notify': False
            }
        }
        
        # Créer le dossier data si nécessaire
        os.makedirs('data/logs', exist_ok=True)
        
        with open(config_file, 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False)
        
        print(f"Configuration par défaut créée dans {config_file}")
    
    @property
    def services(self):
        return self.config.get('services', [])
    
    @property
    def thresholds(self):
        return self.config.get('thresholds', {})
    
    @property
    def monitoring_interval(self):
        return self.config.get('monitoring_interval', 300)
    
    @property
    def db_path(self):
        return self.config.get('database', {}).get('path', 'data/monitoring.db')
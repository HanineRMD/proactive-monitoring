#!/usr/bin/env python3
"""
Test de la configuration Windows
"""

import sys
import os

# Ajouter src au chemin
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.monitor import SystemMonitor
    from src.config import Config
except ImportError as e:
    print(f"Erreur d'importation: {e}")
    print("Vérifiez que les fichiers sont dans le dossier src/")
    sys.exit(1)

def test_windows_services():
    """Test des services Windows"""
    print("=" * 60)
    print("🧪 Test de configuration Windows")
    print("=" * 60)
    
    try:
        config = Config()
        monitor = SystemMonitor()
        
        print(f"Services configurés: {config.services}")
        print(f"Seuils: {config.thresholds}")
        print()
        
        # Tester chaque service
        print("Vérification des services:")
        for service in config.services:
            try:
                status = monitor.check_service(service)
                print(f"  {service}: {'✓ ACTIF' if status else '✗ INACTIF'}")
            except Exception as e:
                print(f"  {service}: ERREUR - {e}")
        
        print()
        
        # Tester les ressources
        print("Vérification des ressources:")
        metrics = monitor.get_system_metrics()
        print(f"  CPU: {metrics['cpu_percent']}%")
        print(f"  Mémoire: {metrics['memory']['percent']}%")
        print(f"  Disque: {metrics['disk']['percent']}%")
        
        print()
        
        # Vérifier l'état des services dans les métriques
        print("État des services (dans métriques):")
        for service, status in metrics['services'].items():
            print(f"  {service}: {'✓ ACTIF' if status else '✗ INACTIF'}")
        
        print()
        
        # Vérifier les anomalies
        anomalies = monitor.detect_anomalies(metrics)
        if anomalies:
            print(f"⚠️  Anomalies détectées ({len(anomalies)}):")
            for anomaly in anomalies:
                if anomaly['type'] == 'SERVICE':
                    print(f"  - SERVICE: {anomaly['service']} ({anomaly['level']})")
                else:
                    print(f"  - {anomaly['type']}: {anomaly['level']} (valeur: {anomaly.get('value', 'N/A')}%, seuil: {anomaly.get('threshold', 'N/A')}%)")
        else:
            print("✅ Aucune anomalie détectée")
        
        print()
        print("✅ Test terminé!")
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_windows_services()
#!/usr/bin/env python3
"""
Test pour vérifier le fonctionnement sur Windows
"""

import psutil
import os
from datetime import datetime

def list_windows_processes():
    """Liste les processus Windows courants"""
    print("Processus Windows courants :")
    common_processes = [
        'svchost.exe', 'explorer.exe', 'SearchIndexer.exe',
        'System', 'Registry', 'smss.exe', 'csrss.exe',
        'wininit.exe', 'services.exe', 'lsass.exe',
        'winlogon.exe', 'spoolsv.exe'
    ]
    
    for proc in psutil.process_iter(['name', 'pid', 'status']):
        try:
            if proc.info['name'].lower() in [p.lower() for p in common_processes]:
                print(f"  ✓ {proc.info['name']} (PID: {proc.info['pid']}) - {proc.info['status']}")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

def check_resources():
    """Vérifie les ressources système"""
    print("\nRessources système :")
    
    # CPU
    cpu = psutil.cpu_percent(interval=1)
    print(f"  CPU: {cpu}%")
    
    # Mémoire
    mem = psutil.virtual_memory()
    print(f"  Mémoire: {mem.percent}% utilisé ({mem.used/1024**3:.1f} Go / {mem.total/1024**3:.1f} Go)")
    
    # Disque
    disk = psutil.disk_usage('C:\\')
    print(f"  Disque C:: {disk.percent}% utilisé ({disk.used/1024**3:.1f} Go / {disk.total/1024**3:.1f} Go)")

def main():
    print("=" * 60)
    print("🧪 Test du système de surveillance sur Windows")
    print("=" * 60)
    
    list_windows_processes()
    check_resources()
    
    print("\n✅ Test terminé !")
    print("Conseil : Modifiez config.yaml avec les processus Windows ci-dessus")

if __name__ == "__main__":
    main()
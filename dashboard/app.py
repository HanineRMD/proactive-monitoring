from flask import Flask, render_template, jsonify
import sqlite3
from datetime import datetime, timedelta
import json
import os
import psutil

app = Flask(__name__)

def get_db_connection():
    """Établit une connexion à la base SQLite"""
    conn = sqlite3.connect('../data/monitoring.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    """Page principale du tableau de bord"""
    return render_template('index.html')

@app.route('/api/status')
def get_current_status():
    """API pour le statut actuel du système"""
    try:
        # Récupérer les métriques actuelles
        cpu = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('C:\\')
        
        # Vérifier les services Windows
        services_to_check = ['explorer.exe', 'svchost.exe', 'SearchIndexer.exe', 'System']
        services_status = {}
        
        for service in services_to_check:
            if service == 'System':
                services_status[service] = True
            else:
                status = False
                for proc in psutil.process_iter(['name']):
                    try:
                        if service.lower() in proc.info['name'].lower():
                            status = True
                            break
                    except:
                        continue
                services_status[service] = status
        
        return jsonify({
            'cpu_percent': cpu,
            'memory_percent': memory.percent,
            'memory_used_gb': memory.used / (1024**3),
            'memory_total_gb': memory.total / (1024**3),
            'disk_percent': disk.percent,
            'disk_used_gb': disk.used / (1024**3),
            'disk_total_gb': disk.total / (1024**3),
            'disk_free_gb': disk.free / (1024**3),
            'services': services_status,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics/<int:hours>')
def get_metrics_history(hours):
    """API pour l'historique des métriques"""
    try:
        conn = get_db_connection()
        
        cursor = conn.execute('''
            SELECT timestamp, cpu_percent, memory_percent, disk_percent
            FROM system_metrics 
            WHERE timestamp >= datetime('now', ?)
            ORDER BY timestamp
        ''', (f'-{hours} hours',))
        
        metrics = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({
            'metrics': metrics,
            'count': len(metrics),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/anomalies/<int:hours>')
def get_recent_anomalies(hours):
    """API pour les anomalies récentes"""
    try:
        conn = get_db_connection()
        
        cursor = conn.execute('''
            SELECT * FROM anomalies 
            WHERE timestamp >= datetime('now', ?)
            ORDER BY timestamp DESC
            LIMIT 20
        ''', (f'-{hours} hours',))
        
        anomalies = []
        for row in cursor.fetchall():
            anomaly = dict(row)
            try:
                anomaly['details'] = json.loads(anomaly['details'])
            except:
                anomaly['details'] = {}
            anomalies.append(anomaly)
        
        conn.close()
        
        return jsonify({
            'anomalies': anomalies,
            'count': len(anomalies),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/actions/<int:hours>')
def get_recent_actions(hours):
    """API pour les actions récentes"""
    try:
        conn = get_db_connection()
        
        cursor = conn.execute('''
            SELECT * FROM actions 
            WHERE timestamp >= datetime('now', ?)
            ORDER BY timestamp DESC
            LIMIT 20
        ''', (f'-{hours} hours',))
        
        actions = []
        for row in cursor.fetchall():
            action = dict(row)
            try:
                action['details'] = json.loads(action['details'])
            except:
                action['details'] = {}
            actions.append(action)
        
        conn.close()
        
        return jsonify({
            'actions': actions,
            'count': len(actions),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/summary')
def get_system_summary():
    """API pour un résumé du système"""
    try:
        conn = get_db_connection()
        
        # Dernières métriques
        cursor = conn.execute('''
            SELECT * FROM system_metrics 
            ORDER BY timestamp DESC 
            LIMIT 1
        ''')
        last_metrics = dict(cursor.fetchone()) if cursor.fetchone() else None
        
        # Statistiques
        cursor.execute("SELECT COUNT(*) as total FROM anomalies")
        total_anomalies = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM actions")
        total_actions = cursor.fetchone()['total']
        
        cursor.execute('''
            SELECT anomaly_type, COUNT(*) as count 
            FROM anomalies 
            WHERE timestamp >= datetime('now', '-24 hours')
            GROUP BY anomaly_type
        ''')
        anomalies_today = {row['anomaly_type']: row['count'] for row in cursor.fetchall()}
        
        cursor.execute('''
            SELECT action_type, COUNT(*) as count 
            FROM actions 
            WHERE timestamp >= datetime('now', '-24 hours')
            GROUP BY action_type
        ''')
        actions_today = {row['action_type']: row['count'] for row in cursor.fetchall()}
        
        conn.close()
        
        return jsonify({
            'last_metrics': last_metrics,
            'stats': {
                'total_anomalies': total_anomalies,
                'total_actions': total_actions,
                'anomalies_today': anomalies_today,
                'actions_today': actions_today
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health')
def health_check():
    """API de santé du système"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'services': {
            'database': os.path.exists('../data/monitoring.db'),
            'logs': os.path.exists('../data/logs/monitoring.log'),
            'api': True
        }
    })

if __name__ == '__main__':
    # Vérifier que le dossier templates existe
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    # Vérifier que le fichier index.html existe
    template_path = 'templates/index.html'
    if not os.path.exists(template_path):
        print(f"⚠️  Création du fichier {template_path}...")
        with open(template_path, 'w', encoding='utf-8') as f:
            # Écrivez votre HTML ici ou copiez-le depuis votre question
            f.write("""<!DOCTYPE html>
<html>
<head>
    <title>Tableau de bord Surveillance en Temps Réel</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; }
        
        .header {
            background: linear-gradient(135deg, #2c3e50, #4a6491);
            color: white;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        
        .card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        
        .card h3 {
            color: #2c3e50;
            margin-bottom: 15px;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }
        
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .status-ok { background: #2ecc71; }
        .status-warning { background: #f39c12; }
        .status-critical { background: #e74c3c; }
        
        .metric {
            display: flex;
            justify-content: space-between;
            margin: 10px 0;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 5px;
        }
        
        .metric-value {
            font-weight: bold;
            font-size: 1.2em;
        }
        
        .incident-list {
            max-height: 300px;
            overflow-y: auto;
        }
        
        .incident-item {
            padding: 10px;
            border-left: 4px solid #e74c3c;
            margin: 5px 0;
            background: #fff5f5;
        }
        
        .action-item {
            padding: 10px;
            border-left: 4px solid #3498db;
            margin: 5px 0;
            background: #f0f8ff;
        }
        
        .timestamp {
            font-size: 0.8em;
            color: #7f8c8d;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 Système de Surveillance Proactive</h1>
        <p>Monitoring en temps réel et auto-réparation</p>
        <div style="margin-top: 10px;">
            <span id="last-update"></span>
            <span id="system-status" style="float: right;"></span>
        </div>
    </div>
    
    <div class="container">
        <!-- Métriques en temps réel -->
        <div class="grid">
            <div class="card">
                <h3>📈 Métriques en Temps Réel</h3>
                <div id="real-time-metrics"></div>
            </div>
            
            <div class="card">
                <h3>⚠️ Dernières Anomalies</h3>
                <div id="recent-anomalies" class="incident-list"></div>
            </div>
            
            <div class="card">
                <h3>🔧 Actions Récentes</h3>
                <div id="recent-actions" class="incident-list"></div>
            </div>
        </div>
        
        <!-- Graphiques -->
        <div class="grid">
            <div class="card">
                <h3>📊 Utilisation CPU</h3>
                <div id="cpu-chart" style="height: 300px;"></div>
            </div>
            
            <div class="card">
                <h3>💾 Utilisation Mémoire</h3>
                <div id="memory-chart" style="height: 300px;"></div>
            </div>
            
            <div class="card">
                <h3>💿 Utilisation Disque</h3>
                <div id="disk-chart" style="height: 300px;"></div>
            </div>
        </div>
    </div>
    
    <script>
        // Fonction de formatage
        function formatDate(dateString) {
            const date = new Date(dateString);
            return date.toLocaleString();
        }
        
        // Fonction pour mettre à jour les métriques
        async function updateMetrics() {
            try {
                // Récupérer les données de l'API
                const [statusRes, metricsRes, anomaliesRes, actionsRes] = await Promise.all([
                    fetch('/api/status'),
                    fetch('/api/metrics/6'),
                    fetch('/api/anomalies/6'),
                    fetch('/api/actions/6')
                ]);
                
                const status = await statusRes.json();
                const metricsData = await metricsRes.json();
                const anomaliesData = await anomaliesRes.json();
                const actionsData = await actionsRes.json();
                
                // Mettre à jour le timestamp
                document.getElementById('last-update').innerHTML = 
                    `Dernière mise à jour: ${formatDate(status.timestamp)}`;
                
                // Afficher les métriques en temps réel
                const metricsHtml = `
                    <div class="metric">
                        <span>CPU:</span>
                        <span class="metric-value" style="color: ${status.cpu_percent > 70 ? '#e74c3c' : status.cpu_percent > 50 ? '#f39c12' : '#27ae60'}">
                            ${status.cpu_percent.toFixed(1)}%
                        </span>
                    </div>
                    <div class="metric">
                        <span>Mémoire:</span>
                        <span class="metric-value" style="color: ${status.memory_percent > 70 ? '#e74c3c' : status.memory_percent > 50 ? '#f39c12' : '#27ae60'}">
                            ${status.memory_percent.toFixed(1)}%
                        </span>
                    </div>
                    <div class="metric">
                        <span>Disque:</span>
                        <span class="metric-value" style="color: ${status.disk_percent > 80 ? '#e74c3c' : status.disk_percent > 70 ? '#f39c12' : '#27ae60'}">
                            ${status.disk_percent.toFixed(1)}%
                        </span>
                    </div>
                `;
                document.getElementById('real-time-metrics').innerHTML = metricsHtml;
                
                // Afficher les anomalies
                if (anomaliesData.anomalies && anomaliesData.anomalies.length > 0) {
                    let anomaliesHtml = '';
                    anomaliesData.anomalies.forEach(anomaly => {
                        const levelColor = anomaly.level === 'CRITICAL' ? '#e74c3c' : '#f39c12';
                        anomaliesHtml += `
                            <div class="incident-item" style="border-left-color: ${levelColor}">
                                <strong>${anomaly.anomaly_type}</strong> - <span style="color: ${levelColor}">${anomaly.level}</span>
                                ${anomaly.details.service ? ` (${anomaly.details.service})` : ''}
                                ${anomaly.details.value ? ` - Valeur: ${anomaly.details.value}%` : ''}
                                <div class="timestamp">${formatDate(anomaly.timestamp)}</div>
                            </div>
                        `;
                    });
                    document.getElementById('recent-anomalies').innerHTML = anomaliesHtml;
                } else {
                    document.getElementById('recent-anomalies').innerHTML = '<p style="color: #7f8c8d; text-align: center;">Aucune anomalie récente</p>';
                }
                
                // Afficher les actions
                if (actionsData.actions && actionsData.actions.length > 0) {
                    let actionsHtml = '';
                    actionsData.actions.forEach(action => {
                        const successIcon = action.success ? '✅' : '❌';
                        const color = action.success ? 'green' : 'red';
                        actionsHtml += `
                            <div class="action-item">
                                <span style="color: ${color}">${successIcon}</span> <strong>${action.action_type}</strong>
                                ${action.details.service ? ` - ${action.details.service}` : ''}
                                ${action.details.freed_space_mb ? ` (${action.details.freed_space_mb.toFixed(1)} MB libérés)` : ''}
                                <div class="timestamp">${formatDate(action.timestamp)}</div>
                            </div>
                        `;
                    });
                    document.getElementById('recent-actions').innerHTML = actionsHtml;
                } else {
                    document.getElementById('recent-actions').innerHTML = '<p style="color: #7f8c8d; text-align: center;">Aucune action récente</p>';
                }
                
                // Mettre à jour les graphiques
                if (metricsData.metrics && metricsData.metrics.length > 0) {
                    updateCharts(metricsData.metrics);
                }
                
            } catch (error) {
                console.error('Erreur mise à jour:', error);
                document.getElementById('last-update').innerHTML = 'Erreur de connexion à l\'API';
            }
        }
        
        // Fonction pour mettre à jour les graphiques
        function updateCharts(metrics) {
            const timestamps = metrics.map(m => new Date(m.timestamp));
            const cpuData = metrics.map(m => m.cpu_percent);
            const memoryData = metrics.map(m => m.memory_percent);
            const diskData = metrics.map(m => m.disk_percent);
            
            // Graphique CPU
            const cpuTrace = {
                x: timestamps,
                y: cpuData,
                type: 'scatter',
                mode: 'lines+markers',
                name: 'CPU',
                line: {color: '#3498db', width: 2}
            };
            
            Plotly.newPlot('cpu-chart', [cpuTrace], {
                title: 'Utilisation CPU (%)',
                xaxis: {title: 'Temps'},
                yaxis: {title: 'Pourcentage', range: [0, 100]},
                height: 280
            });
            
            // Graphique Mémoire
            const memoryTrace = {
                x: timestamps,
                y: memoryData,
                type: 'scatter',
                mode: 'lines+markers',
                name: 'Mémoire',
                line: {color: '#2ecc71', width: 2}
            };
            
            Plotly.newPlot('memory-chart', [memoryTrace], {
                title: 'Utilisation Mémoire (%)',
                xaxis: {title: 'Temps'},
                yaxis: {title: 'Pourcentage', range: [0, 100]},
                height: 280
            });
            
            // Graphique Disque
            const diskTrace = {
                x: timestamps,
                y: diskData,
                type: 'scatter',
                mode: 'lines+markers',
                name: 'Disque',
                line: {color: '#e74c3c', width: 2}
            };
            
            Plotly.newPlot('disk-chart', [diskTrace], {
                title: 'Utilisation Disque (%)',
                xaxis: {title: 'Temps'},
                yaxis: {title: 'Pourcentage', range: [0, 100]},
                height: 280
            });
        }
        
        // Mettre à jour toutes les 5 secondes
        setInterval(updateMetrics, 5000);
        
        // Premier chargement
        updateMetrics();
    </script>
</body>
</html>""")
    
    print("🚀 Démarrage du serveur Flask...")
    print("🌐 Tableau de bord disponible à: http://localhost:5000")
    print("📊 API disponible à: http://localhost:5000/api/status")
    app.run(host='0.0.0.0', port=5000, debug=True)
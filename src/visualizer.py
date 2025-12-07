import matplotlib.pyplot as plt
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

class DataVisualizer:
    def __init__(self, db_path='data/monitoring.db'):
        self.db_path = db_path
        self.output_dir = 'data/graphs'
        os.makedirs(self.output_dir, exist_ok=True)
    
    def load_data(self, hours=24):
        """Charge les données depuis la base"""
        conn = sqlite3.connect(self.db_path)
        
        # Charger métriques système
        df_metrics = pd.read_sql_query(f"""
            SELECT * FROM system_metrics 
            WHERE timestamp >= datetime('now', '-{hours} hours')
            ORDER BY timestamp
        """, conn)
        
        # Charger anomalies
        df_anomalies = pd.read_sql_query(f"""
            SELECT * FROM anomalies 
            WHERE timestamp >= datetime('now', '-{hours} hours')
            ORDER BY timestamp
        """, conn)
        
        # Charger actions
        df_actions = pd.read_sql_query(f"""
            SELECT * FROM actions 
            WHERE timestamp >= datetime('now', '-{hours} hours')
            ORDER BY timestamp
        """, conn)
        
        # Charger statut services
        df_services = pd.read_sql_query(f"""
            SELECT * FROM service_status 
            WHERE timestamp >= datetime('now', '-{hours} hours')
            ORDER BY timestamp
        """, conn)
        
        conn.close()
        
        # Convertir les timestamps
        for df in [df_metrics, df_anomalies, df_actions, df_services]:
            if 'timestamp' in df.columns and not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        return df_metrics, df_anomalies, df_actions, df_services
    
    def create_resource_usage_plot(self, df_metrics):
        """Crée un graphique d'utilisation des ressources"""
        if df_metrics.empty:
            return None
            
        fig = make_subplots(
            rows=3, cols=1,
            subplot_titles=('Utilisation CPU (%)', 'Utilisation Mémoire (%)', 'Utilisation Disque (%)'),
            vertical_spacing=0.1
        )
        
        # CPU
        fig.add_trace(
            go.Scatter(x=df_metrics['timestamp'], y=df_metrics['cpu_percent'],
                      mode='lines+markers', name='CPU', line=dict(color='blue')),
            row=1, col=1
        )
        
        # Mémoire
        fig.add_trace(
            go.Scatter(x=df_metrics['timestamp'], y=df_metrics['memory_percent'],
                      mode='lines+markers', name='Mémoire', line=dict(color='green')),
            row=2, col=1
        )
        
        # Disque
        fig.add_trace(
            go.Scatter(x=df_metrics['timestamp'], y=df_metrics['disk_percent'],
                      mode='lines+markers', name='Disque', line=dict(color='red')),
            row=3, col=1
        )
        
        # Ajouter des lignes de seuil
        fig.add_hline(y=80, line_dash="dash", line_color="orange", row=1, col=1)
        fig.add_hline(y=90, line_dash="dash", line_color="red", row=1, col=1)
        
        fig.update_layout(height=800, showlegend=False, title_text="Évolution des Ressources Système")
        fig.update_xaxes(title_text="Temps")
        
        # Sauvegarder
        output_path = os.path.join(self.output_dir, 'resource_usage.html')
        fig.write_html(output_path)
        
        return output_path
    
    def create_anomalies_chart(self, df_anomalies):
        """Crée un graphique des anomalies"""
        if df_anomalies.empty:
            return None
        
        # Compter les anomalies par type et niveau
        anomalies_by_type = df_anomalies.groupby(['anomaly_type', 'level']).size().reset_index(name='count')
        
        fig = px.bar(anomalies_by_type, 
                    x='anomaly_type', 
                    y='count',
                    color='level',
                    barmode='group',
                    title='Nombre d\'Anomalies par Type et Niveau',
                    labels={'anomaly_type': 'Type d\'Anomalie', 'count': 'Nombre'},
                    color_discrete_map={'CRITICAL': 'red', 'WARNING': 'orange'})
        
        output_path = os.path.join(self.output_dir, 'anomalies_chart.html')
        fig.write_html(output_path)
        
        return output_path
    
    def create_service_uptime_chart(self, df_services):
        """Crée un graphique de disponibilité des services"""
        if df_services.empty:
            return None
        
        # Calculer le taux de disponibilité par service
        service_stats = df_services.groupby('service_name')['is_active'].mean().reset_index()
        service_stats['uptime_percent'] = service_stats['is_active'] * 100
        
        fig = px.bar(service_stats,
                    x='service_name',
                    y='uptime_percent',
                    title='Disponibilité des Services (%)',
                    labels={'service_name': 'Service', 'uptime_percent': 'Disponibilité (%)'},
                    color='uptime_percent',
                    color_continuous_scale='RdYlGn')
        
        output_path = os.path.join(self.output_dir, 'service_uptime.html')
        fig.write_html(output_path)
        
        return output_path
    
    def create_actions_timeline(self, df_actions):
        """Crée une timeline des actions correctives"""
        if df_actions.empty:
            return None
        
        # S'assurer que les colonnes nécessaires existent
        df_actions['end_time'] = df_actions['timestamp'] + pd.Timedelta(minutes=5)
        
        fig = px.timeline(df_actions,
                         x_start="timestamp",
                         x_end=df_actions['end_time'],
                         y="action_type",
                         color="success",
                         title="Timeline des Actions Correctives",
                         labels={'action_type': 'Type d\'Action', 'timestamp': 'Temps'},
                         color_discrete_map={True: 'green', False: 'red'})
        
        output_path = os.path.join(self.output_dir, 'actions_timeline.html')
        fig.write_html(output_path)
        
        return output_path
    
    def generate_all_charts(self, hours=24):
        """Génère tous les graphiques"""
        df_metrics, df_anomalies, df_actions, df_services = self.load_data(hours)
        
        charts = {}
        
        # Générer chaque graphique
        charts['resource_usage'] = self.create_resource_usage_plot(df_metrics)
        charts['anomalies'] = self.create_anomalies_chart(df_anomalies)
        charts['service_uptime'] = self.create_service_uptime_chart(df_services)
        charts['actions_timeline'] = self.create_actions_timeline(df_actions)
        
        # Créer un tableau de bord combiné
        dashboard_path = self.create_dashboard(charts)
        charts['dashboard'] = dashboard_path
        
        return charts
    
    def create_dashboard(self, charts):
        """Crée un fichier HTML de tableau de bord"""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Tableau de bord Surveillance</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }
                .chart-container { margin: 20px 0; border: 1px solid #ddd; padding: 10px; border-radius: 5px; }
                iframe { width: 100%; height: 400px; border: none; }
                .grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }
                @media (max-width: 768px) { .grid { grid-template-columns: 1fr; } }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📊 Tableau de bord de Surveillance Proactive</h1>
                <p>Dernière mise à jour: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
            </div>
            
            <div class="grid">
        """
        
        # Ajouter chaque graphique
        for name, path in charts.items():
            if path and name != 'dashboard':
                html_content += f"""
                <div class="chart-container">
                    <h3>{name.replace('_', ' ').title()}</h3>
                    <iframe src="{os.path.basename(path)}"></iframe>
                </div>
                """
        
        html_content += """
            </div>
        </body>
        </html>
        """
        
        dashboard_path = os.path.join(self.output_dir, 'dashboard.html')
        with open(dashboard_path, 'w') as f:
            f.write(html_content)
        
        return dashboard_path
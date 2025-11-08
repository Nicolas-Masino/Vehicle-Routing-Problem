"""
Módulo de visualización de rutas optimizadas
Genera mapas y gráficos para análisis de resultados
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from typing import List, Tuple
import folium
from folium import plugins


class VisualizadorRutas:
    """
    Clase para visualizar rutas optimizadas en mapas
    """
    
    def __init__(self, df_ruta: pd.DataFrame):
        """
        Inicializa el visualizador con datos de ruta
        
        Parámetros
        ----------
        df_ruta : pd.DataFrame
            DataFrame con la ruta optimizada (debe tener lat, lon, nombre, orden)
        """
        self.df_ruta = df_ruta
        
    def crear_mapa_interactivo(self, 
                               output_path: str = "mapa_ruta.html",
                               zoom_inicio: int = 13) -> folium.Map:
        """
        Crea un mapa interactivo con la ruta optimizada
        
        Parámetros
        ----------
        output_path : str
            Ruta donde guardar el mapa HTML
        zoom_inicio : int
            Nivel de zoom inicial
            
        Retorna
        -------
        folium.Map
            Mapa de Folium
        """
        # Centro del mapa (promedio de coordenadas)
        centro_lat = self.df_ruta['lat'].mean()
        centro_lon = self.df_ruta['lon'].mean()
        
        # Crear mapa base
        mapa = folium.Map(
            location=[centro_lat, centro_lon],
            zoom_start=zoom_inicio,
            tiles='OpenStreetMap'
        )
        
        # Colores para diferentes tipos de puntos
        color_depot = 'red'
        color_entrega = 'blue'
        
        # Agregar marcadores
        for idx, row in self.df_ruta.iterrows():
            es_depot = idx == 0 or idx == len(self.df_ruta) - 1
            
            # Ícono y color según tipo
            if es_depot:
                icon = folium.Icon(color=color_depot, icon='home', prefix='fa')
                popup_text = f"<b>DEPOT</b><br>{row['nombre']}"
            else:
                icon = folium.Icon(color=color_entrega, icon='box', prefix='fa')
                popup_text = f"<b>Parada {row['orden']}</b><br>{row['nombre']}<br>"
                popup_text += f"Dist. acumulada: {row['distancia_acumulada_km']:.2f} km"
            
            # Agregar marcador
            folium.Marker(
                location=[row['lat'], row['lon']],
                popup=folium.Popup(popup_text, max_width=250),
                tooltip=row['nombre'],
                icon=icon
            ).add_to(mapa)
            
            # Agregar número de orden
            if not es_depot:
                folium.Marker(
                    location=[row['lat'], row['lon']],
                    icon=folium.DivIcon(
                        html=f'<div style="font-size: 12pt; color: white; background-color: {color_entrega}; '
                             f'border-radius: 50%; width: 25px; height: 25px; text-align: center; '
                             f'line-height: 25px; font-weight: bold;">{row["orden"]}</div>'
                    )
                ).add_to(mapa)
        
        # Dibujar líneas de ruta
        coordenadas = self.df_ruta[['lat', 'lon']].values.tolist()
        
        folium.PolyLine(
            coordenadas,
            color='darkblue',
            weight=3,
            opacity=0.7,
            popup='Ruta óptima'
        ).add_to(mapa)
        
        # Agregar plugin de medición
        plugins.MeasureControl(position='topleft', primary_length_unit='kilometers').add_to(mapa)
        
        # Agregar controles de capa
        folium.LayerControl().add_to(mapa)
        
        # Guardar mapa
        mapa.save(output_path)
        print(f"🗺️  Mapa interactivo guardado en: {output_path}")
        
        return mapa
    
    def graficar_distancias_tramos(self, output_path: str = "distancias_tramos.png"):
        """
        Genera gráfico de barras con distancias por tramo
        
        Parámetros
        ----------
        output_path : str
            Ruta donde guardar el gráfico
        """
        # Filtrar solo paradas con siguiente tramo
        df_tramos = self.df_ruta[self.df_ruta['distancia_siguiente_km'] > 0].copy()
        
        if len(df_tramos) == 0:
            print("⚠️  No hay tramos para graficar")
            return
        
        # Crear gráfico
        fig, ax = plt.subplots(figsize=(14, 6))
        
        # Crear etiquetas cortas
        etiquetas = [f"{i+1}" for i in range(len(df_tramos))]
        
        # Gráfico de barras
        bars = ax.bar(
            etiquetas,
            df_tramos['distancia_siguiente_km'],
            color='steelblue',
            edgecolor='navy',
            alpha=0.7
        )
        
        # Línea de promedio
        promedio = df_tramos['distancia_siguiente_km'].mean()
        ax.axhline(
            y=promedio, 
            color='red', 
            linestyle='--', 
            linewidth=2,
            label=f'Promedio: {promedio:.2f} km'
        )
        
        # Configuración del gráfico
        ax.set_xlabel('Tramo (Parada → Siguiente)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Distancia (km)', fontsize=12, fontweight='bold')
        ax.set_title('Distancias entre Paradas de la Ruta Optimizada', 
                    fontsize=14, fontweight='bold', pad=20)
        ax.legend(fontsize=10)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        
        # Rotar etiquetas si hay muchas
        if len(df_tramos) > 15:
            plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"📊 Gráfico de distancias guardado en: {output_path}")
        plt.close()
    
    def graficar_distancia_acumulada(self, output_path: str = "distancia_acumulada.png"):
        """
        Genera gráfico de línea con distancia acumulada
        
        Parámetros
        ----------
        output_path : str
            Ruta donde guardar el gráfico
        """
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Gráfico de línea
        ax.plot(
            self.df_ruta['orden'],
            self.df_ruta['distancia_acumulada_km'],
            marker='o',
            linewidth=2,
            markersize=6,
            color='darkgreen',
            markerfacecolor='lightgreen',
            markeredgecolor='darkgreen',
            markeredgewidth=2
        )
        
        # Rellenar área bajo la curva
        ax.fill_between(
            self.df_ruta['orden'],
            self.df_ruta['distancia_acumulada_km'],
            alpha=0.3,
            color='lightgreen'
        )
        
        # Configuración
        ax.set_xlabel('Número de Parada', fontsize=12, fontweight='bold')
        ax.set_ylabel('Distancia Acumulada (km)', fontsize=12, fontweight='bold')
        ax.set_title('Distancia Acumulada a lo Largo de la Ruta', 
                    fontsize=14, fontweight='bold', pad=20)
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # Agregar anotación del total
        total = self.df_ruta['distancia_acumulada_km'].iloc[-1]
        ax.annotate(
            f'Total: {total:.2f} km',
            xy=(self.df_ruta['orden'].iloc[-1], total),
            xytext=(10, -20),
            textcoords='offset points',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7),
            arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0', color='red')
        )
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"📊 Gráfico de distancia acumulada guardado en: {output_path}")
        plt.close()
    
    def crear_dashboard_completo(self, output_folder: str = "visualizaciones"):
        """
        Crea un conjunto completo de visualizaciones
        
        Parámetros
        ----------
        output_folder : str
            Carpeta donde guardar todas las visualizaciones
        """
        import os
        
        # Crear carpeta si no existe
        os.makedirs(output_folder, exist_ok=True)
        
        print("\n🎨 Generando visualizaciones...")
        print("-"*70)
        
        # Mapa interactivo
        self.crear_mapa_interactivo(
            output_path=f"{output_folder}/mapa_ruta.html"
        )
        
        # Gráfico de distancias por tramo
        self.graficar_distancias_tramos(
            output_path=f"{output_folder}/distancias_tramos.png"
        )
        
        # Gráfico de distancia acumulada
        self.graficar_distancia_acumulada(
            output_path=f"{output_folder}/distancia_acumulada.png"
        )
        
        print("-"*70)
        print(f"✅ Todas las visualizaciones guardadas en: {output_folder}/\n")


def visualizar_comparacion_rutas(ruta_original: pd.DataFrame,
                                 ruta_optimizada: pd.DataFrame,
                                 output_path: str = "comparacion_rutas.png"):
    """
    Compara visualmente dos rutas (original vs optimizada)
    
    Parámetros
    ----------
    ruta_original : pd.DataFrame
        Ruta sin optimizar
    ruta_optimizada : pd.DataFrame
        Ruta optimizada
    output_path : str
        Ruta donde guardar el gráfico
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Ruta original
    ax1.plot(
        ruta_original['orden'],
        ruta_original['distancia_acumulada_km'],
        marker='o',
        linewidth=2,
        color='red',
        label='Ruta Original'
    )
    ax1.fill_between(
        ruta_original['orden'],
        ruta_original['distancia_acumulada_km'],
        alpha=0.3,
        color='red'
    )
    ax1.set_title('Ruta Sin Optimizar', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Parada', fontsize=12)
    ax1.set_ylabel('Distancia Acumulada (km)', fontsize=12)
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Ruta optimizada
    ax2.plot(
        ruta_optimizada['orden'],
        ruta_optimizada['distancia_acumulada_km'],
        marker='o',
        linewidth=2,
        color='green',
        label='Ruta Optimizada'
    )
    ax2.fill_between(
        ruta_optimizada['orden'],
        ruta_optimizada['distancia_acumulada_km'],
        alpha=0.3,
        color='green'
    )
    ax2.set_title('Ruta Optimizada', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Parada', fontsize=12)
    ax2.set_ylabel('Distancia Acumulada (km)', fontsize=12)
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    # Calcular ahorro
    dist_original = ruta_original['distancia_acumulada_km'].iloc[-1]
    dist_optimizada = ruta_optimizada['distancia_acumulada_km'].iloc[-1]
    ahorro = dist_original - dist_optimizada
    ahorro_pct = (ahorro / dist_original) * 100
    
    # Título general con métricas
    fig.suptitle(
        f'Comparación de Rutas | Ahorro: {ahorro:.2f} km ({ahorro_pct:.1f}%)',
        fontsize=16,
        fontweight='bold',
        y=0.98
    )
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"📊 Comparación guardada en: {output_path}")
    plt.close()

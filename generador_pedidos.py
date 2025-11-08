"""
Módulo para generar pedidos aleatorios dentro de comunas de CABA
"""

import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point
import random
from typing import Tuple, List


# Datos de centros de distribución Andreani
ANDREANI_DATA = [
    {"Andreani": "Barracas", "comuna": 4, "lat": -34.646764, "lon": -58.378025},
    {"Andreani": "Monserrat", "comuna": 1, "lat": -34.613193, "lon": -58.383455},
    {"Andreani": "Retiro", "comuna": 1, "lat": -34.603277, "lon": -58.373207},
    {"Andreani": "Recoleta", "comuna": 2, "lat": -34.602725, "lon": -58.385984},
    {"Andreani": "Balvanera", "comuna": 3, "lat": -34.608869, "lon": -58.406404},
    {"Andreani": "Almagro", "comuna": 5, "lat": -34.608671, "lon": -58.425996},
    {"Andreani": "Villa Crespo", "comuna": 15, "lat": -34.597650, "lon": -58.435302},
    {"Andreani": "Flores", "comuna": 7, "lat": -34.634331, "lon": -58.471665},
    {"Andreani": "Liniers", "comuna": 9, "lat": -34.638290, "lon": -58.505790},
    {"Andreani": "Villa Devoto", "comuna": 11, "lat": -34.609255, "lon": -58.517293},
    {"Andreani": "Villa Urquiza", "comuna": 12, "lat": -34.575654, "lon": -58.477644},
    {"Andreani": "Belgrano", "comuna": 13, "lat": -34.567591, "lon": -58.449757},
]


def obtener_depot_por_comuna(comuna_id: int) -> dict:
    """
    Obtiene el centro de distribución Andreani correspondiente a una comuna
    
    Parámetros
    ----------
    comuna_id : int
        ID de la comuna (1-15)
        
    Retorna
    -------
    dict
        Información del depot con lat, lon, nombre
    """
    # Buscar depot en la comuna
    for depot in ANDREANI_DATA:
        if depot.get('comuna') == comuna_id:
            return depot
    
    # Si no hay depot específico, usar el más cercano
    print(f"⚠️  No hay depot específico para comuna {comuna_id}, usando el más cercano")
    return ANDREANI_DATA[0]  # Por default usar Barracas


def generar_puntos_comuna(gdf_comuna: gpd.GeoDataFrame, 
                          min_n: int = 9,
                          max_n: int = 30,
                          seed: int = None) -> gpd.GeoDataFrame:
    """
    Genera puntos aleatorios dentro de una o más comunas
    
    Parámetros
    ----------
    gdf_comuna : gpd.GeoDataFrame
        GeoDataFrame con el/los polígono(s) de la(s) comuna(s)
    min_n : int
        Número mínimo de puntos a generar
    max_n : int
        Número máximo de puntos a generar
    seed : int, opcional
        Semilla para reproducibilidad
        
    Retorna
    -------
    gpd.GeoDataFrame
        GeoDataFrame con los puntos generados
    """
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)
    
    # Número aleatorio de pedidos
    n_pedidos = random.randint(min_n, max_n)
    
    # Unir todas las geometrías si hay múltiples
    union_geometry = gdf_comuna.unary_union
    bounds = union_geometry.bounds  # (minx, miny, maxx, maxy)
    
    puntos = []
    intentos_max = n_pedidos * 100  # Para evitar loop infinito
    intentos = 0
    
    while len(puntos) < n_pedidos and intentos < intentos_max:
        # Generar punto aleatorio dentro del bounding box
        lon = random.uniform(bounds[0], bounds[2])
        lat = random.uniform(bounds[1], bounds[3])
        punto = Point(lon, lat)
        
        # Verificar si está dentro de la comuna
        if union_geometry.contains(punto):
            puntos.append(punto)
        
        intentos += 1
    
    if len(puntos) < n_pedidos:
        print(f"⚠️  Solo se pudieron generar {len(puntos)} de {n_pedidos} puntos")
    
    # Crear GeoDataFrame
    gdf_puntos = gpd.GeoDataFrame(
        {'geometry': puntos},
        crs=gdf_comuna.crs
    )
    
    return gdf_puntos


def generar_puntos_caba(gdf_caba: gpd.GeoDataFrame,
                        min_n: int = 9,
                        max_n: int = 30,
                        seed: int = None) -> gpd.GeoDataFrame:
    """
    Genera puntos aleatorios en toda CABA
    
    Parámetros
    ----------
    gdf_caba : gpd.GeoDataFrame
        GeoDataFrame con el polígono de CABA
    min_n : int
        Número mínimo de puntos
    max_n : int
        Número máximo de puntos
    seed : int, opcional
        Semilla para reproducibilidad
        
    Retorna
    -------
    gpd.GeoDataFrame
        GeoDataFrame con los puntos
    """
    return generar_puntos_comuna(gdf_caba, min_n, max_n, seed)


def generar_pedidos_csv(comuna_id: int,
                        gdf_comunas: gpd.GeoDataFrame,
                        n_pedidos: int = None,
                        min_pedidos: int = 9,
                        max_pedidos: int = 30,
                        output_path: str = "pedidos.csv",
                        seed: int = None) -> pd.DataFrame:
    """
    Genera un CSV con pedidos aleatorios para una comuna específica
    
    Parámetros
    ----------
    comuna_id : int
        ID de la comuna (1-15)
    gdf_comunas : gpd.GeoDataFrame
        GeoDataFrame con todas las comunas (debe tener columna 'COMUNAS')
    n_pedidos : int, opcional
        Número exacto de pedidos. Si no se especifica, usa random entre min y max
    min_pedidos : int
        Mínimo de pedidos si n_pedidos es None
    max_pedidos : int
        Máximo de pedidos si n_pedidos es None
    output_path : str
        Ruta donde guardar el CSV
    seed : int, opcional
        Semilla para reproducibilidad
        
    Retorna
    -------
    pd.DataFrame
        DataFrame con los pedidos generados
    """
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)
    
    # Filtrar la comuna específica
    comuna = gdf_comunas[gdf_comunas['COMUNAS'] == comuna_id]
    
    if len(comuna) == 0:
        raise ValueError(f"No se encontró la comuna {comuna_id}")
    
    # Determinar número de pedidos
    if n_pedidos is None:
        n_pedidos = random.randint(min_pedidos, max_pedidos)
    
    print(f"🎲 Generando {n_pedidos} pedidos para Comuna {comuna_id}...")
    
    # Generar puntos
    puntos_gdf = generar_puntos_comuna(
        comuna, 
        min_n=n_pedidos, 
        max_n=n_pedidos,
        seed=seed
    )
    
    # Crear DataFrame
    df_pedidos = pd.DataFrame({
        'pedido': [f"pedido_{i+1:03d}" for i in range(len(puntos_gdf))],
        'lat': [p.y for p in puntos_gdf.geometry],
        'lon': [p.x for p in puntos_gdf.geometry],
        'comuna': comuna_id
    })
    
    # Guardar CSV
    df_pedidos.to_csv(output_path, index=False)
    print(f"✅ Pedidos guardados en: {output_path}")
    
    return df_pedidos


def crear_dataset_completo(comuna_id: int,
                          gdf_comunas: gpd.GeoDataFrame,
                          n_pedidos: int = None,
                          min_pedidos: int = 9,
                          max_pedidos: int = 30,
                          seed: int = None) -> Tuple[pd.DataFrame, dict]:
    """
    Crea dataset completo con depot y pedidos para optimización
    
    Parámetros
    ----------
    comuna_id : int
        ID de la comuna
    gdf_comunas : gpd.GeoDataFrame
        GeoDataFrame con comunas
    n_pedidos : int, opcional
        Número exacto de pedidos
    min_pedidos : int
        Mínimo de pedidos
    max_pedidos : int
        Máximo de pedidos
    seed : int, opcional
        Semilla para reproducibilidad
        
    Retorna
    -------
    df_completo : pd.DataFrame
        DataFrame con depot (primera fila) y pedidos
    info : dict
        Información sobre el dataset
    """
    # Obtener depot de la comuna
    depot = obtener_depot_por_comuna(comuna_id)
    
    # Generar pedidos
    df_pedidos = generar_pedidos_csv(
        comuna_id=comuna_id,
        gdf_comunas=gdf_comunas,
        n_pedidos=n_pedidos,
        min_pedidos=min_pedidos,
        max_pedidos=max_pedidos,
        output_path=f"pedidos_comuna_{comuna_id}.csv",
        seed=seed
    )
    
    # Crear DataFrame del depot
    df_depot = pd.DataFrame({
        'pedido': [f"DEPOT_{depot['Andreani']}"],
        'lat': [depot['lat']],
        'lon': [depot['lon']],
        'comuna': [comuna_id]
    })
    
    # Concatenar depot + pedidos
    df_completo = pd.concat([df_depot, df_pedidos], ignore_index=True)
    
    info = {
        'comuna_id': comuna_id,
        'depot_nombre': depot['Andreani'],
        'depot_coords': (depot['lat'], depot['lon']),
        'n_pedidos': len(df_pedidos),
        'n_puntos_total': len(df_completo)
    }
    
    print(f"\n📊 Dataset creado:")
    print(f"   Comuna: {comuna_id}")
    print(f"   Depot: {depot['Andreani']}")
    print(f"   Pedidos: {len(df_pedidos)}")
    print(f"   Total de puntos: {len(df_completo)}\n")
    
    return df_completo, info


def listar_comunas_disponibles():
    """Imprime lista de comunas con depots disponibles"""
    print("\n" + "="*60)
    print("📍 CENTROS DE DISTRIBUCIÓN ANDREANI POR COMUNA")
    print("="*60)
    
    for depot in ANDREANI_DATA:
        comuna = depot.get('comuna', 'N/A')
        print(f"  Comuna {comuna:2d} - {depot['Andreani']:<20s} ({depot['lat']:.4f}, {depot['lon']:.4f})")
    
    print("="*60 + "\n")

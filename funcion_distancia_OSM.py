import osmnx as ox
import networkx as nx
from shapely.geometry import Point

def calcular_distancia(A, B, radio_m=20000):
    """
    Calcula la distancia mínima de manejo (en km) entre dos puntos geográficos
    usando la red vial de OpenStreetMap.

    Parámetros
    ----------
    A : tuple(float, float)
        (latitud, longitud) del origen.
    B : tuple(float, float)
        (latitud, longitud) del destino.
    radio_m : int
        Radio (en metros) para descargar la red vial alrededor del centro entre A y B.
        Debe ser suficientemente grande para que A y B queden dentro del grafo.

    Retorna
    -------
    dist_km : float
        Distancia de la ruta más corta en km sobre la red de calles transitable en auto.
    """

    # 1. Parseo de coordenadas
    latA, lonA = A
    latB, lonB = B

    # 2. Centro aproximado entre A y B para bajar UNA sola red OSM
    latC = (latA + latB) / 2.0
    lonC = (lonA + lonB) / 2.0

    # 3. Descargamos la red vial "drive" alrededor del punto medio
    #    - network_type="drive" filtra calles transitables en vehículo
    #    - retain_all=True evita que se descarten componentes chicas
    G = ox.graph_from_point(
        center_point=(latC, lonC),
        dist=radio_m,
        network_type="drive",
        simplify=True,
        retain_all=True
    )

    # 4. Encontrar el nodo de la red más cercano a cada punto
    nodo_A = ox.distance.nearest_nodes(G, lonA, latA)
    nodo_B = ox.distance.nearest_nodes(G, lonB, latB)

    # 5. Calcular la distancia más corta en metros usando el atributo 'length'
    try:
        dist_m = nx.shortest_path_length(G, nodo_A, nodo_B, weight="length")
    except nx.NetworkXNoPath:
        raise ValueError("No hay camino en la red vial entre A y B con el radio dado.")

    # 6. Pasar a km
    dist_km = dist_m / 1000.0
    return dist_km

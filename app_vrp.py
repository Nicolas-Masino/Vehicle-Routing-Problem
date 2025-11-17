"""
Aplicación Streamlit para Optimización de Rutas de Vehículos (VRP)
MVP para optimización de rutas usando OR-Tools y visualización con Folium
"""

import streamlit as st
import pandas as pd
import numpy as np
import geopandas as gpd
from shapely import wkt
from shapely.geometry import Point
import requests
import polyline
import folium
from streamlit_folium import st_folium
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import os
import time
from analisis_sensibilidad import AnalizadorSensibilidad

# ============================================================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================================================

st.set_page_config(
    page_title="Optimizador de Rutas VRP",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# FUNCIONES AUXILIARES - CARGA DE DATOS
# ============================================================================

@st.cache_data
def cargar_barrios_caba():
    """Carga el polígono de barrios de CABA desde CSV"""
    try:
        # Intentar con ruta relativa
        barrios_path = 'utils/barrios copy.csv'
        if not os.path.exists(barrios_path):
            barrios_path = 'barrios copy.csv'

        barrios_df = pd.read_csv(barrios_path, encoding='latin-1')
        barrios_df['geometry'] = barrios_df['WKT'].apply(wkt.loads)
        barrios_gdf = gpd.GeoDataFrame(barrios_df, geometry='geometry', crs='EPSG:4326')
        caba_polygon = barrios_gdf.unary_union

        return barrios_gdf, caba_polygon
    except Exception as e:
        st.error(f"Error cargando archivo de barrios: {e}")
        return None, None

# ============================================================================
# FUNCIONES AUXILIARES - GENERACIÓN DE PEDIDOS
# ============================================================================

def generate_random_deliveries_in_caba(caba_polygon, num_orders, seed=None):
    """
    Genera pedidos con coordenadas aleatorias DENTRO del polígono de CABA

    Args:
        caba_polygon: Polígono de CABA (shapely Polygon o MultiPolygon)
        num_orders: cantidad de pedidos
        seed: semilla para reproducibilidad

    Returns:
        orders: lista de ubicaciones dentro de CABA
    """
    if seed is not None:
        np.random.seed(seed)

    orders = []
    minx, miny, maxx, maxy = caba_polygon.bounds

    attempts = 0
    max_attempts = num_orders * 100

    while len(orders) < num_orders and attempts < max_attempts:
        random_lon = np.random.uniform(minx, maxx)
        random_lat = np.random.uniform(miny, maxy)
        point = Point(random_lon, random_lat)

        if caba_polygon.contains(point):
            order = {
                'order_id': len(orders) + 1,
                'lat': random_lat,
                'lon': random_lon,
                'type': 'order'
            }
            orders.append(order)

        attempts += 1

    if len(orders) < num_orders:
        st.warning(f"Solo se generaron {len(orders)}/{num_orders} pedidos dentro de CABA")

    return orders

# ============================================================================
# FUNCIONES AUXILIARES - OSRM Y DISTANCIAS
# ============================================================================

def calculate_euclidean_distances(locations):
    """Distancia euclidiana como fallback"""
    n = len(locations)
    distance_matrix = np.zeros((n, n))

    for i in range(n):
        for j in range(n):
            lat1, lon1 = locations[i]['lat'], locations[i]['lon']
            lat2, lon2 = locations[j]['lat'], locations[j]['lon']
            distance_matrix[i][j] = np.sqrt(
                ((lat2 - lat1) * 111000)**2 +
                ((lon2 - lon1) * 111000 * np.cos(np.radians(lat1)))**2
            )

    return distance_matrix

def calculate_distance_matrix_osrm(locations, use_cache=True, cache_name='distances'):
    """
    Calcula matriz de distancias usando OSRM API

    Args:
        locations: lista de diccionarios con 'lat' y 'lon'
        use_cache: si usar cache de archivo
        cache_name: nombre base del archivo de cache

    Returns:
        distance_matrix: matriz de distancias en metros
    """
    n = len(locations)
    distance_matrix = np.zeros((n, n))

    cache_file = f'{cache_name}_{n}.npz'

    if use_cache:
        try:
            cache = np.load(cache_file)
            return cache['distance']
        except:
            pass

    coords = ";".join([f"{loc['lon']},{loc['lat']}" for loc in locations])
    url = f"http://router.project-osrm.org/table/v1/driving/{coords}?annotations=distance"

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()

        if data['code'] == 'Ok':
            distance_matrix = np.array(data['distances'])

            if use_cache:
                np.savez(cache_file, distance=distance_matrix)
        else:
            st.warning("Error en OSRM, usando distancia euclidiana")
            distance_matrix = calculate_euclidean_distances(locations)

    except Exception as e:
        st.warning(f"Error conectando a OSRM: {e}. Usando distancias euclidianas")
        distance_matrix = calculate_euclidean_distances(locations)

    return distance_matrix.astype(int)

def get_osrm_route_geometry(locations_indices, all_locations):
    """
    Obtiene la geometría de la ruta real usando OSRM

    Args:
        locations_indices: lista de índices de ubicaciones en orden
        all_locations: lista completa de ubicaciones

    Returns:
        route_coords: lista de tuplas (lat, lon) de la ruta real
    """
    if len(locations_indices) < 2:
        return None

    coords = ";".join([f"{all_locations[i]['lon']},{all_locations[i]['lat']}"
                      for i in locations_indices])

    url = f"http://router.project-osrm.org/route/v1/driving/{coords}?overview=full&geometries=polyline"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data['code'] == 'Ok':
            encoded_polyline = data['routes'][0]['geometry']
            decoded = polyline.decode(encoded_polyline)
            # Retornar como lista de tuplas (lat, lon) para Folium
            return decoded
        else:
            return None

    except Exception as e:
        return None

# ============================================================================
# FUNCIÓN DE OPTIMIZACIÓN - OR-TOOLS
# ============================================================================

def optimizar_rutas_vrp(all_locations, num_vehicles, vehicle_capacity, distance_matrix, tiempo_limite_segundos=30):
    """
    Optimiza las rutas usando OR-Tools

    Args:
        all_locations: lista de ubicaciones [depot] + [orders]
        num_vehicles: número de camiones
        vehicle_capacity: capacidad de cada camión
        distance_matrix: matriz de distancias
        tiempo_limite_segundos: tiempo límite de optimización en segundos (default: 30)

    Returns:
        solution, routing, manager, data, all_routes
    """

    # Crear modelo de datos
    data = {}
    data['distance_matrix'] = distance_matrix.tolist()
    data['demands'] = [0] + [1] * (len(all_locations) - 1)  # Depot tiene demanda 0
    data['vehicle_capacities'] = [vehicle_capacity] * num_vehicles
    data['num_vehicles'] = num_vehicles
    data['depot'] = 0

    # Crear manager y routing model
    manager = pywrapcp.RoutingIndexManager(
        len(data['distance_matrix']),
        data['num_vehicles'],
        data['depot']
    )
    routing = pywrapcp.RoutingModel(manager)

    # Callback de distancia
    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['distance_matrix'][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Callback de demanda
    def demand_callback(from_index):
        from_node = manager.IndexToNode(from_index)
        return data['demands'][from_node]

    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)

    # Agregar restricción de capacidad
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,  # null capacity slack
        data['vehicle_capacities'],
        True,  # start cumul to zero
        'Capacity'
    )

    # Configurar parámetros de búsqueda
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    search_parameters.time_limit.seconds = tiempo_limite_segundos

    # Resolver
    solution = routing.SolveWithParameters(search_parameters)

    if not solution:
        return None, None, None, None, None

    # Extraer rutas de la solución
    all_routes = []

    for vehicle_id in range(data['num_vehicles']):
        index = routing.Start(vehicle_id)
        route_distance = 0
        route_load = 0
        route_nodes = []

        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            route_load += data['demands'][node_index]
            route_nodes.append(node_index)

            previous_index = index
            index = solution.Value(routing.NextVar(index))
            route_distance += routing.GetArcCostForVehicle(previous_index, index, vehicle_id)

        # Agregar regreso al depósito
        node_index = manager.IndexToNode(index)
        route_nodes.append(node_index)

        all_routes.append({
            'vehicle': vehicle_id + 1,
            'distance': route_distance,
            'packages': route_load,
            'nodes': route_nodes
        })

    return solution, routing, manager, data, all_routes

# ============================================================================
# FUNCIÓN DE VISUALIZACIÓN - FOLIUM
# ============================================================================

def crear_mapa_folium(all_locations, all_routes, barrios_gdf, selected_vehicle=None):
    """
    Crea mapa de Folium con las rutas

    Args:
        all_locations: lista de ubicaciones
        all_routes: rutas calculadas
        barrios_gdf: GeoDataFrame de barrios
        selected_vehicle: None para mostrar todos, o número de vehículo específico

    Returns:
        mapa de Folium
    """

    # Obtener centro (depósito)
    depot = all_locations[0]
    centro = [depot['lat'], depot['lon']]

    # Crear mapa base
    mapa = folium.Map(
        location=centro,
        zoom_start=12,
        tiles='OpenStreetMap'
    )

    # Colores para rutas
    colors = ['green', 'orange', 'purple', 'brown', 'pink', 'cyan']

    # Agregar polígonos de barrios (fondo)
    if barrios_gdf is not None:
        folium.GeoJson(
            barrios_gdf,
            style_function=lambda x: {
                'fillColor': 'lightgray',
                'color': 'gray',
                'weight': 0.5,
                'fillOpacity': 0.2
            }
        ).add_to(mapa)

    # Agregar depósito
    folium.Marker(
        location=[depot['lat'], depot['lon']],
        popup=f"<b>{depot.get('name', 'Depósito')}</b>",
        icon=folium.Icon(color='red', icon='home', prefix='fa'),
        tooltip="Depósito"
    ).add_to(mapa)

    # Determinar qué rutas mostrar
    if selected_vehicle is not None:
        routes_to_show = [r for r in all_routes if r['vehicle'] == selected_vehicle and r['packages'] > 0]
    else:
        routes_to_show = [r for r in all_routes if r['packages'] > 0]

    # Agregar rutas
    for route_info in routes_to_show:
        vehicle_id = route_info['vehicle'] - 1
        route_nodes = route_info['nodes']
        color = colors[vehicle_id % len(colors)]

        # Solo mostrar rutas con al menos depot -> entrega -> depot (mínimo 3 nodos)
        if len(route_nodes) > 2:
            # Obtener geometría real de OSRM
            route_geometry = get_osrm_route_geometry(route_nodes, all_locations)

            if route_geometry:
                # Ruta real de OSRM
                folium.PolyLine(
                    locations=route_geometry,
                    color=color,
                    weight=3,
                    opacity=0.7,
                    popup=f"Camión {route_info['vehicle']}"
                ).add_to(mapa)
            else:
                # Fallback a líneas rectas
                route_coords = [[all_locations[i]['lat'], all_locations[i]['lon']]
                               for i in route_nodes]
                folium.PolyLine(
                    locations=route_coords,
                    color=color,
                    weight=3,
                    opacity=0.7,
                    popup=f"Camión {route_info['vehicle']}"
                ).add_to(mapa)

            # Agregar marcadores de entregas en esta ruta
            for idx, node_idx in enumerate(route_nodes):
                if node_idx != 0:  # Excluir depósito
                    loc = all_locations[node_idx]
                    order_id = loc.get('order_id', node_idx)

                    folium.CircleMarker(
                        location=[loc['lat'], loc['lon']],
                        radius=6,
                        color='black',
                        fillColor=color,
                        fillOpacity=0.8,
                        weight=1,
                        popup=f"Pedido #{order_id}<br>Camión {route_info['vehicle']}<br>Paso {idx}",
                        tooltip=f"Pedido #{order_id}"
                    ).add_to(mapa)

    return mapa

# ============================================================================
# INTERFAZ PRINCIPAL
# ============================================================================

def main():
    # Logo
    try:
        logo_path = 'logo.png'
        if os.path.exists(logo_path):
            st.image(logo_path, width=300)
        else:
            # Intentar con ruta alternativa
            logo_path = 'utils/logo.png'
            if os.path.exists(logo_path):
                st.image(logo_path, width=300)
    except:
        pass  # Si no hay logo, continuar sin él

    st.title("Optimizador de Rutas de Vehículos (VRP)")
    st.markdown("---")

    # Cargar barrios
    barrios_gdf, caba_polygon = cargar_barrios_caba()

    if barrios_gdf is None:
        st.error("No se pudo cargar el archivo de barrios. Verifica que exista 'utils/barrios copy.csv'")
        return

    # ========================================================================
    # LAYOUT DE 3 COLUMNAS
    # ========================================================================

    col_left, col_center, col_right = st.columns([0.3, 0.45, 0.25])

    # ========================================================================
    # COLUMNA IZQUIERDA - CONFIGURACIÓN
    # ========================================================================

    with col_left:
        st.header("Configuración")

        # Coordenadas del depósito
        st.subheader("Depósito")

        # Ubicaciones predefinidas
        ubicaciones_predefinidas = {
            "Retiro": (-34.603277, -58.373207),
            "Palermo": (-34.577882, -58.420664),
            "Recoleta": (-34.588249, -58.396328),
            "San Telmo": (-34.621340, -58.372150),
            "Belgrano": (-34.562991, -58.457417)
        }

        ubicacion_seleccionada = st.selectbox(
            "Ubicación predefinida:",
            options=["Personalizada"] + list(ubicaciones_predefinidas.keys())
        )

        if ubicacion_seleccionada == "Personalizada":
            depot_lat = st.number_input("Latitud", value=-34.603277, format="%.6f")
            depot_lon = st.number_input("Longitud", value=-58.373207, format="%.6f")
        else:
            depot_lat, depot_lon = ubicaciones_predefinidas[ubicacion_seleccionada]
            st.info(f"Lat: {depot_lat:.6f}, Lon: {depot_lon:.6f}")

        # Validar coordenadas
        if not (-90 <= depot_lat <= 90) or not (-180 <= depot_lon <= 180):
            st.error("Coordenadas inválidas")
            return

        st.markdown("---")

        # Configuración de flota
        st.subheader("Configuración de Flota")

        num_vehicles = st.slider("Cantidad de Camiones", min_value=1, max_value=5, value=3)
        vehicle_capacity = st.slider("Capacidad por Camión", min_value=5, max_value=15, value=15)

        st.markdown("---")

        # Parámetros económicos
        st.subheader("Parámetros Económicos")

        col_precio1, col_precio2 = st.columns(2)

        with col_precio1:
            precio_nafta = st.number_input(
                "Precio Nafta ($/L)",
                min_value=0.0,
                value=1000.0,
                step=50.0,
                format="%.2f",
                help="Precio del litro de nafta en pesos"
            )

            rendimiento_vehiculo = st.number_input(
                "Rendimiento (km/L)",
                min_value=0.1,
                value=10.0,
                step=0.5,
                format="%.2f",
                help="Kilómetros que recorre el vehículo por litro de nafta"
            )

            velocidad_promedio_kmh = st.number_input(
                "Velocidad Promedio (km/h)",
                min_value=1.0,
                value=30.0,
                step=5.0,
                format="%.1f",
                help="Velocidad promedio del vehículo en la ciudad"
            )

        with col_precio2:
            precio_base_por_pedido = st.number_input(
                "Precio Base ($/pedido)",
                min_value=0.0,
                value=2000.0,
                step=100.0,
                format="%.2f",
                help="Precio base cobrado por cada pedido entregado"
            )

            precio_por_km = st.number_input(
                "Precio por km ($/km)",
                min_value=0.0,
                value=150.0,
                step=10.0,
                format="%.2f",
                help="Precio variable cobrado por kilómetro recorrido"
            )

            costo_chofer_por_hora = st.number_input(
                "Costo Chofer ($/h)",
                min_value=0.0,
                value=2000.0,
                step=100.0,
                format="%.2f",
                help="Costo por hora del chofer/conductor"
            )

        st.markdown("---")

        # Ingreso de pedidos
        st.subheader("Ingrese sus pedidos")

        # Tabs para diferentes métodos de carga
        tab_csv, tab_aleatorio = st.tabs(["Subir CSV", "Generar Aleatorio"])

        orders = []

        with tab_csv:
            uploaded_file = st.file_uploader("Subir archivo CSV", type=['csv'])

            if uploaded_file is not None:
                try:
                    df_pedidos = pd.read_csv(uploaded_file)

                    # Validar columnas
                    if 'lat' not in df_pedidos.columns or 'lon' not in df_pedidos.columns:
                        st.error("El CSV debe tener columnas 'lat' y 'lon'")
                    else:
                        # Validar rangos
                        if not df_pedidos['lat'].between(-90, 90).all():
                            st.error("Latitudes fuera de rango (-90, 90)")
                        elif not df_pedidos['lon'].between(-180, 180).all():
                            st.error("Longitudes fuera de rango (-180, 180)")
                        else:
                            # Preview
                            st.write("Preview:")
                            st.dataframe(df_pedidos.head(), use_container_width=True)

                            # Crear lista de orders
                            for idx, row in df_pedidos.iterrows():
                                order_id = row.get('order_id', row.get('pedido_id', idx + 1))
                                orders.append({
                                    'order_id': order_id,
                                    'lat': row['lat'],
                                    'lon': row['lon'],
                                    'type': 'order'
                                })

                            st.success(f"{len(orders)} pedidos cargados")
                except Exception as e:
                    st.error(f"Error al leer CSV: {e}")

        with tab_aleatorio:
            num_pedidos_aleatorios = st.number_input(
                "Número de pedidos a generar",
                min_value=1,
                max_value=50,
                value=20
            )

            seed_aleatorio = st.number_input(
                "Semilla (para reproducibilidad)",
                min_value=0,
                value=42
            )

            if st.button("Generar Pedidos Aleatorios"):
                orders = generate_random_deliveries_in_caba(
                    caba_polygon,
                    num_pedidos_aleatorios,
                    seed=seed_aleatorio
                )
                st.session_state['generated_orders'] = orders
                st.success(f"{len(orders)} pedidos generados")

        # Si hay pedidos generados en session_state, usarlos
        if 'generated_orders' in st.session_state and not orders:
            orders = st.session_state['generated_orders']

        # Mostrar contador de pedidos
        if orders:
            st.info(f"**{len(orders)} pedidos cargados**")

            # Validar capacidad
            total_capacity = num_vehicles * vehicle_capacity
            if len(orders) > total_capacity:
                st.error(f"Total de pedidos ({len(orders)}) excede la capacidad total ({total_capacity})")
                st.stop()

        st.markdown("---")

        # Configuración de optimización
        st.subheader("Configuración de Optimización")

        tiempo_limite = st.slider(
            "Tiempo Límite de Optimización (segundos)",
            min_value=10,
            max_value=300,
            value=30,
            step=10,
            help="Tiempo máximo que el algoritmo buscará la solución óptima. Aumenta este valor si tienes muchos pedidos."
        )

        # Calcular número de pedidos actual
        num_pedidos_actual = len(orders) if orders else 0

        # Mensaje de recomendación dinámico
        if num_pedidos_actual > 30:
            st.warning(f"⚠️ Tienes {num_pedidos_actual} pedidos. Se recomienda usar al menos 60 segundos de tiempo límite para obtener mejores resultados.")
        elif num_pedidos_actual > 20:
            st.info(f"ℹ️ Tienes {num_pedidos_actual} pedidos. Con 30 segundos es suficiente, pero puedes aumentar el tiempo para buscar mejores soluciones.")

        st.markdown("---")

        # Botón de optimización
        optimizar_disabled = len(orders) == 0

        if st.button("Optimizar Rutas", disabled=optimizar_disabled, type="primary", use_container_width=True):
            # Crear ubicaciones
            DEPOT = {
                "name": f"{ubicacion_seleccionada}" if ubicacion_seleccionada != "Personalizada" else "Depósito",
                "lat": depot_lat,
                "lon": depot_lon
            }

            all_locations = [DEPOT] + orders

            # Calcular matriz de distancias
            with st.spinner("Calculando matriz de distancias..."):
                distance_matrix = calculate_distance_matrix_osrm(
                    all_locations,
                    use_cache=True,
                    cache_name='vrp_streamlit'
                )

            # Optimizar
            with st.spinner(f"Optimizando rutas... (máx. {tiempo_limite} segundos)"):
                start_time = time.time()
                solution, routing, manager, data, all_routes = optimizar_rutas_vrp(
                    all_locations,
                    num_vehicles,
                    vehicle_capacity,
                    distance_matrix,
                    tiempo_limite_segundos=tiempo_limite
                )
                elapsed_time = time.time() - start_time

            if solution is None:
                st.error("No se encontró solución óptima. Intenta con menos pedidos o más camiones.")
            else:
                # Guardar en session_state
                st.session_state['solution'] = solution
                st.session_state['routing'] = routing
                st.session_state['manager'] = manager
                st.session_state['data'] = data
                st.session_state['all_routes'] = all_routes
                st.session_state['all_locations'] = all_locations
                st.session_state['distance_matrix'] = distance_matrix
                st.session_state['optimization_time'] = elapsed_time

                # Guardar parámetros económicos
                st.session_state['precio_nafta'] = precio_nafta
                st.session_state['rendimiento_vehiculo'] = rendimiento_vehiculo
                st.session_state['precio_base_por_pedido'] = precio_base_por_pedido
                st.session_state['precio_por_km'] = precio_por_km
                st.session_state['costo_chofer_por_hora'] = costo_chofer_por_hora
                st.session_state['velocidad_promedio_kmh'] = velocidad_promedio_kmh

                st.success(f"Optimización completada en {elapsed_time:.2f} segundos")
                st.rerun()

    # ========================================================================
    # COLUMNA CENTRAL - MAPA
    # ========================================================================

    with col_center:
        st.header("Visualización de Rutas")

        # Verificar si hay solución
        if 'all_routes' in st.session_state and 'all_locations' in st.session_state:
            all_routes = st.session_state['all_routes']
            all_locations = st.session_state['all_locations']
            solution = st.session_state['solution']

            # Obtener camiones activos
            active_vehicles = [r['vehicle'] for r in all_routes if r['packages'] > 0]

            # Crear selector de vista (en lugar de tabs nativos para evitar conflictos)
            opciones_vista = [f"Camión {v}" for v in active_vehicles] + ["Vista General"]

            # Usar columns para el selector de vista
            col_sel, col_spacer = st.columns([3, 1])
            with col_sel:
                vista_seleccionada = st.selectbox(
                    "Seleccionar vista:",
                    options=opciones_vista,
                    key="vista_mapa"
                )

            # Determinar qué mapa mostrar según la selección
            if vista_seleccionada == "Vista General":
                selected_vehicle = None
                map_key = "mapa_general"
            else:
                # Extraer número de camión de "Camión X"
                vehicle_num = int(vista_seleccionada.split()[1])
                selected_vehicle = vehicle_num
                map_key = f"mapa_camion_{vehicle_num}"

            # Crear y mostrar SOLO el mapa seleccionado
            mapa = crear_mapa_folium(all_locations, all_routes, barrios_gdf, selected_vehicle=selected_vehicle)
            st_folium(mapa, width=900, height=800, key=map_key, returned_objects=[])

        else:
            # Mostrar mapa vacío centrado en CABA
            st.info("Configure los parámetros y presione 'Optimizar Rutas' para ver los resultados")

            mapa_inicial = folium.Map(
                location=[-34.603277, -58.373207],
                zoom_start=12,
                tiles='OpenStreetMap'
            )

            if barrios_gdf is not None:
                folium.GeoJson(
                    barrios_gdf,
                    style_function=lambda x: {
                        'fillColor': 'lightgray',
                        'color': 'gray',
                        'weight': 0.5,
                        'fillOpacity': 0.2
                    }
                ).add_to(mapa_inicial)

            st_folium(mapa_inicial, width=700, height=600, key="mapa_inicial", returned_objects=[])

        # ====================================================================
        # ANÁLISIS ECONÓMICO Y DE SENSIBILIDAD
        # ====================================================================

        required_keys = ['precio_nafta', 'rendimiento_vehiculo', 'precio_base_por_pedido', 'precio_por_km', 'costo_chofer_por_hora', 'velocidad_promedio_kmh']
        if 'all_routes' in st.session_state and all(k in st.session_state for k in required_keys):
            all_routes = st.session_state['all_routes']
            data = st.session_state['data']

            st.markdown("---")
            st.header("Análisis Económico")

            # Obtener parámetros económicos
            precio_nafta_sess = st.session_state['precio_nafta']
            rendimiento_sess = st.session_state['rendimiento_vehiculo']
            precio_base_sess = st.session_state['precio_base_por_pedido']
            precio_por_km_sess = st.session_state['precio_por_km']
            costo_chofer_sess = st.session_state['costo_chofer_por_hora']
            velocidad_sess = st.session_state['velocidad_promedio_kmh']

            # Calcular distancias y número de pedidos
            total_distance = sum(r['distance'] for r in all_routes)
            num_pedidos = sum(r['packages'] for r in all_routes)
            distancias_por_ruta = [r['distance'] / 1000 for r in all_routes]  # Convertir de metros a km
            distancia_total_km = total_distance / 1000

            # Crear analizador
            try:
                analizador = AnalizadorSensibilidad(
                    distancia_total_km=distancia_total_km,
                    num_rutas=len(all_routes),
                    num_pedidos=num_pedidos,
                    distancias_por_ruta=distancias_por_ruta,
                    precio_nafta=precio_nafta_sess,
                    rendimiento_vehiculo=rendimiento_sess,
                    precio_base_por_pedido=precio_base_sess,
                    precio_por_km=precio_por_km_sess,
                    costo_chofer_por_hora=costo_chofer_sess,
                    velocidad_promedio_kmh=velocidad_sess
                )

                # Obtener resultados
                costos = analizador.calcular_costos_operacion()
                ingresos = analizador.calcular_ingresos()
                margen = analizador.calcular_margen()

                # Mostrar métricas económicas en 4 columnas
                col_eco1, col_eco2, col_eco3, col_eco4 = st.columns(4)

                with col_eco1:
                    st.metric(
                        "💵 Costo Operativo",
                        f"${costos['costo_total']:,.2f}",
                        help=f"Nafta: ${costos['costo_total_nafta']:,.2f} + Chofer: ${costos['costo_total_chofer']:,.2f} ({costos['tiempo_total_horas']:.1f}h)"
                    )

                with col_eco2:
                    st.metric(
                        "💰 Ingreso Total",
                        f"${ingresos['ingreso_total']:,.2f}",
                        help=f"Base: ${ingresos['ingreso_base']:,.2f} + Variable: ${ingresos['ingreso_variable']:,.2f}"
                    )

                with col_eco3:
                    margen_delta = f"{margen['rentabilidad_porcentaje']:+.1f}%"
                    margen_color = "normal" if margen['margen_total'] >= 0 else "inverse"

                    st.metric(
                        "📊 Margen Neto",
                        f"${margen['margen_total']:,.2f}",
                        delta=margen_delta,
                        delta_color=margen_color
                    )

                with col_eco4:
                    st.metric(
                        "📈 Rentabilidad",
                        f"{margen['rentabilidad_porcentaje']:.1f}%"
                    )

                st.markdown("---")
                st.subheader("Análisis de Sensibilidad")

                # Mostrar tabla estilo LINGO
                tabla_lingo = analizador.generar_tabla_lingo()
                st.dataframe(tabla_lingo, use_container_width=True, hide_index=True)

                # Interpretaciones
                st.markdown("##### Interpretación")
                interpretaciones = analizador.obtener_interpretaciones()

                for interpretacion in interpretaciones:
                    # Determinar el tipo de mensaje según el contenido
                    if interpretacion.startswith("✓"):
                        st.success(interpretacion)
                    elif interpretacion.startswith("⚠"):
                        st.warning(interpretacion)
                    elif interpretacion.startswith("✗"):
                        st.error(interpretacion)
                    else:
                        st.info(interpretacion)

            except Exception as e:
                st.error(f"Error en análisis económico: {e}")

    # ========================================================================
    # COLUMNA DERECHA - ÓRDENES Y MÉTRICAS
    # ========================================================================

    with col_right:
        st.header("Orden de entregas")

        if 'all_routes' in st.session_state and 'all_locations' in st.session_state:
            all_routes = st.session_state['all_routes']
            all_locations = st.session_state['all_locations']
            data = st.session_state['data']

            # Selector de camión (sincronizado con vista de mapa si es posible)
            active_vehicles = [r['vehicle'] for r in all_routes if r['packages'] > 0]

            # Intentar sincronizar con la vista del mapa si es un camión específico
            default_index = 0
            if 'vista_mapa' in st.session_state:
                vista_actual = st.session_state['vista_mapa']
                if vista_actual != "Vista General" and "Camión" in vista_actual:
                    vehicle_from_map = int(vista_actual.split()[1])
                    if vehicle_from_map in active_vehicles:
                        default_index = active_vehicles.index(vehicle_from_map)

            selected_truck = st.selectbox(
                "Ver detalles de:",
                options=active_vehicles,
                format_func=lambda x: f"Camión {x}",
                index=default_index,
                key="selected_truck_detail"
            )

            # Obtener ruta del camión seleccionado
            route_info = next(r for r in all_routes if r['vehicle'] == selected_truck)
            route_nodes = route_info['nodes']

            st.markdown("---")
            st.subheader(f"Ruta - Camión {selected_truck}")

            # Listar paradas
            for idx, node_idx in enumerate(route_nodes):
                loc = all_locations[node_idx]

                if node_idx == 0 and idx == 0:
                    # Salida del depósito
                    st.markdown(f"**{idx}.** 🏢 **Depósito**")
                    st.caption(f"Lat: {loc['lat']:.4f}, Lon: {loc['lon']:.4f}")
                elif node_idx == 0 and idx == len(route_nodes) - 1:
                    # Regreso al depósito
                    st.markdown(f"**{idx}.** 🔄 **Regreso al Depósito**")
                    st.caption(f"Lat: {loc['lat']:.4f}, Lon: {loc['lon']:.4f}")
                else:
                    # Pedido
                    order_id = loc.get('order_id', node_idx)
                    st.markdown(f"**{idx}.** 📦 Pedido #{order_id}")
                    st.caption(f"Lat: {loc['lat']:.4f}, Lon: {loc['lon']:.4f}")

            st.markdown("---")

            # Métricas de la ruta
            st.subheader("Métricas de la Ruta")

            col_m1, col_m2 = st.columns(2)

            with col_m1:
                st.metric(
                    "📏 Distancia",
                    f"{route_info['distance'] / 1000:.2f} km"
                )

            with col_m2:
                st.metric(
                    "📦 Paquetes",
                    f"{route_info['packages']}/{data['vehicle_capacities'][selected_truck - 1]}"
                )

            st.markdown("---")

            # Métricas generales
            st.subheader("Métricas Generales")

            total_distance = sum(r['distance'] for r in all_routes)
            total_packages = sum(r['packages'] for r in all_routes)
            active_trucks = len(active_vehicles)
            total_trucks = data['num_vehicles']
            utilization = (total_packages / (total_trucks * data['vehicle_capacities'][0])) * 100

            st.metric("🎯 Distancia Total", f"{total_distance / 1000:.2f} km")
            st.metric("📦 Total Paquetes", total_packages)
            st.metric("🚛 Camiones Utilizados", f"{active_trucks}/{total_trucks}")
            st.metric("📈 Utilización de Flota", f"{utilization:.1f}%")

            # Mostrar tiempo de optimización
            if 'optimization_time' in st.session_state:
                st.caption(f"⏱️ Tiempo de optimización: {st.session_state['optimization_time']:.2f}s")

        else:
            st.info("Ejecuta la optimización para ver las órdenes de entrega")

# ============================================================================
# EJECUTAR APLICACIÓN
# ============================================================================

if __name__ == "__main__":
    main()

"""
Módulo de optimización de rutas usando Google OR-Tools
Resuelve el Traveling Salesman Problem (TSP) para minimizar distancias de entrega
"""

from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import numpy as np
from typing import List, Tuple, Dict
import time


class OptimizadorRutas:
    """
    Clase para optimizar rutas de entrega usando el algoritmo TSP
    """
    
    def __init__(self, matriz_distancias: np.ndarray, nombres_puntos: List[str] = None):
        """
        Inicializa el optimizador con una matriz de distancias
        
        Parámetros
        ----------
        matriz_distancias : np.ndarray
            Matriz cuadrada NxN con distancias entre puntos (en km)
            matriz[i][j] = distancia del punto i al punto j
        nombres_puntos : List[str], opcional
            Lista con nombres de los puntos (para referencia)
        """
        self.matriz_distancias = matriz_distancias
        self.n_puntos = len(matriz_distancias)
        self.nombres_puntos = nombres_puntos or [f"Punto_{i}" for i in range(self.n_puntos)]
        self.ruta_optima = None
        self.distancia_total = None
        self.tiempo_solucion = None
        
    def _crear_modelo_datos(self) -> Dict:
        """Crea el diccionario de datos para OR-Tools"""
        # Convertir distancias a metros (enteros) para OR-Tools
        matriz_metros = (self.matriz_distancias * 1000).astype(int)
        
        data = {
            'distance_matrix': matriz_metros.tolist(),
            'num_vehicles': 1,  # Un solo camión
            'depot': 0  # El punto 0 es el centro de distribución (depot)
        }
        return data
    
    def resolver(self, tiempo_limite_segundos: int = 30) -> Tuple[List[int], float]:
        """
        Resuelve el problema TSP y encuentra la ruta óptima
        
        Parámetros
        ----------
        tiempo_limite_segundos : int
            Tiempo máximo de búsqueda en segundos
            
        Retorna
        -------
        ruta : List[int]
            Lista de índices representando el orden óptimo de visita
        distancia_total : float
            Distancia total de la ruta en km
        """
        print(f"🚛 Optimizando ruta para {self.n_puntos} puntos...")
        print(f"   Centro de distribución: {self.nombres_puntos[0]}")
        print(f"   Pedidos a entregar: {self.n_puntos - 1}")
        
        inicio = time.time()
        
        # Crear datos del modelo
        data = self._crear_modelo_datos()
        
        # Crear el routing index manager
        manager = pywrapcp.RoutingIndexManager(
            len(data['distance_matrix']),
            data['num_vehicles'],
            data['depot']
        )
        
        # Crear el modelo de routing
        routing = pywrapcp.RoutingModel(manager)
        
        # Crear y registrar la callback de distancia
        def distance_callback(from_index, to_index):
            """Retorna la distancia entre dos nodos"""
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return data['distance_matrix'][from_node][to_node]
        
        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        
        # Definir el costo de cada arco
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
        
        # Configurar parámetros de búsqueda
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        search_parameters.time_limit.seconds = tiempo_limite_segundos
        search_parameters.log_search = False
        
        # Resolver el problema
        solution = routing.SolveWithParameters(search_parameters)
        
        self.tiempo_solucion = time.time() - inicio
        
        if solution:
            # Extraer la ruta óptima
            self.ruta_optima = self._extraer_ruta(manager, routing, solution)
            self.distancia_total = solution.ObjectiveValue() / 1000.0  # Convertir a km
            
            print(f"✅ Optimización completada en {self.tiempo_solucion:.2f} segundos")
            print(f"📊 Distancia total óptima: {self.distancia_total:.2f} km")
            
            return self.ruta_optima, self.distancia_total
        else:
            print("❌ No se encontró solución")
            return None, None
    
    def _extraer_ruta(self, manager, routing, solution) -> List[int]:
        """Extrae la secuencia de puntos de la solución"""
        ruta = []
        index = routing.Start(0)
        
        while not routing.IsEnd(index):
            ruta.append(manager.IndexToNode(index))
            index = solution.Value(routing.NextVar(index))
        
        # Agregar el último nodo (regreso al depot)
        ruta.append(manager.IndexToNode(index))
        
        return ruta
    
    def obtener_ruta_detallada(self) -> List[Dict]:
        """
        Retorna información detallada de la ruta óptima
        
        Retorna
        -------
        List[Dict]
            Lista de diccionarios con información de cada parada
        """
        if self.ruta_optima is None:
            raise ValueError("Primero debes resolver el problema con .resolver()")
        
        ruta_detallada = []
        distancia_acumulada = 0.0
        
        for i, idx in enumerate(self.ruta_optima):
            info = {
                'orden': i,
                'indice': idx,
                'nombre': self.nombres_puntos[idx],
                'distancia_acumulada_km': distancia_acumulada
            }
            
            # Calcular distancia al siguiente punto
            if i < len(self.ruta_optima) - 1:
                idx_siguiente = self.ruta_optima[i + 1]
                distancia_tramo = self.matriz_distancias[idx][idx_siguiente]
                info['distancia_siguiente_km'] = distancia_tramo
                distancia_acumulada += distancia_tramo
            else:
                info['distancia_siguiente_km'] = 0.0
            
            ruta_detallada.append(info)
        
        return ruta_detallada
    
    def imprimir_ruta(self):
        """Imprime la ruta óptima de forma legible"""
        if self.ruta_optima is None:
            print("No hay ruta para mostrar. Ejecuta .resolver() primero.")
            return
        
        print("\n" + "="*70)
        print("🗺️  RUTA ÓPTIMA DE ENTREGA")
        print("="*70)
        
        ruta_detallada = self.obtener_ruta_detallada()
        
        for info in ruta_detallada:
            if info['orden'] == 0:
                print(f"\n🏢 INICIO: {info['nombre']}")
            elif info['orden'] == len(ruta_detallada) - 1:
                print(f"\n🏁 REGRESO: {info['nombre']}")
                print(f"   Distancia total recorrida: {info['distancia_acumulada_km']:.2f} km")
            else:
                print(f"\n📦 Parada {info['orden']}: {info['nombre']}")
                print(f"   → Distancia acumulada: {info['distancia_acumulada_km']:.2f} km")
                if info['distancia_siguiente_km'] > 0:
                    print(f"   → Siguiente tramo: {info['distancia_siguiente_km']:.2f} km")
        
        print("\n" + "="*70)
        print(f"⏱️  Tiempo de optimización: {self.tiempo_solucion:.2f} segundos")
        print("="*70 + "\n")
    
    def obtener_metricas(self) -> Dict:
        """
        Retorna métricas de la ruta optimizada
        
        Retorna
        -------
        Dict
            Diccionario con métricas clave
        """
        if self.ruta_optima is None:
            raise ValueError("Primero debes resolver el problema con .resolver()")
        
        ruta_detallada = self.obtener_ruta_detallada()
        distancias_tramos = [
            info['distancia_siguiente_km'] 
            for info in ruta_detallada[:-1]  # Excluir el último (regreso)
        ]
        
        metricas = {
            'distancia_total_km': self.distancia_total,
            'numero_entregas': self.n_puntos - 1,  # Sin contar el depot
            'distancia_promedio_km': np.mean(distancias_tramos),
            'distancia_maxima_tramo_km': np.max(distancias_tramos),
            'distancia_minima_tramo_km': np.min(distancias_tramos),
            'tiempo_optimizacion_seg': self.tiempo_solucion,
            'ruta_completa': [self.nombres_puntos[idx] for idx in self.ruta_optima]
        }
        
        return metricas


def comparar_rutas(ruta_original: List[int], 
                   ruta_optimizada: List[int],
                   matriz_distancias: np.ndarray) -> Dict:
    """
    Compara dos rutas y calcula el ahorro obtenido
    
    Parámetros
    ----------
    ruta_original : List[int]
        Ruta sin optimizar (ej: orden de carga)
    ruta_optimizada : List[int]
        Ruta optimizada
    matriz_distancias : np.ndarray
        Matriz de distancias
        
    Retorna
    -------
    Dict
        Comparación con métricas de ambas rutas
    """
    def calcular_distancia_ruta(ruta, matriz):
        distancia = 0.0
        for i in range(len(ruta) - 1):
            distancia += matriz[ruta[i]][ruta[i+1]]
        return distancia
    
    dist_original = calcular_distancia_ruta(ruta_original, matriz_distancias)
    dist_optimizada = calcular_distancia_ruta(ruta_optimizada, matriz_distancias)
    ahorro_km = dist_original - dist_optimizada
    ahorro_porcentual = (ahorro_km / dist_original) * 100
    
    return {
        'distancia_original_km': dist_original,
        'distancia_optimizada_km': dist_optimizada,
        'ahorro_km': ahorro_km,
        'ahorro_porcentual': ahorro_porcentual
    }

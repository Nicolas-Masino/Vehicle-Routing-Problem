"""
Módulo para calcular matriz de distancias entre múltiples puntos
Utiliza OpenStreetMap para obtener distancias reales de manejo
"""

import numpy as np
import pandas as pd
from typing import List, Tuple, Dict
from tqdm import tqdm
import pickle
import os
from funcion_distancia_OSM import calcular_distancia


class CalculadorMatrizDistancias:
    """
    Calcula y almacena matrices de distancias entre puntos geográficos
    """
    
    def __init__(self, puntos: List[Tuple[float, float]], 
                 nombres: List[str] = None,
                 radio_m: int = 20000):
        """
        Inicializa el calculador de matriz de distancias
        
        Parámetros
        ----------
        puntos : List[Tuple[float, float]]
            Lista de coordenadas (latitud, longitud)
        nombres : List[str], opcional
            Nombres descriptivos para cada punto
        radio_m : int
            Radio en metros para búsqueda OSM
        """
        self.puntos = puntos
        self.n_puntos = len(puntos)
        self.nombres = nombres or [f"Punto_{i}" for i in range(self.n_puntos)]
        self.radio_m = radio_m
        self.matriz_distancias = None
        self.cache_file = None
        
    def calcular_matriz(self, usar_cache: bool = True, 
                       cache_file: str = "matriz_distancias.pkl") -> np.ndarray:
        """
        Calcula la matriz de distancias entre todos los puntos
        
        Parámetros
        ----------
        usar_cache : bool
            Si True, intenta cargar desde cache o guarda el resultado
        cache_file : str
            Nombre del archivo de cache
            
        Retorna
        -------
        np.ndarray
            Matriz NxN con distancias en km
        """
        self.cache_file = cache_file
        
        # Intentar cargar desde cache
        if usar_cache and os.path.exists(cache_file):
            print(f"📂 Cargando matriz desde cache: {cache_file}")
            try:
                with open(cache_file, 'rb') as f:
                    cache_data = pickle.load(f)
                    if self._validar_cache(cache_data):
                        self.matriz_distancias = cache_data['matriz']
                        print(f"✅ Matriz cargada exitosamente ({self.n_puntos}x{self.n_puntos})")
                        return self.matriz_distancias
                    else:
                        print("⚠️  Cache inválido, recalculando...")
            except Exception as e:
                print(f"⚠️  Error al cargar cache: {e}")
        
        # Calcular matriz desde cero
        print(f"\n🗺️  Calculando matriz de distancias para {self.n_puntos} puntos...")
        print(f"   Total de cálculos: {self.n_puntos * (self.n_puntos - 1) // 2}")
        
        self.matriz_distancias = np.zeros((self.n_puntos, self.n_puntos))
        
        # Calcular distancias con barra de progreso
        total_calculos = self.n_puntos * (self.n_puntos - 1) // 2
        errores = []
        
        with tqdm(total=total_calculos, desc="Calculando distancias") as pbar:
            for i in range(self.n_puntos):
                for j in range(i + 1, self.n_puntos):
                    try:
                        distancia = calcular_distancia(
                            self.puntos[i], 
                            self.puntos[j], 
                            radio_m=self.radio_m
                        )
                        self.matriz_distancias[i][j] = distancia
                        self.matriz_distancias[j][i] = distancia  # Simétrica
                    except Exception as e:
                        error_msg = f"Error calculando distancia entre {self.nombres[i]} y {self.nombres[j]}: {e}"
                        errores.append(error_msg)
                        # Usar distancia euclidiana como fallback
                        dist_euclidiana = self._distancia_euclidiana(
                            self.puntos[i], 
                            self.puntos[j]
                        )
                        self.matriz_distancias[i][j] = dist_euclidiana
                        self.matriz_distancias[j][i] = dist_euclidiana
                    
                    pbar.update(1)
        
        # Reportar errores si los hubo
        if errores:
            print(f"\n⚠️  Se encontraron {len(errores)} errores:")
            for error in errores[:5]:  # Mostrar solo los primeros 5
                print(f"   {error}")
            if len(errores) > 5:
                print(f"   ... y {len(errores) - 5} errores más")
        
        print(f"✅ Matriz calculada exitosamente\n")
        
        # Guardar en cache
        if usar_cache:
            self._guardar_cache(cache_file)
        
        return self.matriz_distancias
    
    def _distancia_euclidiana(self, punto1: Tuple[float, float], 
                             punto2: Tuple[float, float]) -> float:
        """
        Calcula distancia euclidiana aproximada en km
        (Usado como fallback cuando OSM falla)
        """
        lat1, lon1 = punto1
        lat2, lon2 = punto2
        
        # Aproximación simple (1 grado ≈ 111 km)
        dlat = (lat2 - lat1) * 111.0
        dlon = (lon2 - lon1) * 111.0 * np.cos(np.radians((lat1 + lat2) / 2))
        
        return np.sqrt(dlat**2 + dlon**2)
    
    def _validar_cache(self, cache_data: Dict) -> bool:
        """Valida que el cache sea compatible"""
        if 'matriz' not in cache_data or 'puntos' not in cache_data:
            return False
        
        if len(cache_data['puntos']) != self.n_puntos:
            return False
        
        # Verificar que los puntos coincidan
        for i, punto in enumerate(self.puntos):
            if not np.allclose(punto, cache_data['puntos'][i], atol=1e-6):
                return False
        
        return True
    
    def _guardar_cache(self, cache_file: str):
        """Guarda la matriz en cache"""
        try:
            cache_data = {
                'matriz': self.matriz_distancias,
                'puntos': self.puntos,
                'nombres': self.nombres,
                'n_puntos': self.n_puntos
            }
            with open(cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
            print(f"💾 Matriz guardada en cache: {cache_file}")
        except Exception as e:
            print(f"⚠️  No se pudo guardar cache: {e}")
    
    def obtener_dataframe(self) -> pd.DataFrame:
        """
        Retorna la matriz como DataFrame con nombres
        
        Retorna
        -------
        pd.DataFrame
            Matriz con índices y columnas nombradas
        """
        if self.matriz_distancias is None:
            raise ValueError("Primero debes calcular la matriz con .calcular_matriz()")
        
        return pd.DataFrame(
            self.matriz_distancias,
            index=self.nombres,
            columns=self.nombres
        )
    
    def imprimir_resumen(self):
        """Imprime un resumen estadístico de la matriz"""
        if self.matriz_distancias is None:
            print("No hay matriz calculada aún.")
            return
        
        # Obtener solo valores no nulos (triángulo superior sin diagonal)
        valores = []
        for i in range(self.n_puntos):
            for j in range(i + 1, self.n_puntos):
                valores.append(self.matriz_distancias[i][j])
        
        valores = np.array(valores)
        
        print("\n" + "="*60)
        print("📊 RESUMEN DE MATRIZ DE DISTANCIAS")
        print("="*60)
        print(f"Número de puntos: {self.n_puntos}")
        print(f"Distancia promedio: {np.mean(valores):.2f} km")
        print(f"Distancia mínima: {np.min(valores):.2f} km")
        print(f"Distancia máxima: {np.max(valores):.2f} km")
        print(f"Desviación estándar: {np.std(valores):.2f} km")
        print("="*60 + "\n")
    
    def visualizar_matriz_heatmap(self):
        """Crea un heatmap de la matriz de distancias"""
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns
            
            if self.matriz_distancias is None:
                print("Primero debes calcular la matriz.")
                return
            
            plt.figure(figsize=(12, 10))
            
            # Crear heatmap
            sns.heatmap(
                self.matriz_distancias,
                annot=False,
                fmt='.1f',
                cmap='YlOrRd',
                xticklabels=self.nombres,
                yticklabels=self.nombres,
                cbar_kws={'label': 'Distancia (km)'}
            )
            
            plt.title('Matriz de Distancias entre Puntos', fontsize=16, pad=20)
            plt.xlabel('Destino', fontsize=12)
            plt.ylabel('Origen', fontsize=12)
            plt.xticks(rotation=45, ha='right')
            plt.yticks(rotation=0)
            plt.tight_layout()
            
            return plt.gcf()
        
        except ImportError:
            print("Para visualizar, instala: pip install matplotlib seaborn")
            return None


def crear_matriz_desde_csv(csv_path: str, 
                           lat_col: str = 'lat',
                           lon_col: str = 'lon',
                           nombre_col: str = 'pedido',
                           depot: Tuple[float, float, str] = None) -> CalculadorMatrizDistancias:
    """
    Crea un calculador de matriz desde un archivo CSV de pedidos
    
    Parámetros
    ----------
    csv_path : str
        Ruta al archivo CSV con pedidos
    lat_col : str
        Nombre de la columna de latitud
    lon_col : str
        Nombre de la columna de longitud
    nombre_col : str
        Nombre de la columna con identificadores
    depot : Tuple[float, float, str], opcional
        (latitud, longitud, nombre) del centro de distribución
        Si se provee, será el primer punto de la matriz
        
    Retorna
    -------
    CalculadorMatrizDistancias
        Instancia lista para calcular matriz
    """
    # Leer CSV
    df = pd.read_csv(csv_path)
    
    # Extraer puntos
    puntos = []
    nombres = []
    
    # Agregar depot primero si existe
    if depot:
        puntos.append((depot[0], depot[1]))
        nombres.append(depot[2])
    
    # Agregar pedidos
    for _, row in df.iterrows():
        puntos.append((row[lat_col], row[lon_col]))
        nombres.append(str(row[nombre_col]))
    
    return CalculadorMatrizDistancias(puntos, nombres)

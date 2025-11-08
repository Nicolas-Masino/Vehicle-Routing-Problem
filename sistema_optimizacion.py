"""
Script Principal: Sistema de Optimización de Rutas para Andreani
Integra generación de pedidos, cálculo de distancias y optimización TSP
"""

import pandas as pd
import geopandas as gpd
import numpy as np
import os
from typing import Tuple, Dict
import argparse

from generador_pedidos import (
    crear_dataset_completo, 
    obtener_depot_por_comuna,
    listar_comunas_disponibles
)
from calculador_matriz import CalculadorMatrizDistancias
from optimizador_rutas import OptimizadorRutas, comparar_rutas


class SistemaOptimizacionRutas:
    """
    Sistema completo de optimización de rutas de entrega
    """
    
    def __init__(self, ruta_shp_comunas: str = "caba/comunas.shp"):
        """
        Inicializa el sistema
        
        Parámetros
        ----------
        ruta_shp_comunas : str
            Ruta al shapefile de comunas
        """
        self.ruta_shp_comunas = ruta_shp_comunas
        self.gdf_comunas = None
        self.df_dataset = None
        self.info_dataset = None
        self.calculador = None
        self.matriz_distancias = None
        self.optimizador = None
        
    def cargar_comunas(self):
        """Carga el shapefile de comunas"""
        if not os.path.exists(self.ruta_shp_comunas):
            raise FileNotFoundError(
                f"No se encontró el shapefile: {self.ruta_shp_comunas}\n"
                "Asegúrate de tener el archivo de comunas de CABA."
            )
        
        print(f"📂 Cargando shapefile de comunas...")
        self.gdf_comunas = gpd.read_file(self.ruta_shp_comunas).to_crs(epsg=4326)
        print(f"✅ Shapefile cargado: {len(self.gdf_comunas)} comunas\n")
        
    def generar_pedidos(self, 
                       comuna_id: int,
                       n_pedidos: int = None,
                       min_pedidos: int = 9,
                       max_pedidos: int = 30,
                       seed: int = None) -> pd.DataFrame:
        """
        Genera pedidos aleatorios para una comuna
        
        Parámetros
        ----------
        comuna_id : int
            ID de la comuna (1-15)
        n_pedidos : int, opcional
            Número exacto de pedidos a generar
        min_pedidos : int
            Mínimo de pedidos si n_pedidos es None
        max_pedidos : int
            Máximo de pedidos si n_pedidos es None
        seed : int, opcional
            Semilla para reproducibilidad
            
        Retorna
        -------
        pd.DataFrame
            Dataset con depot y pedidos
        """
        if self.gdf_comunas is None:
            self.cargar_comunas()
        
        self.df_dataset, self.info_dataset = crear_dataset_completo(
            comuna_id=comuna_id,
            gdf_comunas=self.gdf_comunas,
            n_pedidos=n_pedidos,
            min_pedidos=min_pedidos,
            max_pedidos=max_pedidos,
            seed=seed
        )
        
        return self.df_dataset
    
    def calcular_distancias(self, 
                          usar_cache: bool = True,
                          radio_m: int = 20000) -> np.ndarray:
        """
        Calcula matriz de distancias entre todos los puntos
        
        Parámetros
        ----------
        usar_cache : bool
            Si True, usa cache si está disponible
        radio_m : int
            Radio para búsqueda OSM
            
        Retorna
        -------
        np.ndarray
            Matriz de distancias
        """
        if self.df_dataset is None:
            raise ValueError("Primero debes generar pedidos con .generar_pedidos()")
        
        # Preparar puntos y nombres
        puntos = [
            (row['lat'], row['lon']) 
            for _, row in self.df_dataset.iterrows()
        ]
        nombres = self.df_dataset['pedido'].tolist()
        
        # Crear calculador
        self.calculador = CalculadorMatrizDistancias(
            puntos=puntos,
            nombres=nombres,
            radio_m=radio_m
        )
        
        # Calcular matriz
        cache_file = f"matriz_comuna_{self.info_dataset['comuna_id']}.pkl"
        self.matriz_distancias = self.calculador.calcular_matriz(
            usar_cache=usar_cache,
            cache_file=cache_file
        )
        
        # Mostrar resumen
        self.calculador.imprimir_resumen()
        
        return self.matriz_distancias
    
    def optimizar_ruta(self, tiempo_limite: int = 30) -> Tuple[list, float]:
        """
        Optimiza la ruta de entrega
        
        Parámetros
        ----------
        tiempo_limite : int
            Tiempo máximo de optimización en segundos
            
        Retorna
        -------
        ruta_optima : list
            Lista de índices con el orden óptimo
        distancia_total : float
            Distancia total en km
        """
        if self.matriz_distancias is None:
            raise ValueError("Primero debes calcular distancias con .calcular_distancias()")
        
        # Crear optimizador
        self.optimizador = OptimizadorRutas(
            matriz_distancias=self.matriz_distancias,
            nombres_puntos=self.df_dataset['pedido'].tolist()
        )
        
        # Resolver
        ruta_optima, distancia_total = self.optimizador.resolver(
            tiempo_limite_segundos=tiempo_limite
        )
        
        # Mostrar resultados
        if ruta_optima:
            self.optimizador.imprimir_ruta()
        
        return ruta_optima, distancia_total
    
    def generar_reporte(self, output_path: str = "reporte_optimizacion.txt"):
        """
        Genera un reporte completo de la optimización
        
        Parámetros
        ----------
        output_path : str
            Ruta donde guardar el reporte
        """
        if self.optimizador is None:
            raise ValueError("Primero debes optimizar la ruta")
        
        metricas = self.optimizador.obtener_metricas()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write("REPORTE DE OPTIMIZACIÓN DE RUTAS - ANDREANI\n")
            f.write("="*70 + "\n\n")
            
            # Información del dataset
            f.write("📊 INFORMACIÓN DEL DATASET\n")
            f.write("-"*70 + "\n")
            f.write(f"Comuna: {self.info_dataset['comuna_id']}\n")
            f.write(f"Centro de distribución: {self.info_dataset['depot_nombre']}\n")
            f.write(f"Ubicación depot: {self.info_dataset['depot_coords']}\n")
            f.write(f"Número de pedidos: {self.info_dataset['n_pedidos']}\n")
            f.write(f"Total de puntos: {self.info_dataset['n_puntos_total']}\n\n")
            
            # Métricas de optimización
            f.write("🎯 MÉTRICAS DE OPTIMIZACIÓN\n")
            f.write("-"*70 + "\n")
            f.write(f"Distancia total óptima: {metricas['distancia_total_km']:.2f} km\n")
            f.write(f"Número de entregas: {metricas['numero_entregas']}\n")
            f.write(f"Distancia promedio por tramo: {metricas['distancia_promedio_km']:.2f} km\n")
            f.write(f"Tramo más largo: {metricas['distancia_maxima_tramo_km']:.2f} km\n")
            f.write(f"Tramo más corto: {metricas['distancia_minima_tramo_km']:.2f} km\n")
            f.write(f"Tiempo de optimización: {metricas['tiempo_optimizacion_seg']:.2f} segundos\n\n")
            
            # Ruta completa
            f.write("🗺️  RUTA ÓPTIMA COMPLETA\n")
            f.write("-"*70 + "\n")
            for i, nombre in enumerate(metricas['ruta_completa']):
                f.write(f"{i+1:3d}. {nombre}\n")
            
            f.write("\n" + "="*70 + "\n")
        
        print(f"📄 Reporte guardado en: {output_path}")
    
    def exportar_ruta_csv(self, output_path: str = "ruta_optimizada.csv"):
        """
        Exporta la ruta optimizada a CSV con coordenadas
        
        Parámetros
        ----------
        output_path : str
            Ruta donde guardar el CSV
        """
        if self.optimizador is None:
            raise ValueError("Primero debes optimizar la ruta")
        
        ruta_detallada = self.optimizador.obtener_ruta_detallada()
        
        # Agregar coordenadas a la información de la ruta
        for info in ruta_detallada:
            idx = info['indice']
            row = self.df_dataset.iloc[idx]
            info['lat'] = row['lat']
            info['lon'] = row['lon']
            info['comuna'] = row['comuna']
        
        # Crear DataFrame
        df_ruta = pd.DataFrame(ruta_detallada)
        
        # Guardar
        df_ruta.to_csv(output_path, index=False)
        print(f"📄 Ruta exportada a: {output_path}")
        
        return df_ruta
    
    def ejecutar_flujo_completo(self,
                               comuna_id: int,
                               n_pedidos: int = None,
                               seed: int = None,
                               tiempo_limite: int = 30,
                               usar_cache: bool = True) -> Dict:
        """
        Ejecuta el flujo completo de optimización
        
        Parámetros
        ----------
        comuna_id : int
            ID de la comuna
        n_pedidos : int, opcional
            Número de pedidos a generar
        seed : int, opcional
            Semilla para reproducibilidad
        tiempo_limite : int
            Tiempo máximo de optimización
        usar_cache : bool
            Usar cache de distancias
            
        Retorna
        -------
        Dict
            Resumen de resultados
        """
        print("\n" + "="*70)
        print("🚛 SISTEMA DE OPTIMIZACIÓN DE RUTAS ANDREANI")
        print("="*70 + "\n")
        
        # 1. Generar pedidos
        print("PASO 1: Generación de pedidos")
        print("-"*70)
        self.generar_pedidos(
            comuna_id=comuna_id,
            n_pedidos=n_pedidos,
            seed=seed
        )
        
        # 2. Calcular distancias
        print("\nPASO 2: Cálculo de matriz de distancias")
        print("-"*70)
        self.calcular_distancias(usar_cache=usar_cache)
        
        # 3. Optimizar ruta
        print("\nPASO 3: Optimización de ruta")
        print("-"*70)
        ruta, distancia = self.optimizar_ruta(tiempo_limite=tiempo_limite)
        
        # 4. Generar reportes
        print("\nPASO 4: Generación de reportes")
        print("-"*70)
        self.generar_reporte()
        self.exportar_ruta_csv()
        
        # Resumen final
        metricas = self.optimizador.obtener_metricas()
        
        print("\n" + "="*70)
        print("✅ OPTIMIZACIÓN COMPLETADA")
        print("="*70)
        print(f"📍 Comuna: {comuna_id}")
        print(f"📦 Pedidos: {self.info_dataset['n_pedidos']}")
        print(f"📏 Distancia total: {metricas['distancia_total_km']:.2f} km")
        print(f"⏱️  Tiempo: {metricas['tiempo_optimizacion_seg']:.2f} segundos")
        print("="*70 + "\n")
        
        return {
            'comuna_id': comuna_id,
            'n_pedidos': self.info_dataset['n_pedidos'],
            'distancia_total_km': metricas['distancia_total_km'],
            'tiempo_optimizacion': metricas['tiempo_optimizacion_seg'],
            'ruta_optima': ruta
        }


def main():
    """Función principal para ejecución desde línea de comandos"""
    parser = argparse.ArgumentParser(
        description='Sistema de Optimización de Rutas Andreani'
    )
    parser.add_argument(
        '--comuna', 
        type=int, 
        required=False,
        help='ID de la comuna (1-15)'
    )
    parser.add_argument(
        '--pedidos', 
        type=int, 
        default=None,
        help='Número de pedidos a generar (default: aleatorio entre 9-30)'
    )
    parser.add_argument(
        '--seed', 
        type=int, 
        default=None,
        help='Semilla para reproducibilidad'
    )
    parser.add_argument(
        '--tiempo', 
        type=int, 
        default=30,
        help='Tiempo límite de optimización en segundos'
    )
    parser.add_argument(
        '--sin-cache', 
        action='store_true',
        help='No usar cache de distancias'
    )
    parser.add_argument(
        '--listar-comunas',
        action='store_true',
        help='Listar comunas disponibles'
    )
    
    args = parser.parse_args()
    
    # Listar comunas si se solicitó
    if args.listar_comunas:
        listar_comunas_disponibles()
        return
    
    # Validar que se especificó comuna
    if args.comuna is None:
        print("❌ Error: Debes especificar una comuna con --comuna")
        print("   Usa --listar-comunas para ver las comunas disponibles")
        return
    
    # Validar rango de comuna
    if not (1 <= args.comuna <= 15):
        print("❌ Error: La comuna debe estar entre 1 y 15")
        return
    
    # Crear sistema y ejecutar
    sistema = SistemaOptimizacionRutas()
    
    try:
        resultados = sistema.ejecutar_flujo_completo(
            comuna_id=args.comuna,
            n_pedidos=args.pedidos,
            seed=args.seed,
            tiempo_limite=args.tiempo,
            usar_cache=not args.sin_cache
        )
        
        print("\n✨ ¡Proceso completado exitosamente!")
        
    except Exception as e:
        print(f"\n❌ Error durante la ejecución: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

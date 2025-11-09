# Optimizador de Rutas VRP - Aplicación Streamlit

MVP de optimización de rutas de vehículos (Vehicle Routing Problem) con visualización interactiva.

## Características

- **Optimización de rutas** usando OR-Tools (Google)
- **Visualización interactiva** con mapas de Folium
- **Rutas reales** obtenidas de OSRM (Open Source Routing Machine)
- **Interfaz intuitiva** con Streamlit
- **Múltiples métodos de carga**: CSV o generación aleatoria

## Instalación

### 1. Clonar el repositorio o descargar los archivos

```bash
cd Vehicle-Routing-Problem
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

## Ejecutar la aplicación

```bash
streamlit run app_vrp.py
```

La aplicación se abrirá automáticamente en tu navegador en `http://localhost:8501`

## Uso de la aplicación

### Panel Izquierdo - Configuración

1. **Depósito**:
   - Selecciona una ubicación predefinida (Retiro, Palermo, etc.) o ingresa coordenadas personalizadas
   - Lat/Lon deben estar en formato decimal

2. **Configuración de Flota**:
   - Camiones: 1 a 5
   - Capacidad: 5 a 15 paquetes por camión

3. **Ingreso de Pedidos**:
   - **Opción 1 - CSV**: Sube un archivo CSV con columnas `lat`, `lon` (y opcionalmente `order_id`)
   - **Opción 2 - Aleatorio**: Genera pedidos aleatorios dentro de CABA

4. **Optimizar**: Presiona el botón para ejecutar el algoritmo

### Panel Central - Visualización

- **Tabs por camión**: Muestra la ruta individual de cada camión
- **Vista General**: Muestra todas las rutas juntas
- **Elementos del mapa**:
  - Depósito (icono rojo de casa)
  - Puntos de entrega (círculos de colores)
  - Rutas reales (líneas de colores)
  - Polígonos de barrios de CABA (fondo gris)

### Panel Derecho - Órdenes y Métricas

- **Lista de paradas**: Orden secuencial de entregas para el camión seleccionado
- **Métricas individuales**: Distancia y paquetes por camión
- **Métricas generales**: Totales de la operación completa

## Formato del CSV

El archivo CSV debe tener las siguientes columnas:

```csv
order_id,lat,lon
1,-34.603,-58.381
2,-34.610,-58.400
3,-34.598,-58.425
```

- **Obligatorio**: `lat` y `lon`
- **Opcional**: `order_id` o `pedido_id` (se genera automáticamente si no existe)

**Ejemplo**: Ver archivo `pedidos_ejemplo.csv`

## Validaciones

- Latitud: entre -90 y 90
- Longitud: entre -180 y 180
- Total de pedidos ≤ (número de camiones × capacidad por camión)
- CSV no vacío y con formato correcto

## Algoritmo de Optimización

La aplicación utiliza **OR-Tools** de Google con la siguiente configuración:

- **Estrategia inicial**: PATH_CHEAPEST_ARC
- **Meta-heurística**: GUIDED_LOCAL_SEARCH
- **Límite de tiempo**: 30 segundos
- **Restricciones**: Capacidad de vehículos

## Rutas Reales

Las rutas se calculan usando **OSRM** (Open Source Routing Machine), que proporciona:

- Distancias reales por calles
- Geometría exacta de las rutas
- Fallback automático a distancia euclidiana si OSRM no está disponible

## Caché de Distancias

La aplicación guarda en caché las matrices de distancias para evitar recalcularlas:

- Archivos: `vrp_streamlit_N.npz` (donde N = número de ubicaciones)
- Se reutilizan si las ubicaciones son las mismas
- Mejora significativa de performance

## Estructura de archivos

```
Vehicle-Routing-Problem/
├── app_vrp.py              # Aplicación principal
├── requirements.txt        # Dependencias
├── pedidos_ejemplo.csv     # Ejemplo de CSV
├── README_APP.md          # Este archivo
└── utils/
    └── barrios copy.csv    # Polígonos de CABA (REQUERIDO)
```

**IMPORTANTE**: El archivo `utils/barrios copy.csv` es necesario para visualizar los barrios de CABA.

## Métricas y KPIs

La aplicación calcula automáticamente:

- Distancia total de todas las rutas
- Distancia individual por camión
- Paquetes entregados por camión
- Utilización de flota (%)
- Tiempo de optimización

## Solución de Problemas

### Error: "No se pudo cargar el archivo de barrios"
- Verifica que existe `utils/barrios copy.csv` en la carpeta correcta

### Error: "No se encontró solución óptima"
- Reduce el número de pedidos
- Aumenta el número de camiones o su capacidad
- Verifica que total_pedidos ≤ capacidad_total

### Las rutas no se ven en el mapa
- Verifica tu conexión a internet (OSRM requiere conexión)
- La aplicación usará líneas rectas si OSRM falla

### Performance lenta
- Reduce el número de pedidos (ideal: < 30)
- Las primeras optimizaciones tardan más (calculando matriz de distancias)
- Optimizaciones posteriores son más rápidas (usan caché)

## Tecnologías Utilizadas

- **Streamlit**: Framework de aplicación web
- **OR-Tools**: Optimización de rutas
- **Folium**: Mapas interactivos
- **GeoPandas**: Manejo de datos geoespaciales
- **OSRM**: Cálculo de rutas reales
- **Shapely**: Geometrías y polígonos

## Limitaciones

- Máximo recomendado: 50 pedidos
- Requiere conexión a internet para OSRM
- Optimización limitada a 30 segundos
- Solo funciona para CABA (Buenos Aires)

## Próximas Mejoras

- [ ] Ventanas de tiempo de entrega
- [ ] Múltiples depósitos
- [ ] Exportar resultados a Excel/PDF
- [ ] Integración con APIs de geocodificación
- [ ] Soporte para otras ciudades
- [ ] Visualización 3D de rutas

## Contacto y Soporte

Para reportar bugs o solicitar features, por favor abre un issue en el repositorio.

---

**Versión**: 1.0.0
**Última actualización**: Noviembre 2024

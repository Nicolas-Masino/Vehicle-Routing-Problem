# Modelado Matemático - Vehicle Routing Problem (VRP)

## Índice

1. [Descripción del Problema](#1-descripción-del-problema)
2. [Objetivo del Modelo](#2-objetivo-del-modelo)
3. [Conjuntos e Índices](#3-conjuntos-e-índices)
4. [Parámetros](#4-parámetros)
5. [Variables de Decisión](#5-variables-de-decisión)
6. [Función Objetivo](#6-función-objetivo)
7. [Restricciones](#7-restricciones)
8. [Formulación Matemática Completa](#8-formulación-matemática-completa)
9. [Método de Solución](#9-método-de-solución)
10. [Análisis Económico Post-Optimización](#10-análisis-económico-post-optimización)
11. [Implementación](#11-implementación)

---

## 1. Descripción del Problema

Este proyecto implementa un **Problema de Ruteo de Vehículos Capacitado (CVRP - Capacitated Vehicle Routing Problem)** para optimizar la distribución de pedidos en la Ciudad Autónoma de Buenos Aires (CABA).

### Características del Problema

- **Tipo**: CVRP (Capacitated Vehicle Routing Problem)
- **Contexto**: Distribución de última milla en CABA
- **Aplicación**: Aplicación web interactiva con Streamlit
- **Objetivo principal**: Minimizar la distancia total recorrida por la flota
- **Objetivo secundario**: Análisis de viabilidad económica de la operación

### Elementos del Problema

El problema consiste en:

1. **Depósito único**: Centro de distribución donde inician y terminan todas las rutas
2. **Conjunto de pedidos**: Entregas a realizar en diferentes ubicaciones de CABA
3. **Flota de vehículos**: Múltiples camiones con capacidad limitada
4. **Restricción de capacidad**: Cada vehículo puede transportar un máximo de paquetes
5. **Red vial real**: Distancias calculadas sobre calles y avenidas reales de CABA

### Decisiones a Tomar

- ¿Qué pedidos debe entregar cada vehículo?
- ¿En qué orden debe visitar cada cliente?
- ¿Qué ruta debe seguir cada vehículo?

---

## 2. Objetivo del Modelo

Determinar las rutas óptimas para una flota de vehículos que minimicen la distancia total recorrida, cumpliendo con:

- Cada pedido debe ser entregado exactamente una vez
- Cada vehículo debe respetar su capacidad máxima
- Todos los vehículos parten y regresan al depósito
- Las rutas deben ser factibles en la red vial de CABA

---

## 3. Conjuntos e Índices

### Conjuntos

**N**: Conjunto de todos los nodos (ubicaciones)
- N = {0, 1, 2, ..., n}
- Donde n = número de pedidos

**C**: Conjunto de clientes (pedidos)
- C = {1, 2, ..., n}
- C ⊂ N

**V**: Conjunto de vehículos (camiones)
- V = {1, 2, ..., K}
- K = número de vehículos disponibles

**A**: Conjunto de arcos (conexiones entre ubicaciones)
- A = {(i, j) : i, j ∈ N, i ≠ j}

### Índices

- **i, j**: Índices de nodos (i, j ∈ N)
- **k**: Índice de vehículo (k ∈ V)
- **0**: Índice del depósito (nodo depot)

### Estructura de Datos Implementada

```python
# app_vrp.py, líneas 221-227
data = {
    'distance_matrix': distance_matrix.tolist(),  # matriz NxN en metros
    'demands': [0] + [1] * (len(all_locations) - 1),  # demandas
    'vehicle_capacities': [vehicle_capacity] * num_vehicles,  # capacidades
    'num_vehicles': num_vehicles,  # K vehículos
    'depot': 0  # nodo 0 es el depósito
}
```

---

## 4. Parámetros

### 4.1 Parámetros de Red

#### Matriz de Distancias

**d<sub>ij</sub>**: Distancia del nodo i al nodo j (en metros)

**Método de cálculo** (`app_vrp.py`, líneas 121-166):

1. **OSRM API** (método principal):
   ```python
   url = "http://router.project-osrm.org/table/v1/driving/{coords}?annotations=distance"
   ```
   - Utiliza red vial real de OpenStreetMap
   - Considera sentidos de circulación
   - Distancias en metros por calles reales

2. **Distancia Euclidiana** (fallback si OSRM falla):
   ```python
   distance_matrix[i][j] = sqrt(
       ((lat2 - lat1) × 111000)² +
       ((lon2 - lon1) × 111000 × cos(lat1))²
   )
   ```
   - Factor de conversión: 1° latitud ≈ 111,000 metros
   - Factor de conversión: 1° longitud ≈ 111,000 × cos(latitud) metros

**Formato**: Matriz entera NxN en metros (requerido por OR-Tools)

#### Sistema de Cache

```python
# app_vrp.py, líneas 136-143
cache_file = f'vrp_streamlit_{n}.npz'
# Almacena matrices en formato NumPy comprimido
```

---

### 4.2 Parámetros de Demanda

**q<sub>i</sub>**: Demanda del nodo i (número de paquetes)

**Implementación** (`app_vrp.py`, línea 224):
```python
data['demands'] = [0] + [1] * (len(all_locations) - 1)
```

- **q<sub>0</sub> = 0**: El depósito no tiene demanda
- **q<sub>i</sub> = 1**: Cada pedido representa 1 paquete (∀i ∈ C)

---

### 4.3 Parámetros de Flota

#### Ubicaciones del Depósito

5 ubicaciones predefinidas en CABA (`app_vrp.py`, líneas 450-456):

| Ubicación | Latitud | Longitud |
|-----------|---------|----------|
| Retiro | -34.603277 | -58.373207 |
| Palermo | -34.577882 | -58.420664 |
| Recoleta | -34.588249 | -58.396328 |
| San Telmo | -34.621340 | -58.372150 |
| Belgrano | -34.562991 | -58.457417 |

**También permite**: Ubicación personalizada con coordenadas manuales

#### Número de Vehículos

**K**: Número de vehículos disponibles

**Configuración** (`app_vrp.py`, línea 480):
```python
num_vehicles = st.slider("Cantidad de Camiones", min_value=1, max_value=5, value=3)
```

- **Rango**: 1 a 5 vehículos
- **Por defecto**: 3 vehículos

#### Capacidad de Vehículos

**Q<sub>k</sub>**: Capacidad máxima del vehículo k (paquetes)

**Configuración** (`app_vrp.py`, línea 481):
```python
vehicle_capacity = st.slider("Capacidad por Camión", min_value=5, max_value=15, value=15)
```

**Implementación**:
```python
data['vehicle_capacities'] = [vehicle_capacity] * num_vehicles
```

- **Rango**: 5 a 15 paquetes por vehículo
- **Por defecto**: 15 paquetes
- **Nota**: Todos los vehículos tienen la misma capacidad

---

### 4.4 Parámetros Económicos

#### Parámetros de Costo

**p<sub>nafta</sub>**: Precio de nafta por litro ($/L)

**Configuración** (`app_vrp.py`, líneas 491-498):
```python
precio_nafta = st.number_input(
    "Precio Nafta ($/L)",
    min_value=0.0,
    value=1000.0,  # default
    step=50.0,
    format="%.2f"
)
```
- **Rango**: ≥ 0
- **Por defecto**: $1,000.00/L
- **Incremento**: $50

---

**r<sub>vehiculo</sub>**: Rendimiento del vehículo (km/L)

**Configuración** (`app_vrp.py`, líneas 500-507):
```python
rendimiento_vehiculo = st.number_input(
    "Rendimiento (km/L)",
    min_value=0.1,
    value=10.0,  # default
    step=0.5,
    format="%.2f"
)
```
- **Rango**: ≥ 0.1 km/L
- **Por defecto**: 10.0 km/L
- **Incremento**: 0.5 km/L

---

**v<sub>promedio</sub>**: Velocidad promedio (km/h)

**Configuración** (`app_vrp.py`, líneas 509-516):
```python
velocidad_promedio_kmh = st.number_input(
    "Velocidad Promedio (km/h)",
    min_value=1.0,
    value=30.0,  # default
    step=5.0,
    format="%.1f"
)
```
- **Rango**: ≥ 1.0 km/h
- **Por defecto**: 30.0 km/h
- **Incremento**: 5.0 km/h

---

**c<sub>chofer</sub>**: Costo del chofer por hora ($/h)

**Configuración** (`app_vrp.py`, líneas 537-544):
```python
costo_chofer_por_hora = st.number_input(
    "Costo Chofer ($/h)",
    min_value=0.0,
    value=2000.0,  # default
    step=100.0,
    format="%.2f"
)
```
- **Rango**: ≥ 0
- **Por defecto**: $2,000.00/h
- **Incremento**: $100

---

#### Parámetros de Ingreso

**p<sub>base</sub>**: Precio base por pedido entregado ($)

**Configuración** (`app_vrp.py`, líneas 519-526):
```python
precio_base_por_pedido = st.number_input(
    "Precio Base ($/pedido)",
    min_value=0.0,
    value=2000.0,  # default
    step=100.0,
    format="%.2f"
)
```
- **Rango**: ≥ 0
- **Por defecto**: $2,000.00/pedido
- **Incremento**: $100

---

**p<sub>km</sub>**: Precio variable por kilómetro ($/km)

**Configuración** (`app_vrp.py`, líneas 528-535):
```python
precio_por_km = st.number_input(
    "Precio por km ($/km)",
    min_value=0.0,
    value=150.0,  # default
    step=10.0,
    format="%.2f"
)
```
- **Rango**: ≥ 0
- **Por defecto**: $150.00/km
- **Incremento**: $10

---

### 4.5 Parámetros de Optimización

**t<sub>max</sub>**: Tiempo límite de búsqueda (segundos)

**Implementación** (`app_vrp.py`, línea 270):
```python
search_parameters.time_limit.seconds = 30
```
- **Valor fijo**: 30 segundos
- **Nota**: No configurable desde la UI

**Estrategia inicial**: PATH_CHEAPEST_ARC
```python
# app_vrp.py, líneas 264-266
search_parameters.first_solution_strategy = (
    routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
)
```

**Metaheurística**: GUIDED_LOCAL_SEARCH
```python
# app_vrp.py, líneas 267-269
search_parameters.local_search_metaheuristic = (
    routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
)
```

---

### 4.6 Validaciones de Entrada

#### Validación de Coordenadas

**Latitud** (`app_vrp.py`, líneas 568-569):
```
-90° ≤ lat<sub>i</sub> ≤ 90°  ∀i ∈ N
```

**Longitud** (`app_vrp.py`, líneas 570-571):
```
-180° ≤ lon<sub>i</sub> ≤ 180°  ∀i ∈ N
```

#### Validación de Capacidad Total

**Implementación** (`app_vrp.py`, líneas 622-626):
```python
total_capacity = num_vehicles * vehicle_capacity
if len(orders) > total_capacity:
    st.error(f"Total de pedidos ({len(orders)}) excede la capacidad total ({total_capacity})")
    st.stop()
```

**Restricción**:
```
Σ q<sub>i</sub> ≤ Σ Q<sub>k</sub>
i∈C     k∈V
```

Es decir: La demanda total no puede exceder la capacidad total de la flota.

---

## 5. Variables de Decisión

### Variables Binarias Implícitas

OR-Tools maneja las variables de decisión internamente. Conceptualmente, el modelo utiliza:

**x<sub>ijk</sub>** ∈ {0, 1} para todo i, j ∈ N, k ∈ V

Donde:
- x<sub>ijk</sub> = 1 si el vehículo k viaja directamente del nodo i al nodo j
- x<sub>ijk</sub> = 0 en caso contrario

### Variables Auxiliares (implícitas)

**y<sub>ik</sub>** ∈ {0, 1} para todo i ∈ C, k ∈ V
- y<sub>ik</sub> = 1 si el cliente i es atendido por el vehículo k
- y<sub>ik</sub> = 0 en caso contrario

**u<sub>ik</sub>** ≥ 0 para todo i ∈ N, k ∈ V
- u<sub>ik</sub> = carga acumulada del vehículo k al llegar al nodo i
- Usada para verificar restricción de capacidad

---

## 6. Función Objetivo

### Minimizar Distancia Total

**Implementación** (`app_vrp.py`, líneas 237-244):
```python
def distance_callback(from_index, to_index):
    from_node = manager.IndexToNode(from_index)
    to_node = manager.IndexToNode(to_index)
    return data['distance_matrix'][from_node][to_node]

transit_callback_index = routing.RegisterTransitCallback(distance_callback)
routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
```

**Formulación matemática**:
```
Minimizar Z = Σ   Σ   Σ   d<sub>ij</sub> × x<sub>ijk</sub>
              k∈V i∈N j∈N
```

**Significado**: Minimizar la suma de las distancias de todos los arcos recorridos por todos los vehículos.

### Extracción del Valor Óptimo

**Implementación** (`app_vrp.py`, líneas 281-294):
```python
for vehicle_id in range(data['num_vehicles']):
    index = routing.Start(vehicle_id)
    route_distance = 0

    while not routing.IsEnd(index):
        previous_index = index
        index = solution.Value(routing.NextVar(index))
        route_distance += routing.GetArcCostForVehicle(previous_index, index, vehicle_id)
```

**Conversión a kilómetros** (`app_vrp.py`, línea 772):
```python
total_distance = sum(r['distance'] for r in all_routes)  # en metros
distancia_total_km = total_distance / 1000  # convertir a km
```

---

## 7. Restricciones

### R1. Restricción de Capacidad

**Implementación** (`app_vrp.py`, líneas 246-260):
```python
def demand_callback(from_index):
    from_node = manager.IndexToNode(from_index)
    return data['demands'][from_node]

demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)

routing.AddDimensionWithVehicleCapacity(
    demand_callback_index,
    0,  # null capacity slack (sin holgura)
    data['vehicle_capacities'],  # [Q_1, Q_2, ..., Q_K]
    True,  # start cumul to zero (carga inicial = 0)
    'Capacity'  # nombre de la dimensión
)
```

**Formulación matemática**:
```
Σ q<sub>i</sub> × y<sub>ik</sub> ≤ Q<sub>k</sub>    ∀k ∈ V
i∈C
```

**Significado**: La suma de las demandas de los clientes atendidos por el vehículo k no puede exceder su capacidad.

**Parámetros en el código**:
- `null capacity slack = 0`: No hay holgura, la capacidad es estricta
- `start cumul to zero = True`: Cada vehículo inicia con carga 0 en el depósito

---

### R2. Cada Cliente Visitado Exactamente Una Vez

**Formulación matemática**:
```
Σ   Σ   x<sub>ijk</sub> = 1    ∀i ∈ C
k∈V j∈N
```

**Implementación**: Implícita en OR-Tools RoutingModel. El solver garantiza automáticamente que cada nodo (excepto el depot) sea visitado exactamente una vez.

---

### R3. Conservación de Flujo

**Formulación matemática**:
```
Σ   x<sub>ijk</sub> = Σ   x<sub>jik</sub>    ∀j ∈ N, ∀k ∈ V
i∈N         i∈N
```

**Significado**: Si un vehículo llega a un nodo, debe salir de ese nodo (conservación de flujo).

**Implementación**: Implícita en OR-Tools RoutingModel.

---

### R4. Cada Vehículo Sale del Depósito (máximo una vez)

**Formulación matemática**:
```
Σ   x<sub>0jk</sub> ≤ 1    ∀k ∈ V
j∈C
```

**Implementación**: Implícita al definir el depot en el manager (`app_vrp.py`, líneas 230-234):
```python
manager = pywrapcp.RoutingIndexManager(
    len(data['distance_matrix']),
    data['num_vehicles'],
    data['depot']  # índice 0 es el depósito
)
```

---

### R5. Cada Vehículo Regresa al Depósito

**Formulación matemática**:
```
Σ   x<sub>i0k</sub> ≤ 1    ∀k ∈ V
i∈C
```

**Implementación**: Implícita en OR-Tools. Si un vehículo sale, debe regresar.

**Extracción en el código** (`app_vrp.py`, líneas 296-298):
```python
# Agregar regreso al depósito
node_index = manager.IndexToNode(index)
route_nodes.append(node_index)  # último nodo es depot (0)
```

---

### R6. Consistencia de Salida y Regreso

**Formulación matemática**:
```
Σ   x<sub>0jk</sub> = Σ   x<sub>i0k</sub>    ∀k ∈ V
j∈C         i∈C
```

**Significado**: Un vehículo solo puede regresar si salió del depósito.

**Implementación**: Implícita en OR-Tools.

---

### R7. Validación de Capacidad Total Previa

**Implementación** (`app_vrp.py`, líneas 622-626):
```python
total_capacity = num_vehicles * vehicle_capacity
if len(orders) > total_capacity:
    st.error(f"Total de pedidos ({len(orders)}) excede la capacidad total ({total_capacity})")
    st.stop()
```

**Formulación matemática**:
```
Σ   q<sub>i</sub> ≤ Σ   Q<sub>k</sub>
i∈C     k∈V
```

**Nota**: Esta validación ocurre ANTES de la optimización para evitar problemas infactibles.

---

### R8. Validación de Coordenadas

**Implementación** (`app_vrp.py`, líneas 568-571):
```python
if not df_pedidos['lat'].between(-90, 90).all():
    st.error("Latitudes fuera de rango (-90, 90)")
elif not df_pedidos['lon'].between(-180, 180).all():
    st.error("Longitudes fuera de rango (-180, 180)")
```

**Formulación matemática**:
```
-90 ≤ lat<sub>i</sub> ≤ 90    ∀i ∈ N
-180 ≤ lon<sub>i</sub> ≤ 180  ∀i ∈ N
```

---

## 8. Formulación Matemática Completa

### Modelo CVRP Implementado

```
Minimizar:
    Z = Σ   Σ   Σ   d<sub>ij</sub> × x<sub>ijk</sub>
        k∈V i∈N j∈N

Sujeto a:

(1) Visita única (implícita en OR-Tools):
    Σ   Σ   x<sub>ijk</sub> = 1                           ∀i ∈ C
    k∈V j∈N

(2) Conservación de flujo (implícita en OR-Tools):
    Σ   x<sub>ijk</sub> = Σ   x<sub>jik</sub>                       ∀j ∈ N, ∀k ∈ V
    i∈N         i∈N

(3) Capacidad del vehículo (implementada con AddDimensionWithVehicleCapacity):
    Σ   q<sub>i</sub> × y<sub>ik</sub> ≤ Q<sub>k</sub>                      ∀k ∈ V
    i∈C

(4) Salida del depósito (implícita al definir depot):
    Σ   x<sub>0jk</sub> ≤ 1                             ∀k ∈ V
    j∈C

(5) Regreso al depósito (implícita en OR-Tools):
    Σ   x<sub>i0k</sub> ≤ 1                             ∀k ∈ V
    i∈C

(6) Consistencia de ruta (implícita en OR-Tools):
    Σ   x<sub>0jk</sub> = Σ   x<sub>i0k</sub>                       ∀k ∈ V
    j∈C         i∈C

(7) Relación entre x e y:
    y<sub>ik</sub> = Σ   x<sub>ijk</sub>                          ∀i ∈ C, ∀k ∈ V
           j∈N

(8) Variables binarias:
    x<sub>ijk</sub> ∈ {0, 1}                          ∀i,j ∈ N, ∀k ∈ V
    y<sub>ik</sub> ∈ {0, 1}                           ∀i ∈ C, ∀k ∈ V

(9) Variables no negativas:
    u<sub>ik</sub> ≥ 0                                ∀i ∈ N, ∀k ∈ V

(10) Validación previa de capacidad:
    Σ   q<sub>i</sub> ≤ Σ   Q<sub>k</sub>
    i∈C     k∈V

(11) Validación de coordenadas:
    -90 ≤ lat<sub>i</sub> ≤ 90                        ∀i ∈ N
    -180 ≤ lon<sub>i</sub> ≤ 180                      ∀i ∈ N
```

### Valores del Problema

Con la configuración por defecto:
- **N**: Variable (depende del número de pedidos ingresados)
- **K**: 3 vehículos
- **Q<sub>k</sub>**: 15 paquetes por vehículo
- **q<sub>i</sub>**: 1 paquete por pedido
- **d<sub>ij</sub>**: Calculado por OSRM (distancias reales en metros)

---

## 9. Método de Solución

### Herramienta: Google OR-Tools

**Biblioteca utilizada** (`app_vrp.py`, líneas 16-17):
```python
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
```

**Versión requerida**: `ortools>=9.7.0`

---

### Tipo de Solver

OR-Tools **NO es un solver de Programación Lineal** (no usa Simplex). Es un solver de **Constraint Programming + Metaheurísticas** especializado en problemas combinatorios.

**Características**:
- ✅ Diseñado específicamente para VRP y problemas de ruteo
- ✅ Maneja eficientemente problemas NP-Hard
- ✅ Encuentra soluciones de alta calidad en tiempo razonable
- ❌ NO garantiza optimalidad global
- ❌ NO proporciona precios sombra ni costos reducidos

---

### Estrategia de Solución Inicial

**PATH_CHEAPEST_ARC** (`app_vrp.py`, líneas 264-266):
```python
search_parameters.first_solution_strategy = (
    routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
)
```

**Funcionamiento**:
1. Inicia con todas las rutas vacías
2. Iterativamente agrega el arco más barato disponible
3. Respeta restricciones de capacidad y visita única
4. Construye una solución inicial factible de buena calidad

**Tiempo típico**: 1-3 segundos

---

### Metaheurística de Mejora

**GUIDED_LOCAL_SEARCH (GLS)** (`app_vrp.py`, líneas 267-269):
```python
search_parameters.local_search_metaheuristic = (
    routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
)
```

**Funcionamiento de GLS**:

```
1. Búsqueda local: Mejora la solución actual con movimientos locales
   ↓
2. Detección de óptimo local: No hay mejora posible
   ↓
3. Penalización: Aumenta el costo de arcos usados frecuentemente
   ↓
4. Nueva búsqueda: Explora regiones diferentes del espacio
   ↓
5. Repetición: Vuelve al paso 1 hasta alcanzar tiempo límite
```

**Ventajas**:
- Escapa de óptimos locales mediante penalizaciones adaptativas
- Balance entre intensificación (explotar soluciones buenas) y diversificación (explorar regiones nuevas)
- Especialmente efectiva para VRP

**Calidad típica**: 90-98% del óptimo global

---

### Límite de Tiempo

**Configuración** (`app_vrp.py`, línea 270):
```python
search_parameters.time_limit.seconds = 30
```

**Valor fijo**: 30 segundos

**Comportamiento al alcanzar el límite**:

```
t = 0s    → Solución inicial (PATH_CHEAPEST_ARC)
t = 1-3s  → Primera solución construida
t = 3-25s → Mejoras iterativas (GUIDED_LOCAL_SEARCH)
t = 30s   ⏰ LÍMITE ALCANZADO
          ↓
          Retorna la MEJOR solución encontrada hasta el momento
```

**Importante**:
- ✅ Siempre retorna una solución válida (si existe)
- ✅ La solución cumple todas las restricciones
- ✅ La solución es de buena calidad (90-98% del óptimo)
- ❌ NO garantiza que sea la óptima global
- ❌ El solver NO retorna `None` por límite de tiempo
- ❌ Solo retorna `None` si NO existe solución factible

**Verificación** (`app_vrp.py`, líneas 275-276):
```python
if not solution:
    return None, None, None, None, None
```

Esto ocurre solo si:
- La capacidad total es insuficiente (aunque hay validación previa)
- El problema está mal formulado
- No existe solución factible

---

### Proceso de Optimización Completo

**Implementación** (`app_vrp.py`, líneas 207-307):

```
1. Preparación de datos (líneas 221-227)
   ├─ Convertir matriz de distancias a lista
   ├─ Definir demandas: [0, 1, 1, ..., 1]
   ├─ Definir capacidades: [Q, Q, ..., Q]
   └─ Definir depot: 0

2. Creación del manager (líneas 230-234)
   └─ Mapeo entre índices internos y nodos reales

3. Creación del modelo (línea 235)
   └─ Instancia del RoutingModel

4. Registro de callback de distancia (líneas 237-244)
   └─ Define cómo calcular el costo de cada arco

5. Registro de callback de demanda (líneas 246-251)
   └─ Define la demanda de cada nodo

6. Agregar dimensión de capacidad (líneas 254-260)
   └─ Implementa la restricción de capacidad

7. Configurar parámetros de búsqueda (líneas 263-270)
   ├─ Estrategia inicial: PATH_CHEAPEST_ARC
   ├─ Metaheurística: GUIDED_LOCAL_SEARCH
   └─ Tiempo límite: 30 segundos

8. Resolver (línea 273)
   └─ Ejecuta la optimización

9. Extraer rutas (líneas 278-306)
   ├─ Para cada vehículo:
   │  ├─ Seguir la secuencia de nodos
   │  ├─ Acumular distancia recorrida
   │  ├─ Acumular paquetes transportados
   │  └─ Registrar nodos visitados
   └─ Retornar todas las rutas
```

---

### Cálculo de Matriz de Distancias

#### Método Principal: OSRM API

**Implementación** (`app_vrp.py`, líneas 145-157):
```python
coords = ";".join([f"{loc['lon']},{loc['lat']}" for loc in locations])
url = f"http://router.project-osrm.org/table/v1/driving/{coords}?annotations=distance"

response = requests.get(url, timeout=30)
data = response.json()

if data['code'] == 'Ok':
    distance_matrix = np.array(data['distances'])  # matriz en metros
```

**Características de OSRM**:
- Utiliza datos de OpenStreetMap
- Calcula distancias en red vial real (calles y avenidas)
- Considera sentidos de circulación
- Retorna matriz NxN en metros
- API pública gratuita: `http://router.project-osrm.org`

**Formato de la solicitud**:
```
http://router.project-osrm.org/table/v1/driving/
    lon1,lat1;lon2,lat2;lon3,lat3;...
    ?annotations=distance
```

---

#### Método Fallback: Distancia Euclidiana

**Implementación** (`app_vrp.py`, líneas 114-117):
```python
distance_matrix[i][j] = np.sqrt(
    ((lat2 - lat1) * 111000)**2 +
    ((lon2 - lon1) * 111000 * np.cos(np.radians(lat1)))**2
)
```

**Fórmula matemática**:
```
d<sub>ij</sub> = √[(Δlat × 111000)² + (Δlon × 111000 × cos(lat<sub>i</sub>))²]

donde:
Δlat = lat<sub>j</sub> - lat<sub>i</sub>
Δlon = lon<sub>j</sub> - lon<sub>i</sub>
```

**Factores de conversión**:
- **1° de latitud** ≈ 111,000 metros (constante)
- **1° de longitud** ≈ 111,000 × cos(latitud) metros (varía con la latitud)

**Uso**: Solo se activa si OSRM falla o no está disponible.

---

#### Sistema de Cache

**Implementación** (`app_vrp.py`, líneas 136-143):
```python
cache_file = f'vrp_streamlit_{n}.npz'

if use_cache:
    try:
        cache = np.load(cache_file)
        return cache['distance']
    except:
        pass

# ... calcular matriz ...

if use_cache:
    np.savez(cache_file, distance=distance_matrix)
```

**Beneficios**:
- Evita recalcular matrices costosas
- Acelera ejecuciones repetidas con mismo número de puntos
- Formato `.npz` (NumPy compressed) eficiente

**Nombre de archivo**: `vrp_streamlit_{n}.npz` donde n = número de ubicaciones

---

### Visualización de Rutas

**Biblioteca**: Folium (mapas interactivos basados en Leaflet.js)

**Implementación** (`app_vrp.py`, líneas 313-416):

1. **Obtener geometría real de OSRM** (líneas 168-201):
   ```python
   url = f"http://router.project-osrm.org/route/v1/driving/{coords}?overview=full&geometries=polyline"
   encoded_polyline = data['routes'][0]['geometry']
   decoded = polyline.decode(encoded_polyline)  # lista de (lat, lon)
   ```

2. **Crear mapa base** (líneas 332-336):
   - Centro: coordenadas del depósito
   - Zoom: 12
   - Tiles: OpenStreetMap

3. **Agregar elementos**:
   - Polígonos de barrios de CABA (fondo gris semitransparente)
   - Marcador del depósito (rojo, icono de casa)
   - Rutas de vehículos (líneas de colores sobre calles reales)
   - Puntos de entrega (círculos de colores)
   - Popups interactivos con información

**Colores de vehículos** (línea 339):
```python
colors = ['green', 'orange', 'purple', 'brown', 'pink', 'cyan']
```

---

## 10. Análisis Económico Post-Optimización

### ⚠️ NOTA IMPORTANTE - Limitaciones Metodológicas

El análisis presentado **NO es el análisis de sensibilidad clásico de Programación Lineal** (precios sombra, costos reducidos) debido a las siguientes razones:

1. **OR-Tools utiliza metaheurísticas**, no el método Simplex
2. **No proporciona información dual** (precios sombra de restricciones)
3. **No calcula costos reducidos** de variables
4. **No es un solver de LP**, es un solver de Constraint Programming

Este es un **análisis económico de punto de equilibrio (break-even)** calculado manualmente mediante fórmulas algebraicas sobre la solución ya optimizada.

**Asume**:
- La distancia óptima D* es fija (resultado de la optimización)
- Los parámetros económicos son externos al modelo de optimización
- Se analiza viabilidad económica, no sensibilidad del modelo matemático

**Pregunta que responde**:
> "Dada la solución óptima con distancia D*, ¿qué rangos de precios/costos mantienen la rentabilidad del negocio?"

**Pregunta que NO responde**:
> "¿Cuál es el valor marginal de aumentar la capacidad de un vehículo en una unidad?" (esto requeriría precios sombra)

---

### 10.1 Metodología del Análisis

**Flujo del análisis** (`app_vrp.py`, líneas 772-854):

```
1. Optimización con OR-Tools
   ↓
   D* = distancia óptima (en km)
   n = número de pedidos entregados

2. Cálculo de costos (función de D*)
   ├─ Costo de nafta = (D* / rendimiento) × precio_nafta
   └─ Costo de chofer = (D* / velocidad) × costo_chofer

3. Cálculo de ingresos (función de D* y n)
   ├─ Ingreso base = n × precio_base
   └─ Ingreso variable = D* × precio_por_km

4. Cálculo de margen
   └─ Margen = Ingresos - Costos

5. Análisis de break-even (para cada parámetro económico)
   └─ ¿Qué valor hace que Margen = 0?
```

**Integración con AnalizadorSensibilidad** (`app_vrp.py`, líneas 779-790):
```python
analizador = AnalizadorSensibilidad(
    distancia_total_km=distancia_total_km,  # D* (fijo)
    num_rutas=len(all_routes),
    num_pedidos=num_pedidos,  # n (fijo)
    distancias_por_ruta=distancias_por_ruta,
    precio_nafta=precio_nafta_sess,
    rendimiento_vehiculo=rendimiento_sess,
    precio_base_por_pedido=precio_base_sess,
    precio_por_km=precio_por_km_sess,
    costo_chofer_por_hora=costo_chofer_sess,
    velocidad_promedio_kmh=velocidad_sess
)
```

---

### 10.2 Modelo de Costos

#### Costo de Nafta

**Fórmula** (`analisis_sensibilidad.py`, líneas 63-70):
```
Costo_nafta_por_km = p_nafta / r_vehiculo    ($/km)

Costo_total_nafta = Costo_nafta_por_km × D*    ($)
```

**Ejemplo** (con valores por defecto):
- p_nafta = $1,000/L
- r_vehiculo = 10 km/L
- D* = 45.23 km (resultado de optimización)
- **Costo_nafta_por_km** = $1,000 / 10 = $100/km
- **Costo_total_nafta** = $100/km × 45.23 km = **$4,523**

---

#### Costo de Chofer

**Fórmula** (`analisis_sensibilidad.py`, líneas 72-79):
```
T_horas = D* / v_promedio    (horas)

Costo_total_chofer = c_chofer × T_horas    ($)
```

**Ejemplo**:
- D* = 45.23 km
- v_promedio = 30 km/h
- c_chofer = $2,000/h
- **T_horas** = 45.23 / 30 = 1.51 horas
- **Costo_total_chofer** = $2,000/h × 1.51 h = **$3,020**

---

#### Costo Total

**Fórmula** (`analisis_sensibilidad.py`, líneas 81-103):
```
C_total = Costo_total_nafta + Costo_total_chofer
```

**Ejemplo**: C_total = $4,523 + $3,020 = **$7,543**

**Implementación en UI** (`app_vrp.py`, líneas 800-805):
```python
st.metric(
    "💵 Costo Operativo",
    f"${costos['costo_total']:,.2f}",
    help=f"Nafta: ${costos['costo_total_nafta']:,.2f} + "
         f"Chofer: ${costos['costo_total_chofer']:,.2f} "
         f"({costos['tiempo_total_horas']:.1f}h)"
)
```

---

### 10.3 Modelo de Ingresos

#### Ingreso Base

**Fórmula** (`analisis_sensibilidad.py`, líneas 122-136):
```
I_base = n_pedidos × p_base    ($)
```

**Ejemplo**:
- n_pedidos = 20
- p_base = $2,000/pedido
- **I_base** = 20 × $2,000 = **$40,000**

---

#### Ingreso Variable

**Fórmula**:
```
I_variable = D* × p_km    ($)
```

**Ejemplo**:
- D* = 45.23 km
- p_km = $150/km
- **I_variable** = 45.23 × $150 = **$6,784.50**

---

#### Ingreso Total

**Fórmula**:
```
I_total = I_base + I_variable
```

**Ejemplo**: I_total = $40,000 + $6,784.50 = **$46,784.50**

**Implementación en UI** (`app_vrp.py`, líneas 807-812):
```python
st.metric(
    "💰 Ingreso Total",
    f"${ingresos['ingreso_total']:,.2f}",
    help=f"Base: ${ingresos['ingreso_base']:,.2f} + "
         f"Variable: ${ingresos['ingreso_variable']:,.2f}"
)
```

---

### 10.4 Margen de Ganancia

**Fórmula** (`analisis_sensibilidad.py`, líneas 153-180):
```
M_total = I_total - C_total

Rentabilidad (%) = (M_total / I_total) × 100
```

**Ejemplo**:
- I_total = $46,784.50
- C_total = $7,543
- **M_total** = $46,784.50 - $7,543 = **$39,241.50**
- **Rentabilidad** = ($39,241.50 / $46,784.50) × 100 = **83.9%**

**Implementación en UI** (`app_vrp.py`, líneas 814-829):
```python
st.metric(
    "📊 Margen Neto",
    f"${margen['margen_total']:,.2f}",
    delta=f"{margen['rentabilidad_porcentaje']:+.1f}%",
    delta_color="normal" if margen['margen_total'] >= 0 else "inverse"
)

st.metric(
    "📈 Rentabilidad",
    f"{margen['rentabilidad_porcentaje']:.1f}%"
)
```

---

### 10.5 Análisis de Break-Even: Precio de Nafta

**Objetivo**: Determinar el precio máximo de nafta que mantiene margen ≥ 0.

**Fórmula algebraica** (`analisis_sensibilidad.py`, líneas 200-225):

En el punto de equilibrio (margen = 0):
```
I_total = C_total
I_total = C_nafta + C_chofer
I_total = (p_nafta_BE / r_vehiculo) × D* + C_chofer_actual
```

Despejando p_nafta_BE:
```
p_nafta_BE = ((I_total - C_chofer_actual) × r_vehiculo) / D*
```

**Implementación**:
```python
if self.distancia_total_km > 0:
    precio_nafta_breakeven = (
        (ingresos['ingreso_total'] - costos['costo_total_chofer'])
        * self.rendimiento_vehiculo
    ) / self.distancia_total_km
    precio_nafta_breakeven = max(0, precio_nafta_breakeven)
```

**Aumento permitido**:
```
Δp_nafta = p_nafta_BE - p_nafta_actual

Δp_nafta (%) = (Δp_nafta / p_nafta_actual) × 100
```

**Rangos de viabilidad**:
```
Límite inferior: $0/L (no puede ser negativo)
Límite superior: p_nafta_BE (para mantener rentabilidad)
Rango viable: [0, p_nafta_BE]
```

**Ejemplo**:
- I_total = $46,784.50
- C_chofer = $3,020
- r_vehiculo = 10 km/L
- D* = 45.23 km
- **p_nafta_BE** = (($46,784.50 - $3,020) × 10) / 45.23 = **$9,674.88/L**
- p_nafta_actual = $1,000/L
- **Aumento permitido** = $9,674.88 - $1,000 = **$8,674.88/L** (+867.5%)

---

### 10.6 Análisis de Break-Even: Costo del Chofer

**Objetivo**: Determinar el costo máximo del chofer que mantiene margen ≥ 0.

**Fórmula algebraica** (`analisis_sensibilidad.py`, líneas 317-362):

En el punto de equilibrio:
```
I_total = C_nafta_actual + (c_chofer_BE × T_horas)

c_chofer_BE = (I_total - C_nafta_actual) / T_horas
```

**Implementación**:
```python
tiempo_total_horas = self.calcular_tiempo_total_horas()

if tiempo_total_horas > 0:
    costo_chofer_breakeven = (
        ingresos['ingreso_total'] - costos['costo_total_nafta']
    ) / tiempo_total_horas
    costo_chofer_breakeven = max(0, costo_chofer_breakeven)
```

**Rangos de viabilidad**:
```
Límite inferior: $0/h
Límite superior: c_chofer_BE
Rango viable: [0, c_chofer_BE]
```

**Ejemplo**:
- I_total = $46,784.50
- C_nafta = $4,523
- T_horas = 1.51 h
- **c_chofer_BE** = ($46,784.50 - $4,523) / 1.51 = **$27,987.42/h**
- c_chofer_actual = $2,000/h
- **Aumento permitido** = $27,987.42 - $2,000 = **$25,987.42/h** (+1,299.4%)

---

### 10.7 Análisis de Break-Even: Precio Base por Pedido

**Objetivo**: Determinar el precio base mínimo que mantiene margen ≥ 0.

**Fórmula algebraica** (`analisis_sensibilidad.py`, líneas 227-270):

En el punto de equilibrio:
```
(p_base_BE × n_pedidos) + (p_km × D*) = C_total

p_base_BE = (C_total - (p_km × D*)) / n_pedidos
```

**Implementación**:
```python
if self.num_pedidos > 0:
    precio_base_breakeven = (
        costos['costo_total'] - (self.precio_por_km * self.distancia_total_km)
    ) / self.num_pedidos
    precio_base_breakeven = max(0, precio_base_breakeven)
```

**Margen disponible**:
```
Δp_base = p_base_actual - p_base_BE    (cuánto puede BAJAR)

Δp_base (%) = (Δp_base / p_base_actual) × 100
```

**Rangos de viabilidad**:
```
Límite inferior: p_base_BE (mínimo para no perder)
Límite superior: ∞ (sin límite)
Rango viable: [p_base_BE, ∞)
```

**Ejemplo**:
- C_total = $7,543
- p_km = $150/km
- D* = 45.23 km
- n_pedidos = 20
- **p_base_BE** = ($7,543 - ($150 × 45.23)) / 20 = **$38.65/pedido**
- p_base_actual = $2,000/pedido
- **Margen disponible** = $2,000 - $38.65 = **$1,961.35/pedido** (-98.1%)

**Interpretación**: El precio base puede bajar hasta $38.65/pedido y aún ser rentable, gracias al ingreso por kilómetro.

---

### 10.8 Análisis de Break-Even: Precio por Kilómetro

**Objetivo**: Determinar el precio por km mínimo que mantiene margen ≥ 0.

**Fórmula algebraica** (`analisis_sensibilidad.py`, líneas 272-315):

En el punto de equilibrio:
```
(p_base × n_pedidos) + (p_km_BE × D*) = C_total

p_km_BE = (C_total - (p_base × n_pedidos)) / D*
```

**Implementación**:
```python
if self.distancia_total_km > 0:
    precio_por_km_breakeven = (
        costos['costo_total'] - (self.precio_base_por_pedido * self.num_pedidos)
    ) / self.distancia_total_km
    precio_por_km_breakeven = max(0, precio_por_km_breakeven)
```

**Rangos de viabilidad**:
```
Límite inferior: p_km_BE (mínimo para no perder)
Límite superior: ∞ (sin límite)
Rango viable: [p_km_BE, ∞)
```

**Ejemplo**:
- C_total = $7,543
- p_base = $2,000/pedido
- n_pedidos = 20
- D* = 45.23 km
- **p_km_BE** = ($7,543 - ($2,000 × 20)) / 45.23 = **-$716.89/km**
- p_km_actual = $150/km
- **Margen disponible** = $150 - (-$716.89) = **$866.89/km** (-577.9%)

**Interpretación**: El ingreso base ($40,000) ya cubre todos los costos ($7,543). El precio por km puede ser incluso negativo (descuento) y aún ser rentable.

---

### 10.9 Tabla de Análisis Económico

**Generación** (`analisis_sensibilidad.py`, líneas 381-434):
```python
def generar_tabla_lingo(self) -> pd.DataFrame:
    # Genera DataFrame con análisis de todos los parámetros
```

**Visualización en UI** (`app_vrp.py`, líneas 834-836):
```python
tabla_lingo = analizador.generar_tabla_lingo()
st.dataframe(tabla_lingo, use_container_width=True, hide_index=True)
```

**Formato de la tabla**:

| Variable | Valor Actual | Costo/Ingreso Parcial | Precio Mínimo | Precio Máximo | Margen de Variación |
|----------|--------------|----------------------|---------------|---------------|---------------------|
| Precio Nafta ($/L) | $1,000.00 | Costo: $4,523.00 | $0.00 | $9,674.88 | +$8,674.88 (+867.5%) |
| Costo Chofer ($/h) | $2,000.00 | Costo: $3,020.00 | $0.00 | $27,987.42 | +$25,987.42 (+1,299.4%) |
| Precio Base ($/pedido) | $2,000.00 | Ingreso: $40,000.00 | $38.65 | ∞ | -$1,961.35 (-98.1%) |
| Precio por km ($/km) | $150.00 | Ingreso: $6,784.50 | -$716.89 | ∞ | -$866.89 (-577.9%) |

**Nota sobre el nombre**: Aunque se llama "tabla_lingo", NO es generada por LINGO ni contiene precios sombra/costos reducidos. Es solo un formato similar para presentación visual.

---

### 10.10 Interpretaciones Automáticas

**Generación** (`analisis_sensibilidad.py`, líneas 436-554):
```python
def obtener_interpretaciones(self) -> List[str]:
    # Genera interpretaciones en lenguaje natural
```

**Visualización en UI** (`app_vrp.py`, líneas 838-851):
```python
interpretaciones = analizador.obtener_interpretaciones()

for interpretacion in interpretaciones:
    if interpretacion.startswith("✓"):
        st.success(interpretacion)
    elif interpretacion.startswith("⚠"):
        st.warning(interpretacion)
    elif interpretacion.startswith("✗"):
        st.error(interpretacion)
    else:
        st.info(interpretacion)
```

**Tipos de interpretaciones**:

1. **Rentabilidad general**:
   - ✓ Operación rentable (margen > 0)
   - ⚠ Punto de equilibrio (margen = 0)
   - ✗ Operación con pérdida (margen < 0)

2. **Composición financiera**:
   - 💵 Detalle de ingresos (base + variable)
   - 💰 Detalle de costos (nafta + chofer)

3. **Análisis por parámetro**:
   - ⛽ Precio de nafta: rango viable
   - 🚗 Costo de chofer: rango viable
   - 📦 Precio base: mínimo requerido
   - 📏 Precio por km: mínimo requerido

**Ejemplo de interpretaciones**:

```
✓ La operación es RENTABLE con un margen de $39,241.50 (83.9% de rentabilidad)

💵 Composición de Ingresos: Base $40,000.00 (20 pedidos × $2,000.00) +
   Variable $6,784.50 (45.2 km × $150.00/km)

💰 Composición de Costos: Nafta $4,523.00 + Chofer $3,020.00 (1.5h × $2,000.00/h)

⛽ Precio Nafta: Puede aumentar hasta $8,674.88/L más (+867.5%) sin generar
   pérdidas. Rango: $0.00/L - $9,674.88/L

📦 Precio Base por Pedido: El ingreso por precio por km ($6,784.50) ya cubre
   todos los costos ($7,543.00). Podrías bajar el precio base hasta $38.65 y
   aún ser rentable. Margen disponible: $1,961.35/pedido (98.1%)
```

---

### 10.11 Limitaciones del Análisis Económico

**Importante entender**:

1. **Asume la distancia óptima como fija**:
   - El análisis NO recalcula rutas al cambiar parámetros económicos
   - Si cambias el precio de nafta, la ruta sigue siendo la misma
   - Solo analiza si esa ruta es económicamente viable

2. **No analiza sensibilidad del modelo de optimización**:
   - No dice "¿qué pasa si aumento la capacidad de un vehículo?"
   - No dice "¿cuál es el valor de agregar un pedido más?"
   - No proporciona precios sombra de restricciones

3. **Es análisis de negocio, no de optimización**:
   - Pregunta empresarial: "¿A qué precios puedo operar?"
   - NO pregunta matemática: "¿Cuál es el valor dual de la restricción de capacidad?"

4. **Los parámetros económicos son externos al modelo VRP**:
   - El modelo VRP minimiza distancia, no maximiza ganancia
   - Los costos/ingresos se calculan después de la optimización
   - No afectan la decisión de qué rutas tomar

---

## 11. Implementación

### Archivo Principal

**`app_vrp.py`** (961 líneas)

Aplicación web Streamlit que implementa:
- Interfaz de usuario con 3 columnas
- Configuración de parámetros (depósito, flota, economía, pedidos)
- Optimización con OR-Tools (función `optimizar_rutas_vrp`)
- Visualización con Folium (función `crear_mapa_folium`)
- Análisis económico post-optimización
- Métricas y reportes

---

### Estructura de la Aplicación

#### Configuración (Columna Izquierda)

**Sección Depósito** (líneas 446-473):
- Selector de ubicación predefinida o personalizada
- Input de coordenadas (latitud, longitud)
- Validación de rangos

**Sección Flota** (líneas 477-481):
- Slider: Cantidad de camiones (1-5)
- Slider: Capacidad por camión (5-15)

**Sección Parámetros Económicos** (líneas 485-544):
- 6 inputs numéricos con valores por defecto
- Tooltips explicativos

**Sección Pedidos** (líneas 548-617):
- Tab 1: Subir CSV (con validaciones)
- Tab 2: Generar aleatorios dentro de CABA
- Contador de pedidos cargados
- Validación de capacidad total

**Botón Optimizar** (líneas 630-684):
- Deshabilitado si no hay pedidos
- Crea lista de ubicaciones: [DEPOT] + orders
- Calcula matriz de distancias (con spinner)
- Ejecuta optimización (con spinner, 30s)
- Guarda resultados en session_state
- Recarga la aplicación

---

#### Visualización (Columna Central)

**Mapa Interactivo** (líneas 690-749):
- Selector de vista (por camión o general)
- Mapa Folium con rutas reales (OSRM)
- Colores por vehículo
- Marcadores interactivos
- Polígonos de barrios de fondo

**Análisis Económico** (líneas 751-854):
- 4 métricas principales en columnas
- Tabla de análisis de sensibilidad
- Interpretaciones automáticas con íconos

---

#### Órdenes y Métricas (Columna Derecha)

**Detalle de Ruta** (líneas 860-912):
- Selector de camión
- Lista de paradas con coordenadas
- Identificación de depot vs pedidos

**Métricas de Ruta** (líneas 915-930):
- Distancia del camión seleccionado
- Paquetes transportados vs capacidad

**Métricas Generales** (líneas 934-950):
- Distancia total de la flota
- Total de paquetes
- Camiones utilizados / disponibles
- Utilización de flota (%)
- Tiempo de optimización

---

### Función Principal de Optimización

**`optimizar_rutas_vrp()`** (líneas 207-307)

**Entrada**:
- `all_locations`: Lista [depot] + [orders]
- `num_vehicles`: Número de camiones (K)
- `vehicle_capacity`: Capacidad por camión (Q)
- `distance_matrix`: Matriz NxN en metros

**Proceso**:
1. Crear diccionario `data` con parámetros del modelo
2. Instanciar RoutingIndexManager
3. Instanciar RoutingModel
4. Registrar callback de distancia
5. Registrar callback de demanda
6. Agregar dimensión de capacidad
7. Configurar parámetros de búsqueda
8. Resolver con `SolveWithParameters()`
9. Extraer rutas para cada vehículo

**Salida**:
- `solution`: Objeto solución de OR-Tools
- `routing`: Modelo de routing
- `manager`: Manager de índices
- `data`: Diccionario de datos
- `all_routes`: Lista de diccionarios con información de cada ruta:
  ```python
  {
      'vehicle': 1,           # ID del vehículo
      'distance': 15230,      # Distancia en metros
      'packages': 12,         # Paquetes transportados
      'nodes': [0, 5, 12, 3, 0]  # Secuencia de nodos
  }
  ```

**Retorno en caso de fallo**:
```python
return None, None, None, None, None
```

---

### Integración con Análisis Económico

**Creación del analizador** (`app_vrp.py`, líneas 779-790):
```python
from analisis_sensibilidad import AnalizadorSensibilidad

analizador = AnalizadorSensibilidad(
    distancia_total_km=distancia_total_km,  # D* ya calculada
    num_rutas=len(all_routes),
    num_pedidos=num_pedidos,  # n ya conocido
    distancias_por_ruta=distancias_por_ruta,
    # Parámetros económicos desde session_state
    precio_nafta=precio_nafta_sess,
    rendimiento_vehiculo=rendimiento_sess,
    precio_base_por_pedido=precio_base_sess,
    precio_por_km=precio_por_km_sess,
    costo_chofer_por_hora=costo_chofer_sess,
    velocidad_promedio_kmh=velocidad_sess
)
```

**Cálculos** (líneas 792-795):
```python
costos = analizador.calcular_costos_operacion()  # Diccionario con costos
ingresos = analizador.calcular_ingresos()  # Diccionario con ingresos
margen = analizador.calcular_margen()  # Diccionario con margen y rentabilidad
```

**Presentación de resultados** (líneas 797-851):
- Métricas en columnas (st.metric)
- Tabla de sensibilidad (st.dataframe)
- Interpretaciones con formato condicional (st.success/warning/error/info)

---

### Generación de Pedidos Aleatorios

**Función `generate_random_deliveries_in_caba()`** (líneas 59-99)

**Algoritmo**:
1. Obtener bounding box del polígono de CABA
2. Generar coordenadas aleatorias uniformes dentro del bounding box
3. Verificar si el punto está dentro del polígono de CABA (usando shapely)
4. Si está dentro, agregar a la lista de pedidos
5. Repetir hasta generar n pedidos (máx. 100n intentos)

**Validación geográfica**:
```python
point = Point(random_lon, random_lat)
if caba_polygon.contains(point):
    # Punto válido dentro de CABA
```

**Estructura de pedido**:
```python
order = {
    'order_id': len(orders) + 1,
    'lat': random_lat,
    'lon': random_lon,
    'type': 'order'
}
```

---

### Cache y Persistencia

**Session State de Streamlit**:

Almacena entre reruns:
```python
st.session_state = {
    'solution': solution,  # Solución de OR-Tools
    'routing': routing,  # Modelo de routing
    'manager': manager,  # Manager de índices
    'data': data,  # Diccionario de datos
    'all_routes': all_routes,  # Rutas calculadas
    'all_locations': all_locations,  # Ubicaciones
    'distance_matrix': distance_matrix,  # Matriz de distancias
    'optimization_time': elapsed_time,  # Tiempo de optimización
    'generated_orders': orders,  # Pedidos generados
    # Parámetros económicos
    'precio_nafta': precio_nafta,
    'rendimiento_vehiculo': rendimiento_vehiculo,
    'precio_base_por_pedido': precio_base_por_pedido,
    'precio_por_km': precio_por_km,
    'costo_chofer_por_hora': costo_chofer_por_hora,
    'velocidad_promedio_kmh': velocidad_promedio_kmh
}
```

**Cache de matrices de distancias**:
- Archivos: `vrp_streamlit_{n}.npz`
- Formato: NumPy compressed
- Contenido: Matriz NxN de distancias en metros

**Cache de datos geodésicos**:
```python
@st.cache_data
def cargar_barrios_caba():
    # Se ejecuta solo una vez y se cachea
```

---

### Dependencias

**Librerías principales** (líneas 6-20):
```python
import streamlit as st           # Interfaz web
import pandas as pd              # Datos tabulares
import numpy as np               # Operaciones numéricas
import geopandas as gpd          # Datos geoespaciales
from shapely import wkt          # Geometrías
from shapely.geometry import Point  # Puntos geográficos
import requests                  # Llamadas HTTP (OSRM)
import polyline                  # Decodificación de rutas
import folium                    # Mapas interactivos
from streamlit_folium import st_folium  # Integración Folium-Streamlit
from ortools.constraint_solver import routing_enums_pb2  # Enumeraciones OR-Tools
from ortools.constraint_solver import pywrapcp  # Solver de constraint programming
import os                        # Sistema operativo
import time                      # Medición de tiempo
from analisis_sensibilidad import AnalizadorSensibilidad  # Análisis económico
```

**Versiones requeridas** (desde `requirements.txt`):
```
ortools>=9.7.0
streamlit>=1.28.0
pandas>=2.0.0
numpy>=1.24.0
geopandas>=0.14.0
folium>=0.14.0
streamlit-folium>=0.15.0
requests>=2.31.0
polyline>=2.0.0
shapely>=2.0.0
```

---

## Referencias

### Bibliografía Académica

1. **Toth, P., & Vigo, D. (2014)**. *Vehicle Routing: Problems, Methods, and Applications* (2nd ed.). SIAM.

2. **Laporte, G. (2009)**. Fifty years of vehicle routing. *Transportation Science*, 43(4), 408-416.

3. **Voudouris, C., & Tsang, E. (1999)**. Guided local search and its application to the traveling salesman problem. *European Journal of Operational Research*, 113(2), 469-499.

### Herramientas y Documentación

4. **Google OR-Tools Documentation** (2024). *Vehicle Routing Problem*.
   https://developers.google.com/optimization/routing

5. **OpenStreetMap Wiki** (2024). *Routing*.
   https://wiki.openstreetmap.org/wiki/Routing

6. **OSRM Project** (2024). *Open Source Routing Machine - API Documentation*.
   http://project-osrm.org/docs/v5.24.0/api/

7. **Streamlit Documentation** (2024). *Build data apps in Python*.
   https://docs.streamlit.io/

### Bibliotecas Utilizadas

8. **OR-Tools**: https://github.com/google/or-tools
9. **Streamlit**: https://streamlit.io/
10. **Folium**: https://python-visualization.github.io/folium/
11. **GeoPandas**: https://geopandas.org/
12. **Shapely**: https://shapely.readthedocs.io/

### Datos Geográficos

13. **OpenStreetMap**: https://www.openstreetmap.org/
14. **Buenos Aires Data**: https://data.buenosaires.gob.ar/

---

## Notas Finales

### Resumen del Modelo

Este documento describe la implementación de un **Capacitated Vehicle Routing Problem (CVRP)** para distribución urbana en CABA, con las siguientes características:

**Modelo de optimización**:
- Función objetivo: Minimizar distancia total
- Restricción principal: Capacidad de vehículos
- Solver: Google OR-Tools (Constraint Programming + Metaheurísticas)
- Tiempo de ejecución: 30 segundos
- Calidad de solución: 90-98% del óptimo

**Análisis económico post-optimización**:
- Cálculo de costos operativos (nafta + chofer)
- Cálculo de ingresos (base + variable por km)
- Análisis de break-even para 4 parámetros económicos
- **Importante**: No son precios sombra ni costos reducidos

**Implementación**:
- Aplicación web interactiva con Streamlit
- Distancias reales calculadas con OSRM API
- Visualización con mapas interactivos (Folium)
- Configuración flexible de parámetros
- Generación automática de pedidos en CABA

### Diferencias con Programación Lineal Clásica

| Aspecto | LP Clásico (Simplex) | Este Proyecto (OR-Tools) |
|---------|---------------------|-------------------------|
| Tipo de problema | LP (Lineal) | CVRP (NP-Hard) |
| Método de solución | Simplex | Metaheurísticas (GLS) |
| Garantía de optimalidad | ✅ Sí | ❌ No (90-98%) |
| Precios sombra | ✅ Automáticos | ❌ No disponibles |
| Costos reducidos | ✅ Automáticos | ❌ No disponibles |
| Análisis de sensibilidad | ✅ Del modelo | ❌ Solo económico |
| Tiempo de ejecución | Variable (puede ser largo) | 30 segundos (fijo) |
| Escalabilidad | Limitada para problemas grandes | Buena (hasta 50 pedidos) |

### Aplicabilidad

**Este proyecto es adecuado para**:
- Planificación operativa de distribución urbana
- Análisis de viabilidad económica de servicios de entrega
- Optimización de rutas en tiempo real (30 segundos)
- Escenarios con 5-50 pedidos y 1-5 vehículos
- Contexto urbano con distancias reales (calles)

**Este proyecto NO es adecuado para**:
- Certificación matemática de optimalidad
- Obtención de precios sombra o valores marginales
- Análisis de sensibilidad del modelo de optimización
- Problemas con más de 50 pedidos (tiempo de cálculo)
- Contexto donde se requiere 100% de optimalidad garantizada

### Honestidad Metodológica

Es fundamental entender que:

1. **El análisis económico NO es análisis de sensibilidad clásico**
   - No proviene del solver
   - Se calcula manualmente con fórmulas algebraicas
   - Asume la solución de optimización como fija

2. **OR-Tools no proporciona información dual**
   - No hay precios sombra de restricciones
   - No hay costos reducidos de variables
   - No hay rangos de sensibilidad de coeficientes

3. **La solución es casi óptima, no óptima**
   - Calidad típica: 90-98% del óptimo global
   - Suficiente para aplicaciones prácticas
   - No suficiente para demostraciones matemáticas rigurosas

Esta claridad metodológica es esencial para el uso académico y profesional correcto del proyecto.

---

**Última actualización**: 2025-11-17

**Basado en**: `app_vrp.py` (implementación final)

**Institución**: Universidad Católica Argentina (UCA)

**Materia**: Optimización

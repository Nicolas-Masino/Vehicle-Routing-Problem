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
9. [Parámetros Económicos](#9-parámetros-económicos)
10. [Análisis de Sensibilidad](#10-análisis-de-sensibilidad)
11. [Método de Solución](#11-método-de-solución)
12. [Archivos de Implementación](#12-archivos-de-implementación)

---

## 1. Descripción del Problema

Este proyecto implementa un **Problema de Ruteo de Vehículos Capacitado (CVRP - Capacitated Vehicle Routing Problem)** para optimizar la distribución de pedidos en la Ciudad Autónoma de Buenos Aires (CABA).

### Características del Problema

- **Tipo**: CVRP (Capacitated Vehicle Routing Problem)
- **Variante implementada**: VRP con capacidad y depósito único
- **Contexto**: Distribución de última milla para empresa de logística
- **Ubicación**: Ciudad Autónoma de Buenos Aires (CABA), Argentina
- **Objetivo principal**: Minimizar la distancia total recorrida por la flota
- **Objetivo secundario**: Maximizar la rentabilidad económica de la operación

### Variantes Implementadas

El proyecto incluye dos formulaciones:

1. **TSP Simple** (`optimizador_rutas.py`):
   - Un solo vehículo sin restricción de capacidad
   - Todos los pedidos deben ser visitados

2. **CVRP Completo** (`app_vrp.py`):
   - Múltiples vehículos con restricciones de capacidad
   - Cada vehículo tiene capacidad limitada de paquetes

---

## 2. Objetivo del Modelo

El modelo busca determinar las rutas óptimas para una flota de vehículos que deben:

- Partir desde un centro de distribución (depot)
- Visitar un conjunto de clientes para entregar pedidos
- Regresar al centro de distribución
- Minimizar la distancia total recorrida por todos los vehículos
- Respetar las restricciones de capacidad de cada vehículo
- Garantizar que cada cliente sea visitado exactamente una vez

---

## 3. Conjuntos e Índices

### Conjuntos

- **N**: Conjunto de todos los nodos (locaciones)
  - N = {0, 1, 2, ..., n}
  - n = número total de pedidos

- **C**: Conjunto de clientes (pedidos)
  - C = {1, 2, ..., n}
  - C ⊂ N

- **V**: Conjunto de vehículos (camiones)
  - V = {1, 2, ..., K}
  - K = número de vehículos disponibles

- **A**: Conjunto de arcos
  - A = {(i, j) : i, j ∈ N, i ≠ j}

### Índices

- **i, j**: Índices de nodos (i, j ∈ N)
- **k**: Índice de vehículo (k ∈ V)
- **0**: Índice del depósito (depot)

---

## 4. Parámetros

### Parámetros de Distancia

- **d<sub>ij</sub>**: Distancia en metros del nodo i al nodo j
  - Calculada mediante OSRM API (distancia real en calles)
  - Fallback a distancia euclidiana si OSRM falla
  - Convertida a enteros para OR-Tools: d<sub>ij</sub> = distancia_km × 1000

### Parámetros de Demanda

- **q<sub>i</sub>**: Demanda del cliente i (número de paquetes)
  - q<sub>0</sub> = 0 (el depósito no tiene demanda)
  - q<sub>i</sub> = 1 para todo i ∈ C (cada pedido = 1 paquete)

### Parámetros de Capacidad

- **Q<sub>k</sub>**: Capacidad máxima del vehículo k (número de paquetes)
  - Configurable en la UI: entre 5 y 15 paquetes
  - Por defecto: Q<sub>k</sub> = 15 para todo k ∈ V

### Parámetros de Flota

- **K**: Número de vehículos disponibles
  - Configurable en la UI: entre 1 y 5 vehículos
  - Por defecto: K = 3

### Parámetros Económicos

#### Parámetros de Costo

- **p<sub>nafta</sub>**: Precio de nafta por litro ($/L)
  - Por defecto: $1,000.00/L

- **r<sub>vehiculo</sub>**: Rendimiento del vehículo (km/L)
  - Por defecto: 10.0 km/L

- **v<sub>promedio</sub>**: Velocidad promedio (km/h)
  - Por defecto: 30.0 km/h

- **c<sub>chofer</sub>**: Costo del chofer por hora ($/h)
  - Por defecto: $2,000.00/h

#### Parámetros de Ingreso

- **p<sub>base</sub>**: Precio base por pedido entregado ($)
  - Por defecto: $2,000.00/pedido

- **p<sub>km</sub>**: Precio variable por kilómetro ($/km)
  - Por defecto: $150.00/km

### Parámetros Geográficos

- **lat<sub>i</sub>**: Latitud del nodo i (-90° a 90°)
- **lon<sub>i</sub>**: Longitud del nodo i (-180° a 180°)
- **comuna<sub>i</sub>**: Comuna de CABA donde se ubica el nodo i (1-15)

### Parámetros de Optimización

- **t<sub>max</sub>**: Tiempo límite de búsqueda
  - Por defecto: 30 segundos

- **estrategia<sub>inicial</sub>**: PATH_CHEAPEST_ARC
  - Construye la solución inicial agregando el arco más barato

- **metaheurística</sub>**: GUIDED_LOCAL_SEARCH
  - Algoritmo de búsqueda local guiada para escapar de óptimos locales

---

## 5. Variables de Decisión

### Variables Binarias

**x<sub>ijk</sub>** ∈ {0, 1} para todo i, j ∈ N, k ∈ V

- x<sub>ijk</sub> = 1 si el vehículo k viaja directamente del nodo i al nodo j
- x<sub>ijk</sub> = 0 en caso contrario

### Variables Auxiliares (implícitas en OR-Tools)

**y<sub>ik</sub>** ∈ {0, 1} para todo i ∈ C, k ∈ V

- y<sub>ik</sub> = 1 si el cliente i es atendido por el vehículo k
- y<sub>ik</sub> = 0 en caso contrario

**u<sub>ik</sub>** ≥ 0 para todo i ∈ N, k ∈ V

- u<sub>ik</sub> = carga acumulada del vehículo k al visitar el nodo i
- Usada para verificar la restricción de capacidad

---

## 6. Función Objetivo

### Objetivo: Minimizar Distancia Total

```
Minimizar Z = Σ Σ Σ d_ij × x_ijk
              k∈V i∈N j∈N
```

**Significado**: Minimizar la suma de las distancias de todos los arcos recorridos por todos los vehículos.

### Métricas Derivadas

Una vez resuelta la optimización, se calculan:

#### Costo Total de Operación

```
C_total = C_nafta + C_chofer

donde:
C_nafta = (D_total / r_vehiculo) × p_nafta
C_chofer = (D_total / v_promedio) × c_chofer
```

Siendo D_total la distancia total óptima en km.

#### Ingreso Total

```
I_total = I_base + I_variable

donde:
I_base = n_pedidos × p_base
I_variable = D_total × p_km
```

#### Margen de Ganancia

```
M_total = I_total - C_total

Rentabilidad (%) = (M_total / I_total) × 100
```

---

## 7. Restricciones

### R1. Cada Cliente Visitado Exactamente Una Vez

```
Σ Σ x_ijk = 1    ∀i ∈ C
k∈V j∈N
```

**Significado**: Cada pedido debe ser entregado por exactamente un vehículo.

**Implementación**: Implícita en OR-Tools RoutingModel.

---

### R2. Conservación de Flujo

```
Σ x_ijk = Σ x_jik    ∀j ∈ N, ∀k ∈ V
i∈N       i∈N
```

**Significado**: Si un vehículo llega a un nodo, debe salir de ese nodo (conservación de flujo).

**Implementación**: Implícita en OR-Tools RoutingModel.

---

### R3. Restricción de Capacidad

```
Σ q_i × y_ik ≤ Q_k    ∀k ∈ V
i∈C
```

**Significado**: La suma de las demandas de los clientes atendidos por el vehículo k no puede exceder su capacidad.

**Implementación en código**:
```python
# app_vrp.py, líneas 254-260
routing.AddDimensionWithVehicleCapacity(
    demand_callback_index,
    0,  # null capacity slack (sin holgura)
    data['vehicle_capacities'],  # [Q_1, Q_2, ..., Q_K]
    True,  # start cumul to zero
    'Capacity'
)
```

---

### R4. Cada Vehículo Sale del Depósito

```
Σ x_0jk ≤ 1    ∀k ∈ V
j∈C
```

**Significado**: Cada vehículo puede salir del depósito como máximo una vez (puede no usarse).

**Implementación**: Implícita en OR-Tools al definir el depot.

---

### R5. Cada Vehículo Regresa al Depósito

```
Σ x_i0k ≤ 1    ∀k ∈ V
i∈C
```

**Significado**: Si un vehículo sale del depósito, debe regresar al depósito.

**Implementación**: Implícita en OR-Tools.

---

### R6. Consistencia de Salida y Regreso

```
Σ x_0jk = Σ x_i0k    ∀k ∈ V
j∈C       i∈C
```

**Significado**: Un vehículo solo puede regresar si salió del depósito.

**Implementación**: Implícita en OR-Tools.

---

### R7. Restricción de Validación de Pedidos

```
Σ q_i ≤ Σ Q_k
i∈C     k∈V
```

**Significado**: La demanda total no puede exceder la capacidad total de la flota.

**Implementación en código**:
```python
# app_vrp.py, líneas 622-626
total_capacity = num_vehicles * vehicle_capacity
if len(orders) > total_capacity:
    st.error(f"Total de pedidos ({len(orders)}) excede la capacidad total ({total_capacity})")
    st.stop()
```

---

### R8. Validación de Coordenadas

```
-90 ≤ lat_i ≤ 90    ∀i ∈ N
-180 ≤ lon_i ≤ 180  ∀i ∈ N
```

**Implementación en código**:
```python
# app_vrp.py, líneas 568-571
if not df_pedidos['lat'].between(-90, 90).all():
    st.error("Latitudes fuera de rango (-90, 90)")
elif not df_pedidos['lon'].between(-180, 180).all():
    st.error("Longitudes fuera de rango (-180, 180)")
```

---

## 8. Formulación Matemática Completa

### Modelo CVRP Completo

```
Minimizar:
    Z = Σ Σ Σ d_ij × x_ijk
        k∈V i∈N j∈N

Sujeto a:

(1) Visita única:
    Σ Σ x_ijk = 1                           ∀i ∈ C
    k∈V j∈N

(2) Conservación de flujo:
    Σ x_ijk = Σ x_jik                       ∀j ∈ N, ∀k ∈ V
    i∈N       i∈N

(3) Capacidad del vehículo:
    Σ q_i × y_ik ≤ Q_k                      ∀k ∈ V
    i∈C

(4) Salida del depósito:
    Σ x_0jk ≤ 1                             ∀k ∈ V
    j∈C

(5) Regreso al depósito:
    Σ x_i0k ≤ 1                             ∀k ∈ V
    i∈C

(6) Consistencia de ruta:
    Σ x_0jk = Σ x_i0k                       ∀k ∈ V
    j∈C       i∈C

(7) Relación entre x e y:
    y_ik = Σ x_ijk                          ∀i ∈ C, ∀k ∈ V
           j∈N

(8) Variables binarias:
    x_ijk ∈ {0, 1}                          ∀i,j ∈ N, ∀k ∈ V
    y_ik ∈ {0, 1}                           ∀i ∈ C, ∀k ∈ V

(9) Variables no negativas:
    u_ik ≥ 0                                ∀i ∈ N, ∀k ∈ V
```

### Modelo TSP Simple (Caso K=1, sin restricción de capacidad)

```
Minimizar:
    Z = Σ Σ d_ij × x_ij
        i∈N j∈N

Sujeto a:

(1) Cada nodo visitado una vez:
    Σ x_ij = 1                              ∀j ∈ N, j ≠ 0
    i∈N

(2) Salida de cada nodo:
    Σ x_ij = 1                              ∀i ∈ N, i ≠ 0
    j∈N

(3) Inicio y fin en depot:
    El nodo 0 es el depot (inicio y fin)

(4) Variables binarias:
    x_ij ∈ {0, 1}                           ∀i,j ∈ N
```

---

## 9. Parámetros Económicos

### Modelo de Costos

#### Costo de Nafta

```
Costo_nafta_por_km = p_nafta / r_vehiculo    ($/km)

Costo_total_nafta = Costo_nafta_por_km × D_total    ($)
```

**Ejemplo**:
- p_nafta = $1,000/L
- r_vehiculo = 10 km/L
- D_total = 45.23 km
- Costo_nafta_por_km = $100/km
- Costo_total_nafta = $4,523

#### Costo de Chofer

```
T_horas = D_total / v_promedio    (horas)

Costo_total_chofer = c_chofer × T_horas    ($)
```

**Ejemplo**:
- D_total = 45.23 km
- v_promedio = 30 km/h
- c_chofer = $2,000/h
- T_horas = 1.51 horas
- Costo_total_chofer = $3,020

#### Costo Total

```
C_total = Costo_total_nafta + Costo_total_chofer
```

**Ejemplo**: C_total = $4,523 + $3,020 = $7,543

---

### Modelo de Ingresos

#### Ingreso Base

```
I_base = n_pedidos × p_base    ($)
```

**Ejemplo**:
- n_pedidos = 20
- p_base = $2,000/pedido
- I_base = $40,000

#### Ingreso Variable

```
I_variable = D_total × p_km    ($)
```

**Ejemplo**:
- D_total = 45.23 km
- p_km = $150/km
- I_variable = $6,784.50

#### Ingreso Total

```
I_total = I_base + I_variable
```

**Ejemplo**: I_total = $40,000 + $6,784.50 = $46,784.50

---

### Margen de Ganancia

```
M_total = I_total - C_total

Rentabilidad (%) = (M_total / I_total) × 100
```

**Ejemplo**:
- I_total = $46,784.50
- C_total = $7,543
- M_total = $39,241.50
- Rentabilidad = 83.9%

---

## 10. Análisis de Sensibilidad

El sistema implementa un análisis completo de sensibilidad económica para determinar los rangos viables de cada parámetro.

### 10.1 Sensibilidad del Precio de Nafta

**Objetivo**: Determinar cuánto puede aumentar el precio de nafta sin generar pérdidas.

#### Punto de Equilibrio (Break-even)

En el punto de equilibrio, el margen es cero:

```
I_total = C_total
I_total = C_nafta + C_chofer
I_total = (p_nafta_BE / r_vehiculo) × D_total + C_chofer
```

Despejando:

```
p_nafta_BE = ((I_total - C_chofer) × r_vehiculo) / D_total
```

#### Aumento Permitido

```
Δp_nafta = p_nafta_BE - p_nafta_actual

Δp_nafta (%) = (Δp_nafta / p_nafta_actual) × 100
```

#### Rangos de Viabilidad

```
Límite inferior: $0/L (no puede ser negativo)
Límite superior: p_nafta_BE (para no tener pérdidas)
Rango viable: [0, p_nafta_BE]
```

**Implementación**: `analisis_sensibilidad.py`, líneas 182-225

---

### 10.2 Sensibilidad del Costo del Chofer

**Objetivo**: Determinar cuánto puede aumentar el costo del chofer sin generar pérdidas.

#### Punto de Equilibrio

```
I_total = C_nafta + C_chofer
I_total = C_nafta + (c_chofer_BE × T_horas)

c_chofer_BE = (I_total - C_nafta) / T_horas
```

#### Aumento Permitido

```
Δc_chofer = c_chofer_BE - c_chofer_actual

Δc_chofer (%) = (Δc_chofer / c_chofer_actual) × 100
```

#### Rangos de Viabilidad

```
Límite inferior: $0/h
Límite superior: c_chofer_BE
Rango viable: [0, c_chofer_BE]
```

**Implementación**: `analisis_sensibilidad.py`, líneas 317-362

---

### 10.3 Sensibilidad del Precio Base por Pedido

**Objetivo**: Determinar el precio base mínimo para no tener pérdidas.

#### Punto de Equilibrio

```
I_total = C_total
(p_base_BE × n_pedidos) + (p_km × D_total) = C_total

p_base_BE = (C_total - (p_km × D_total)) / n_pedidos
```

#### Margen Disponible

```
Δp_base = p_base_actual - p_base_BE

Δp_base (%) = (Δp_base / p_base_actual) × 100
```

#### Rangos de Viabilidad

```
Límite inferior: p_base_BE (mínimo para no perder)
Límite superior: ∞ (sin límite)
Rango viable: [p_base_BE, ∞)
```

**Implementación**: `analisis_sensibilidad.py`, líneas 227-270

---

### 10.4 Sensibilidad del Precio por Kilómetro

**Objetivo**: Determinar el precio por km mínimo para no tener pérdidas.

#### Punto de Equilibrio

```
I_total = C_total
(p_base × n_pedidos) + (p_km_BE × D_total) = C_total

p_km_BE = (C_total - (p_base × n_pedidos)) / D_total
```

#### Margen Disponible

```
Δp_km = p_km_actual - p_km_BE

Δp_km (%) = (Δp_km / p_km_actual) × 100
```

#### Rangos de Viabilidad

```
Límite inferior: p_km_BE (mínimo para no perder)
Límite superior: ∞ (sin límite)
Rango viable: [p_km_BE, ∞)
```

**Implementación**: `analisis_sensibilidad.py`, líneas 272-315

---

### 10.5 Tabla de Sensibilidad Estilo LINGO

El sistema genera una tabla con formato similar a LINGO que resume todos los análisis:

| Variable | Valor Actual | Costo/Ingreso Parcial | Precio Mínimo | Precio Máximo | Margen de Variación |
|----------|--------------|----------------------|---------------|---------------|---------------------|
| Precio Nafta ($/L) | $1,000.00 | Costo: $4,523.00 | $0.00 | $9,385.67 | +$8,385.67 (+838.6%) |
| Costo Chofer ($/h) | $2,000.00 | Costo: $3,020.00 | $0.00 | $27,987.42 | +$25,987.42 (+1,299.4%) |
| Precio Base ($/pedido) | $2,000.00 | Ingreso: $40,000.00 | $38.65 | ∞ | -$1,961.35 (-98.1%) |
| Precio por km ($/km) | $150.00 | Ingreso: $6,784.50 | -$716.89 | ∞ | -$866.89 (-577.9%) |

**Interpretación de la tabla**:
- **Margen positivo en Precio Nafta**: Puede aumentar hasta $9,385.67/L sin pérdidas
- **Margen positivo en Costo Chofer**: Puede aumentar hasta $27,987.42/h sin pérdidas
- **Margen negativo en Precio Base**: Puede bajar hasta $38.65/pedido sin pérdidas
- **Margen negativo en Precio por km**: Puede bajar incluso a valores negativos (descuentos)

**Implementación**: `analisis_sensibilidad.py`, líneas 381-434

---

## 11. Método de Solución

### Algoritmo: Google OR-Tools

El proyecto utiliza **Google OR-Tools**, una biblioteca de optimización de código abierto que implementa algoritmos avanzados para problemas de ruteo.

### Biblioteca Utilizada

```python
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
```

**Versión**: ≥ 9.7.0 (según `requirements.txt`)

---

### Estrategia de Solución Inicial

```python
# app_vrp.py, líneas 264-266
search_parameters.first_solution_strategy = (
    routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
)
```

**PATH_CHEAPEST_ARC**:
- Construye una solución inicial agregando iterativamente el arco más barato disponible
- Rápida construcción de una solución factible inicial
- Buena calidad inicial para la fase de mejora

**Alternativas disponibles en OR-Tools**:
- AUTOMATIC
- SAVINGS
- SWEEP
- CHRISTOFIDES
- FIRST_UNBOUND_MIN_VALUE

---

### Metaheurística de Mejora

```python
# app_vrp.py, líneas 267-269
search_parameters.local_search_metaheuristic = (
    routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
)
```

**GUIDED_LOCAL_SEARCH (GLS)**:
- Metaheurística que modifica la función objetivo para escapar de óptimos locales
- Penaliza características de soluciones visitadas frecuentemente
- Balance entre intensificación y diversificación
- Especialmente efectiva para VRP

#### Funcionamiento de GLS

1. **Fase de búsqueda local**: Mejora la solución actual con movimientos locales
2. **Detección de óptimo local**: Si no hay mejora posible
3. **Penalización**: Aumenta el costo de arcos frecuentemente usados
4. **Nueva búsqueda**: Explora regiones diferentes del espacio de soluciones
5. **Repetición**: Vuelve al paso 1 hasta alcanzar el tiempo límite

**Alternativas disponibles**:
- AUTOMATIC
- GREEDY_DESCENT
- SIMULATED_ANNEALING
- TABU_SEARCH
- GENERIC_TABU_SEARCH

---

### Límite de Tiempo

```python
# app_vrp.py, línea 270
search_parameters.time_limit.seconds = 30
```

- **Por defecto**: 30 segundos
- Configurable mediante parámetro `tiempo_limite_segundos`
- Balance entre calidad de solución y tiempo de ejecución

---

### Estructura del Modelo en OR-Tools

#### 1. Creación del Manager

```python
# app_vrp.py, líneas 230-234
manager = pywrapcp.RoutingIndexManager(
    len(data['distance_matrix']),  # número de nodos
    data['num_vehicles'],           # número de vehículos
    data['depot']                   # índice del depósito
)
```

#### 2. Creación del Routing Model

```python
# app_vrp.py, línea 235
routing = pywrapcp.RoutingModel(manager)
```

#### 3. Registro de la Callback de Distancia

```python
# app_vrp.py, líneas 237-243
def distance_callback(from_index, to_index):
    from_node = manager.IndexToNode(from_index)
    to_node = manager.IndexToNode(to_index)
    return data['distance_matrix'][from_node][to_node]

transit_callback_index = routing.RegisterTransitCallback(distance_callback)
routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
```

#### 4. Registro de la Callback de Demanda

```python
# app_vrp.py, líneas 246-251
def demand_callback(from_index):
    from_node = manager.IndexToNode(from_index)
    return data['demands'][from_node]

demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
```

#### 5. Agregado de Dimensión de Capacidad

```python
# app_vrp.py, líneas 254-260
routing.AddDimensionWithVehicleCapacity(
    demand_callback_index,
    0,  # null capacity slack (sin holgura)
    data['vehicle_capacities'],  # capacidad de cada vehículo
    True,  # start cumul to zero (la carga inicial es 0)
    'Capacity'  # nombre de la dimensión
)
```

#### 6. Resolución

```python
# app_vrp.py, línea 273
solution = routing.SolveWithParameters(search_parameters)
```

#### 7. Extracción de Rutas

```python
# app_vrp.py, líneas 279-306
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
```

---

### Cálculo de Matriz de Distancias

#### Fuente Principal: OSRM API

**OSRM (Open Source Routing Machine)**:
- Utiliza datos reales de OpenStreetMap
- Calcula distancias en red vial real (calles, avenidas)
- Considera sentidos de circulación y restricciones de tránsito
- API pública: `http://router.project-osrm.org`

```python
# app_vrp.py, líneas 145-167
coords = ";".join([f"{loc['lon']},{loc['lat']}" for loc in locations])
url = f"http://router.project-osrm.org/table/v1/driving/{coords}?annotations=distance"

response = requests.get(url, timeout=30)
data = response.json()

if data['code'] == 'Ok':
    distance_matrix = np.array(data['distances'])
```

**Ventajas de OSRM**:
- Distancias realistas para contexto urbano
- Considera la red vial real de CABA
- Gratuito y sin límite de consultas

#### Fallback: Distancia Euclidiana

Si OSRM falla, se usa distancia euclidiana ajustada:

```python
# app_vrp.py, líneas 105-119
distance_matrix[i][j] = sqrt(
    ((lat2 - lat1) × 111,000)² +
    ((lon2 - lon1) × 111,000 × cos(lat1))²
)
```

**Factores de conversión**:
- 1° de latitud ≈ 111,000 metros
- 1° de longitud ≈ 111,000 × cos(latitud) metros

#### Sistema de Cache

```python
# app_vrp.py, líneas 136-143
cache_file = f'vrp_streamlit_{n}.npz'

if use_cache:
    try:
        cache = np.load(cache_file)
        return cache['distance']
    except:
        pass
```

**Beneficios del cache**:
- Reduce llamadas a OSRM API
- Acelera ejecuciones repetidas
- Formato `.npz` (NumPy compressed)

---

### Visualización de Rutas

#### Geometría de Rutas Reales (OSRM)

Para la visualización, se obtiene la geometría detallada de cada ruta:

```python
# app_vrp.py, líneas 168-201
coords = ";".join([f"{all_locations[i]['lon']},{all_locations[i]['lat']}"
                  for i in locations_indices])

url = f"http://router.project-osrm.org/route/v1/driving/{coords}?overview=full&geometries=polyline"

response = requests.get(url, timeout=10)
data = response.json()

if data['code'] == 'Ok':
    encoded_polyline = data['routes'][0]['geometry']
    decoded = polyline.decode(encoded_polyline)  # Lista de (lat, lon)
    return decoded
```

**Polyline**: Formato compacto de Google para codificar secuencias de coordenadas.

#### Biblioteca de Mapas: Folium

```python
# app_vrp.py, líneas 313-416
import folium
from streamlit_folium import st_folium

mapa = folium.Map(
    location=centro,
    zoom_start=12,
    tiles='OpenStreetMap'
)

# Agregar ruta real
folium.PolyLine(
    locations=route_geometry,
    color=color,
    weight=3,
    opacity=0.7,
    popup=f"Camión {vehicle_id}"
).add_to(mapa)
```

**Elementos visualizados**:
- Polígonos de barrios de CABA (fondo)
- Depósito (marcador rojo con icono de casa)
- Rutas de vehículos (líneas de colores siguiendo calles reales)
- Puntos de entrega (círculos de colores)
- Información interactiva en popups

---

## 12. Archivos de Implementación

### Módulos Principales

#### `app_vrp.py` (961 líneas)
**Descripción**: Aplicación web Streamlit para la interfaz de usuario.

**Funciones clave**:
- `optimizar_rutas_vrp()`: Implementa el modelo CVRP completo
- `calculate_distance_matrix_osrm()`: Calcula matriz de distancias
- `crear_mapa_folium()`: Genera visualización interactiva
- `main()`: Interfaz principal con configuración y resultados

**Secciones**:
- Líneas 36-53: Carga de barrios de CABA
- Líneas 59-99: Generación de pedidos aleatorios
- Líneas 121-167: Cálculo de matriz de distancias con OSRM
- Líneas 207-307: Optimización con OR-Tools (CVRP)
- Líneas 313-416: Visualización con Folium
- Líneas 422-684: Interfaz de usuario con Streamlit
- Líneas 753-854: Análisis económico y de sensibilidad

---

#### `optimizador_rutas.py` (271 líneas)
**Descripción**: Clase OptimizadorRutas para resolver TSP simple.

**Clase principal**: `OptimizadorRutas`

**Métodos clave**:
- `__init__()`: Inicializa con matriz de distancias
- `_crear_modelo_datos()`: Prepara datos para OR-Tools
- `resolver()`: Resuelve el TSP con OR-Tools
- `_extraer_ruta()`: Extrae la secuencia de nodos de la solución
- `obtener_ruta_detallada()`: Retorna información detallada con distancias
- `imprimir_ruta()`: Imprime la ruta de forma legible
- `obtener_metricas()`: Calcula métricas de la ruta optimizada

**Función auxiliar**:
- `comparar_rutas()`: Compara dos rutas y calcula ahorro

**Modelo**: TSP simple (K=1, sin restricción de capacidad)

---

#### `analisis_sensibilidad.py` (573 líneas)
**Descripción**: Clase AnalizadorSensibilidad para análisis económico.

**Clase principal**: `AnalizadorSensibilidad`

**Métodos de cálculo**:
- `calcular_costo_nafta_por_km()`: Costo unitario de nafta
- `calcular_tiempo_total_horas()`: Tiempo de operación
- `calcular_costos_operacion()`: Costos totales (nafta + chofer)
- `calcular_ingresos()`: Ingresos totales (base + variable)
- `calcular_margen()`: Margen de ganancia y rentabilidad

**Métodos de sensibilidad**:
- `analizar_sensibilidad_nafta()`: Rango viable de precio de nafta
- `analizar_sensibilidad_costo_chofer()`: Rango viable de costo de chofer
- `analizar_sensibilidad_precio_base()`: Precio base mínimo
- `analizar_sensibilidad_precio_por_km()`: Precio por km mínimo

**Métodos de reporte**:
- `generar_reporte_completo()`: Diccionario con todos los análisis
- `generar_tabla_lingo()`: Tabla estilo LINGO con pandas
- `obtener_interpretaciones()`: Interpretaciones en lenguaje natural

---

#### `calculador_matriz.py` (295 líneas)
**Descripción**: Calcula matriz de distancias usando OSM/OSRM.

**Clase principal**: `CalculadorMatrizDistancias`

**Métodos**:
- `__init__()`: Inicializa con lista de puntos y nombres
- `descargar_mapa_osm()`: Descarga red vial de OSM con OSMnx
- `calcular_matriz()`: Calcula matriz completa de distancias
- `_calcular_distancia_osm()`: Distancia entre dos puntos vía OSM
- `imprimir_resumen()`: Estadísticas de la matriz
- `guardar_cache()`: Guarda matriz en archivo pickle
- `cargar_cache()`: Carga matriz desde cache

**Métodos de cálculo**:
- Usa OSMnx para descargar red vial de CABA
- Calcula rutas más cortas con networkx
- Fallback a distancia euclidiana si OSM falla

---

#### `sistema_optimizacion.py` (416 líneas)
**Descripción**: Sistema completo que integra todos los módulos.

**Clase principal**: `SistemaOptimizacionRutas`

**Métodos del flujo**:
- `cargar_comunas()`: Carga shapefile de comunas de CABA
- `generar_pedidos()`: Genera pedidos aleatorios en una comuna
- `calcular_distancias()`: Calcula matriz de distancias
- `optimizar_ruta()`: Resuelve el problema de ruteo
- `generar_reporte()`: Crea reporte en formato texto
- `exportar_ruta_csv()`: Exporta ruta optimizada a CSV
- `ejecutar_flujo_completo()`: Pipeline completo de optimización

**Función CLI**:
- `main()`: Interfaz de línea de comandos con argparse

**Uso desde terminal**:
```bash
python sistema_optimizacion.py --comuna 1 --pedidos 20 --seed 42 --tiempo 30
```

---

#### `generador_pedidos.py` (297 líneas)
**Descripción**: Genera pedidos aleatorios dentro de CABA.

**Funciones principales**:
- `obtener_depot_por_comuna()`: Retorna coordenadas del depot de Andreani
- `generar_pedidos_aleatorios_en_comuna()`: Genera puntos aleatorios
- `crear_dataset_completo()`: Crea DataFrame con depot + pedidos
- `listar_comunas_disponibles()`: Lista las 15 comunas de CABA

**Depots de Andreani**:
- 12 centros de distribución predefinidos en CABA
- Coordenadas geográficas reales
- Distribuidos estratégicamente por comunas

---

#### `visualizador_rutas.py` (344 líneas)
**Descripción**: Genera visualizaciones de rutas con Folium.

**Funciones**:
- `crear_mapa_base()`: Crea mapa base de CABA
- `agregar_depot()`: Agrega marcador del depósito
- `agregar_puntos_pedidos()`: Agrega marcadores de entregas
- `agregar_ruta_optimizada()`: Dibuja la ruta en el mapa
- `agregar_estadisticas()`: Agrega panel con métricas
- `guardar_mapa()`: Guarda mapa como archivo HTML

**Elementos visuales**:
- Mapa base de OpenStreetMap
- Polígonos de barrios de CABA
- Marcadores personalizados (depot, entregas)
- Líneas de ruta con colores por vehículo
- Popups interactivos con información

---

#### `funcion_distancia_OSM.py` (58 líneas)
**Descripción**: Funciones auxiliares para cálculo de distancias con OSM.

**Funciones**:
- `calcular_distancia_haversine()`: Distancia "as the crow flies"
- `obtener_distancia_osm()`: Distancia en red vial con OSMnx
- `crear_matriz_distancias_osm()`: Matriz completa usando OSM

---

### Datos

#### `utils/barrios copy.csv` (687 KB)
**Descripción**: Polígonos de los 48 barrios de CABA.

**Columnas**:
- `BARRIO`: Nombre del barrio
- `COMUNA`: Número de comuna (1-15)
- `WKT`: Geometría del polígono en formato WKT

**Uso**: Validar que pedidos generados estén dentro de CABA.

---

#### `pedidos_ejemplo.csv`
**Descripción**: Archivo de ejemplo con pedidos.

**Columnas**:
- `order_id` o `pedido_id`: ID único del pedido
- `lat`: Latitud del punto de entrega
- `lon`: Longitud del punto de entrega

**Formato**:
```csv
order_id,lat,lon
1,-34.603277,-58.373207
2,-34.577882,-58.420664
3,-34.588249,-58.396328
```

---

### Archivos de Cache

#### `vrp_streamlit_N.npz`
**Descripción**: Matrices de distancias cacheadas.

**Formato**: NumPy compressed (`.npz`)

**Contenido**:
- `distance`: Matriz NxN de distancias en metros

**N**: Número de locaciones (depot + pedidos)

**Beneficio**: Evita recalcular matrices costosas.

---

#### `matriz_comuna_X.pkl`
**Descripción**: Matrices de distancias por comuna (pickle).

**Formato**: Python pickle

**X**: ID de comuna (1-15)

---

### Documentación

#### `README_APP.md`
**Descripción**: Documentación completa de la aplicación.

**Secciones**:
- Descripción del proyecto
- Instalación y configuración
- Uso de la aplicación web
- Uso de la CLI
- Estructura de archivos
- Ejemplos de uso

---

#### `INSTRUCCIONES_RAPIDAS.md`
**Descripción**: Guía rápida de inicio.

**Contenido**:
- Instalación de dependencias
- Ejecución de la app
- Primer ejemplo
- Troubleshooting

---

#### `requirements.txt`
**Descripción**: Dependencias de Python.

**Librerías principales**:
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
osmnx>=1.5.0
networkx>=3.1
shapely>=2.0.0
```

---

## Referencias

### Bibliografía

1. **Toth, P., & Vigo, D. (2014)**. *Vehicle Routing: Problems, Methods, and Applications* (2nd ed.). SIAM.

2. **Laporte, G. (2009)**. Fifty years of vehicle routing. *Transportation Science*, 43(4), 408-416.

3. **Google OR-Tools Documentation** (2024). *Vehicle Routing Problem*.
   https://developers.google.com/optimization/routing

4. **OpenStreetMap Wiki** (2024). *Routing*.
   https://wiki.openstreetmap.org/wiki/Routing

5. **OSRM Project** (2024). *Open Source Routing Machine*.
   http://project-osrm.org/

### Herramientas y Bibliotecas

- **OR-Tools**: https://github.com/google/or-tools
- **Streamlit**: https://streamlit.io/
- **Folium**: https://python-visualization.github.io/folium/
- **OSMnx**: https://github.com/gboeing/osmnx
- **GeoPandas**: https://geopandas.org/

### Datos Geográficos

- **OpenStreetMap**: https://www.openstreetmap.org/
- **Buenos Aires Data**: https://data.buenosaires.gob.ar/

---

## Notas Finales

Este documento describe la formulación matemática completa del **Capacitated Vehicle Routing Problem (CVRP)** implementado en el proyecto, incluyendo:

- Modelo matemático formal con función objetivo y restricciones
- Parámetros configurables del problema
- Variables de decisión binarias
- Modelo económico completo (costos e ingresos)
- Análisis de sensibilidad de parámetros económicos
- Método de solución con Google OR-Tools
- Detalles de implementación en Python

El sistema es capaz de:
- Optimizar rutas para flotas de 1-5 vehículos
- Manejar capacidades de 5-15 paquetes por vehículo
- Procesar hasta 50 pedidos simultáneamente
- Calcular distancias reales en red vial de CABA
- Analizar viabilidad económica de la operación
- Determinar rangos de sensibilidad de todos los parámetros
- Visualizar rutas en mapas interactivos

---

**Última actualización**: 2025-11-17

**Autores**: Implementación del proyecto Vehicle Routing Problem

**Institución**: Universidad Católica Argentina (UCA)

**Materia**: Optimización

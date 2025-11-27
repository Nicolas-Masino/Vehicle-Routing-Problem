# Vehicle-Routing-Problem

**Autor:** Gerardo Aboulafia, Santiago Arena, Alvaro Hernandez y Nicolas Masino
**Fecha:** Noviembre 2025  
**Problema:** Vehicle Routing Problem (VRP) con Capacidad para Distribución de Paquetes

---

## 1. Introducción y Contexto

### 1.1 Descripción del Problema

Una empresa de e-commerce necesita optimizar la distribución diaria de paquetes a sus clientes. Los pedidos se cargan en el sistema durante el día anterior y, en la madrugada (5:00 AM), se ejecuta un proceso batch que genera las rutas óptimas para la flota de camiones disponible.

### 1.2 Características del Sistema

- **Horizonte temporal:** Planificación diaria (24 horas)
- **Modo de operación:** Batch processing (ejecución única por día)
- **Tipo de problema:** Vehicle Routing Problem (VRP) con restricciones de capacidad
- **Complejidad:** NP-hard

### 1.3 Estrategia de Solución

Dado que el VRP es NP-hard, proponemos dos enfoques híbridos que combinan clustering geográfico con optimización de rutas:

1. **Capacitated K-means + TSP:** Clustering que respeta capacidad desde el inicio
2. **Two-Phase Approach:** Clustering geográfico seguido de ajuste por capacidad

---

## 2. Definiciones y Notación General

### 2.1 Conjuntos

| Símbolo | Descripción |
|---------|-------------|
| $P = \{p_1, p_2, \ldots, p_m\}$ | Conjunto de pedidos a entregar |
| $V = \{v_1, v_2, \ldots, v_n\}$ | Conjunto de vehículos (camiones) disponibles |
| $N = \{0, 1, 2, \ldots, m\}$ | Conjunto de nodos ($0$ = depósito, $1, \ldots, m$ = clientes) |
| $A = \{(i,j) : i,j \in N, i \neq j\}$ | Conjunto de arcos (conexiones entre nodos) |

### 2.2 Parámetros

| Símbolo | Descripción | Unidad |
|---------|-------------|--------|
| $m$ | Número total de pedidos | pedidos |
| $n$ | Número de camiones disponibles | vehículos |
| $Q$ | Capacidad de cada camión | paquetes/vehículo |
| $q_i$ | Demanda del cliente $i$ (típicamente $q_i = 1$) | paquetes |
| $\text{loc}(p_i) = (\text{lat}_i, \text{lon}_i)$ | Coordenadas geográficas del pedido $i$ | grados |
| $d_{ij}$ | Distancia/tiempo de viaje entre nodos $i$ y $j$ | km o minutos |
| $t_{ij}$ | Tiempo de viaje entre nodos $i$ y $j$ | minutos |
| $s_i$ | Tiempo de servicio en el cliente $i$ | minutos |
| $T_{\max}$ | Duración máxima de una ruta | minutos |
| $\text{priority}_i$ | Indicador de prioridad ($1$ = prioritario, $0$ = normal) | binario |
| $[e_i, l_i]$ | Ventana de tiempo para el cliente $i$ | hora del día |
| $M$ | Constante suficientemente grande (Big-M) | - |

### 2.3 Supuestos del Modelo

1. **Homogeneidad de flota:** Todos los camiones tienen la misma capacidad $Q$
2. **Depósito único:** Todos los camiones parten y regresan al mismo depósito (nodo $0$)
3. **Demanda unitaria:** Cada pedido ocupa 1 unidad de capacidad ($q_i = 1$)
4. **Conocimiento completo:** Todos los pedidos se conocen antes de la optimización
5. **Disponibilidad de flota:** Los $n$ camiones están disponibles simultáneamente
6. **Operación diaria:** Las rutas se ejecutan en un solo día
7. **Sin reabastecimiento:** Los camiones no pueden regresar al depósito a mitad de ruta

---

## 3. ENFOQUE 1: Capacitated K-means + TSP

Este enfoque garantiza que el número de clusters resultante corresponde exactamente al número de camiones que se utilizarán.

### 3.1 Fase 1: Capacitated K-means Clustering

#### 3.1.1 Problema de Clustering con Capacidad

**Objetivo:** Particionar el conjunto $P$ en $k$ clusters $C_1, C_2, \ldots, C_k$ minimizando la suma de distancias intra-cluster, sujeto a que cada cluster no exceda la capacidad $Q$.

#### 3.1.2 Formulación Matemática

**Variables de decisión:**

$$y_{ij} \in \{0,1\} \quad \forall i \in P, j \in \{1, \ldots, k\}$$

Donde:
- $y_{ij} = 1$ si el pedido $i$ se asigna al cluster $j$
- $y_{ij} = 0$ en caso contrario

**Centroides:**

$$\mu_j = (\mu_j^{\text{lat}}, \mu_j^{\text{lon}}) \quad \forall j \in \{1, \ldots, k\}$$

Donde $\mu_j$ es el centroide del cluster $j$.

**Función objetivo:**

$$\min Z_1 = \sum_{j=1}^{k} \sum_{i \in P} y_{ij} \cdot \text{dist}(\text{loc}(p_i), \mu_j)$$

Donde $\text{dist}(\cdot, \cdot)$ es la distancia euclidiana:

$$\text{dist}(p_i, \mu_j) = \sqrt{(\text{lat}_i - \mu_j^{\text{lat}})^2 + (\text{lon}_i - \mu_j^{\text{lon}})^2}$$

**Restricciones:**

1. **Asignación única:** Cada pedido debe asignarse a exactamente un cluster
   $$\sum_{j=1}^{k} y_{ij} = 1 \quad \forall i \in P$$

2. **Restricción de capacidad:** Cada cluster no puede exceder la capacidad del camión
   $$\sum_{i \in P} y_{ij} \cdot q_i \leq Q \quad \forall j \in \{1, \ldots, k\}$$

3. **Clusters no vacíos:** Cada cluster debe tener al menos un pedido
   $$\sum_{i \in P} y_{ij} \geq 1 \quad \forall j \in \{1, \ldots, k\}$$

4. **Actualización de centroides:**
   $$\mu_j^{\text{lat}} = \frac{\sum_{i \in P} y_{ij} \cdot \text{lat}_i}{\sum_{i \in P} y_{ij}} \quad \forall j \in \{1, \ldots, k\}$$
   
   $$\mu_j^{\text{lon}} = \frac{\sum_{i \in P} y_{ij} \cdot \text{lon}_i}{\sum_{i \in P} y_{ij}} \quad \forall j \in \{1, \ldots, k\}$$

5. **Variables binarias:**
   $$y_{ij} \in \{0,1\} \quad \forall i \in P, j \in \{1, \ldots, k\}$$

#### 3.1.3 Determinación del Número Óptimo de Clusters

El número de clusters $k$ se determina mediante:

$$k^* = \max\left(n, \left\lceil \frac{m}{Q \cdot \beta} \right\rceil\right)$$

Donde:
- $n$ es el número de camiones disponibles
- $\beta \in (0,1]$ es un factor de utilización (recomendado: $\beta = 0.85$)

**Validación de factibilidad:**

$$k^* \leq n$$

Si $k^* > n$, entonces:
- **Situación:** No hay suficientes camiones para entregar todos los pedidos en un día
- **Acción:** Rechazar pedidos o posponer para el día siguiente

### 3.2 Fase 2: TSP con Restricciones por Cluster

Para cada cluster $C_j$ (donde $j = 1, \ldots, k^*$), resolvemos un **Traveling Salesman Problem (TSP)** con restricciones adicionales.

#### 3.2.1 Definición del Subproblema

**Conjunto de nodos del cluster $j$:**

$$N_j = \{0\} \cup C_j$$

Donde:
- $0$ es el depósito
- $C_j = \{i \in P : y_{ij} = 1\}$ es el conjunto de pedidos asignados al cluster $j$

**Tamaño del cluster:**

$$n_j = |C_j|$$

#### 3.2.2 Variables de Decisión

$$x_{il}^j \in \{0,1\} \quad \forall i,l \in N_j, i \neq l$$

Donde:
- $x_{il}^j = 1$ si el camión asignado al cluster $j$ viaja directamente del nodo $i$ al nodo $l$
- $x_{il}^j = 0$ en caso contrario

**Variables auxiliares:**

$$u_i^j \in \mathbb{R}^+ \quad \forall i \in C_j$$

Variable auxiliar para eliminación de subtours (restricción MTZ - Miller-Tucker-Zemlin).

$$t_i^j \in \mathbb{R}^+ \quad \forall i \in N_j$$

Tiempo de llegada al nodo $i$ en el cluster $j$.

#### 3.2.3 Función Objetivo

**Minimizar el tiempo total de la ruta del cluster $j$:**

$$\min Z_2^j = \sum_{i \in N_j} \sum_{l \in N_j, l \neq i} t_{il} \cdot x_{il}^j + \sum_{i \in C_j} s_i - \alpha \sum_{i \in C_j} \text{priority}_i \cdot \frac{1}{t_i^j + 1}$$

Donde:
- **Primer término:** Tiempo total de viaje
- **Segundo término:** Tiempo total de servicio
- **Tercer término:** Penalización por llegar tarde a pedidos prioritarios (opcional)
- $\alpha \geq 0$ es el peso de la penalización por prioridad

#### 3.2.4 Restricciones del TSP

**1. Salida del depósito:**

$$\sum_{l \in C_j} x_{0l}^j = 1$$

Un único arco sale del depósito hacia los clientes.

**2. Retorno al depósito:**

$$\sum_{i \in C_j} x_{i0}^j = 1$$

Un único arco retorna de los clientes al depósito.

**3. Conservación de flujo - Salida:**

$$\sum_{l \in N_j, l \neq i} x_{il}^j = 1 \quad \forall i \in C_j$$

De cada cliente, sale exactamente un arco.

**4. Conservación de flujo - Entrada:**

$$\sum_{i \in N_j, i \neq l} x_{il}^j = 1 \quad \forall l \in C_j$$

A cada cliente, llega exactamente un arco.

**5. Eliminación de subtours (Miller-Tucker-Zemlin):**

$$u_i^j - u_l^j + (n_j + 1) \cdot x_{il}^j \leq n_j \quad \forall i,l \in C_j, i \neq l$$

Esta restricción garantiza que no se formen ciclos parciales (subtours) que no incluyan el depósito.

**Límites de las variables MTZ:**

$$1 \leq u_i^j \leq n_j \quad \forall i \in C_j$$

**6. Propagación de tiempos:**

$$t_l^j \geq t_i^j + s_i + t_{il} - M(1 - x_{il}^j) \quad \forall i \in N_j, l \in C_j, i \neq l$$

Si el camión va de $i$ a $l$ ($x_{il}^j = 1$), entonces el tiempo de llegada a $l$ es al menos el tiempo de llegada a $i$, más el servicio en $i$, más el tiempo de viaje.

**7. Tiempo inicial en el depósito:**

$$t_0^j = 0$$

**8. Ventanas de tiempo (opcional):**

$$e_i \leq t_i^j \leq l_i \quad \forall i \in C_j$$

El camión debe llegar al cliente $i$ dentro de su ventana de tiempo.

**9. Duración máxima de ruta:**

$$t_0^j + \sum_{i \in N_j} \sum_{l \in N_j, l \neq i} t_{il} \cdot x_{il}^j + \sum_{i \in C_j} s_i \leq T_{\max}$$

El tiempo total de la ruta (incluyendo retorno al depósito) no puede exceder $T_{\max}$.

**10. Variables binarias y no negativas:**

$$x_{il}^j \in \{0,1\} \quad \forall i,l \in N_j, i \neq l$$
$$u_i^j, t_i^j \geq 0 \quad \forall i \in N_j$$

### 3.3 Función Objetivo Global del Enfoque 1

La función objetivo global del sistema es la suma de los tiempos de todas las rutas:

$$\min Z_{\text{total}} = \sum_{j=1}^{k^*} Z_2^j$$

---

## 4. ENFOQUE 2: Two-Phase Approach

Este enfoque separa el clustering geográfico de las restricciones de capacidad, permitiendo mayor flexibilidad pero requiriendo una fase adicional de ajuste.

### 4.1 Fase 1: K-means Clustering Geográfico (Sin Restricción de Capacidad)

#### 4.1.1 Estimación Inicial del Número de Clusters

$$k_{\text{inicial}} = \max\left(n, \left\lceil \frac{m}{Q \cdot \beta} \right\rceil\right)$$

Donde $\beta = 0.8$ (factor de seguridad más conservador que en Enfoque 1).

#### 4.1.2 Formulación del K-means Estándar

**Variables de decisión:**

$$y_{ij} \in \{0,1\} \quad \forall i \in P, j \in \{1, \ldots, k_{\text{inicial}}\}$$

Donde $y_{ij} = 1$ si el pedido $i$ se asigna al cluster $j$.

**Centroides:**

$$\mu_j = (\mu_j^{\text{lat}}, \mu_j^{\text{lon}}) \quad \forall j \in \{1, \ldots, k_{\text{inicial}}\}$$

**Función objetivo:**

$$\min Z_{1a} = \sum_{j=1}^{k_{\text{inicial}}} \sum_{i \in P} y_{ij} \cdot \text{dist}(\text{loc}(p_i), \mu_j)^2$$

**Restricciones:**

1. **Asignación única:**
   $$\sum_{j=1}^{k_{\text{inicial}}} y_{ij} = 1 \quad \forall i \in P$$

2. **Actualización de centroides:**
   $$\mu_j = \frac{\sum_{i \in P} y_{ij} \cdot \text{loc}(p_i)}{\sum_{i \in P} y_{ij}} \quad \forall j \in \{1, \ldots, k_{\text{inicial}}\}$$

3. **Variables binarias:**
   $$y_{ij} \in \{0,1\} \quad \forall i \in P, j \in \{1, \ldots, k_{\text{inicial}}\}$$

**Nota:** En esta fase NO se considera la restricción de capacidad.

### 4.2 Fase 2: Validación y Ajuste de Capacidad

#### 4.2.1 Definición de Clusters Resultantes

Sea $\mathcal{C}_{\text{inicial}} = \{C_1, C_2, \ldots, C_{k_{\text{inicial}}}\}$ el conjunto de clusters resultantes de la Fase 1, donde:

$$C_j = \{i \in P : y_{ij} = 1\} \quad \forall j \in \{1, \ldots, k_{\text{inicial}}\}$$

#### 4.2.2 Algoritmo de Ajuste de Capacidad

**Para cada cluster $C_j \in \mathcal{C}_{\text{inicial}}$:**

**Caso 1:** $|C_j| \leq Q$ (Cluster respeta capacidad)

- ✅ Aceptar cluster $C_j$ como está
- Asignar 1 camión al cluster
- Agregar $C_j$ a $\mathcal{C}_{\text{final}}$

**Caso 2:** $|C_j| > Q$ (Cluster excede capacidad)

- Dividir $C_j$ en sub-clusters mediante K-means
- Número de sub-clusters necesarios:

$$k_j^{\text{sub}} = \left\lceil \frac{|C_j|}{Q} \right\rceil$$

- Ejecutar K-means sobre $C_j$ con $k = k_j^{\text{sub}}$:

$$\min \sum_{r=1}^{k_j^{\text{sub}}} \sum_{i \in C_j} y_{ir}^{\text{sub}} \cdot \text{dist}(\text{loc}(p_i), \mu_r^{\text{sub}})^2$$

$$\text{sujeto a:} \quad \sum_{r=1}^{k_j^{\text{sub}}} y_{ir}^{\text{sub}} = 1 \quad \forall i \in C_j$$

- Resultan sub-clusters $C_j^1, C_j^2, \ldots, C_j^{k_j^{\text{sub}}}$
- Agregar cada sub-cluster a $\mathcal{C}_{\text{final}}$
- Asignar $k_j^{\text{sub}}$ camiones al cluster original $C_j$

#### 4.2.3 Validación Final

**Total de camiones necesarios:**

$$n_{\text{necesarios}} = |\mathcal{C}_{\text{final}}|$$

**Condición de factibilidad:**

$$n_{\text{necesarios}} \leq n$$

Si $n_{\text{necesarios}} > n$:
- **Situación:** Insuficiente capacidad de flota
- **Alternativa 1:** Fusionar los dos clusters más cercanos
- **Alternativa 2:** Rechazar o posponer $n_{\text{necesarios}} - n$ clusters de menor prioridad

#### 4.2.4 Fusión de Clusters (Si es necesario)

**Distancia entre clusters:**

$$D(C_i, C_j) = \text{dist}(\mu_i, \mu_j)$$

**Criterio de fusión:**

Mientras $|\mathcal{C}_{\text{final}}| > n$:

1. Encontrar el par de clusters $(C_a, C_b)$ con mínima distancia:
   $$(C_a, C_b) = \arg\min_{C_i, C_j \in \mathcal{C}_{\text{final}}, i \neq j} D(C_i, C_j)$$

2. Verificar factibilidad de fusión:
   $$|C_a \cup C_b| \leq Q$$

3. Si factible:
   - Fusionar: $C_{\text{nuevo}} = C_a \cup C_b$
   - Remover $C_a$ y $C_b$ de $\mathcal{C}_{\text{final}}$
   - Agregar $C_{\text{nuevo}}$ a $\mathcal{C}_{\text{final}}$

4. Si no factible:
   - Elegir el siguiente par más cercano

### 4.3 Fase 3: Optimización de Rutas (TSP por Cluster)

Para cada cluster $C_j \in \mathcal{C}_{\text{final}}$, resolver el mismo TSP descrito en la **Sección 3.2** del Enfoque 1.

La formulación matemática es idéntica, solo cambia el conjunto de clusters de entrada:
- **Enfoque 1:** Usa clusters de Capacitated K-means
- **Enfoque 2:** Usa clusters de K-means ajustados

### 4.4 Función Objetivo Global del Enfoque 2

$$\min Z_{\text{total}} = \sum_{j \in \mathcal{C}_{\text{final}}} Z_2^j$$

---

## 5. Cálculo de Matrices de Distancia/Tiempo

### 5.1 Distancia Euclidiana (Aproximación)

Para clustering inicial (rápido):

$$d_{ij}^{\text{eucl}} = R \cdot \sqrt{(\text{lat}_i - \text{lat}_j)^2 + (\text{lon}_i - \text{lon}_j)^2} \cdot \frac{\pi}{180}$$

Donde $R = 6371$ km (radio de la Tierra).

### 5.2 Distancia Haversine (Más Precisa)

$$a = \sin^2\left(\frac{\Delta\text{lat}}{2}\right) + \cos(\text{lat}_i) \cdot \cos(\text{lat}_j) \cdot \sin^2\left(\frac{\Delta\text{lon}}{2}\right)$$

$$c = 2 \cdot \text{atan2}\left(\sqrt{a}, \sqrt{1-a}\right)$$

$$d_{ij}^{\text{haversine}} = R \cdot c$$

### 5.3 Distancia Real de Ruta (API)

Para optimización de TSP (más preciso):

$$d_{ij}^{\text{real}}, t_{ij}^{\text{real}} = \text{API}_{\text{routing}}(\text{loc}(p_i), \text{loc}(p_j))$$

Donde $\text{API}_{\text{routing}}$ puede ser:
- Google Maps Distance Matrix API
- OSRM (Open Source Routing Machine)
- OpenRouteService

**Nota:** Se recomienda usar distancia Haversine para clustering y distancia real para TSP.

---

## 6. Métricas de Evaluación

### 6.1 Métricas de Calidad de Solución

**1. Distancia total recorrida:**

$$D_{\text{total}} = \sum_{j=1}^{k^*} \sum_{i \in N_j} \sum_{l \in N_j, l \neq i} d_{il} \cdot x_{il}^j$$

**2. Tiempo total de operación:**

$$T_{\text{total}} = \sum_{j=1}^{k^*} \left(\sum_{i \in N_j} \sum_{l \in N_j, l \neq i} t_{il} \cdot x_{il}^j + \sum_{i \in C_j} s_i\right)$$

**3. Utilización promedio de flota:**

$$U_{\text{avg}} = \frac{1}{k^*} \sum_{j=1}^{k^*} \frac{|C_j|}{Q}$$

**4. Ruta más larga:**

$$T_{\max}^{\text{sol}} = \max_{j=1,\ldots,k^*} \left(\sum_{i \in N_j} \sum_{l \in N_j, l \neq i} t_{il} \cdot x_{il}^j + \sum_{i \in C_j} s_i\right)$$

**5. Pedidos prioritarios entregados a tiempo:**

$$P_{\text{ontime}} = \frac{\sum_{j=1}^{k^*} \sum_{i \in C_j} \text{priority}_i \cdot \mathbb{1}_{t_i^j \leq l_i}}{|\{i : \text{priority}_i = 1\}|}$$

Donde $\mathbb{1}_{t_i^j \leq l_i}$ es una función indicadora.

### 6.2 Métricas de Eficiencia Computacional

**1. Tiempo de ejecución clustering:**

$$T_{\text{cluster}}$$

**2. Tiempo de ejecución TSP (suma de todos los clusters):**

$$T_{\text{TSP}} = \sum_{j=1}^{k^*} T_{\text{TSP}}^j$$

**3. Tiempo total de optimización:**

$$T_{\text{opt}} = T_{\text{cluster}} + T_{\text{TSP}}$$

### 6.3 Métricas de Negocio

**1. Costo operativo total:**

$$C_{\text{total}} = c_{\text{km}} \cdot D_{\text{total}} + c_{\text{hora}} \cdot T_{\text{total}} + c_{\text{camión}} \cdot k^*$$

Donde:
- $c_{\text{km}}$: Costo por kilómetro (combustible, mantenimiento)
- $c_{\text{hora}}$: Costo por hora (salario conductor)
- $c_{\text{camión}}$: Costo fijo por camión utilizado

**2. Nivel de servicio:**

$$\text{SL} = \frac{|\{i : t_i^j \leq l_i\}|}{m} \times 100\%$$

Porcentaje de pedidos entregados dentro de la ventana de tiempo.

---

## 7. Comparación de Enfoques

### 7.1 Tabla Comparativa

| Aspecto | **Enfoque 1: Capacitated K-means** | **Enfoque 2: Two-Phase** |
|---------|-----------------------------------|--------------------------|
| **Complejidad algorítmica** | Alta (clustering NP-hard) | Media (k-means + ajuste) |
| **Garantía de capacidad** | Desde el clustering | Post-clustering |
| **Flexibilidad** | Baja (rígido) | Alta (adaptable) |
| **Número de clusters** | Exacto desde inicio | Variable, requiere ajuste |
| **Tiempo de cómputo** | Alto (iteración con restricción) | Medio (dos fases separadas) |
| **Calidad de clustering geográfico** | Puede ser subóptimo | Óptimo geográficamente |
| **Manejo de casos límite** | Más robusto | Requiere lógica de fusión |
| **Implementación** | Más compleja | Más simple |

### 7.2 Cuándo Usar Cada Enfoque

**Usar Enfoque 1 (Capacitated K-means) cuando:**
- La capacidad de los camiones es una restricción crítica
- Se requiere garantía de factibilidad desde el clustering
- Se tiene tiempo de cómputo suficiente
- La distribución geográfica es relativamente uniforme

**Usar Enfoque 2 (Two-Phase) cuando:**
- La geografía tiene zonas densas y dispersas
- Se requiere flexibilidad para ajustar el número de camiones
- Se necesita solución rápida
- Se puede tolerar post-procesamiento (fusión de clusters)

### 7.3 Complejidad Computacional

**Enfoque 1:**
- Clustering: $O(m \cdot k \cdot I_1 \cdot C)$ donde $I_1$ es el número de iteraciones y $C$ es el costo de verificar capacidad
- TSP por cluster: $O(k \cdot n_j! )$ para solución exacta, o $O(k \cdot n_j^2)$ para heurística
- **Total:** $O(m \cdot k \cdot I_1 \cdot C + k \cdot n_j^2)$

**Enfoque 2:**
- K-means estándar: $O(m \cdot k \cdot I_2)$ donde $I_2$ es el número de iteraciones
- Validación y ajuste: $O(k + k_{\text{sub}} \cdot m_{\text{sub}})$
- TSP por cluster: $O(k_{\text{final}} \cdot n_j^2)$
- **Total:** $O(m \cdot k \cdot I_2 + k_{\text{final}} \cdot n_j^2)$

Típicamente: $I_1 > I_2$ pero $k_{\text{final}} \geq k$

---

## 8. Extensiones y Variaciones

### 8.1 Ventanas de Tiempo Estrictas

Modificar la restricción de ventanas de tiempo para hacerla estricta:

$$e_i \leq t_i^j \leq l_i \quad \forall i \in C_j$$

Eliminar la relajación con penalización en la función objetivo.

### 8.2 Múltiples Depósitos

Extender el modelo para incluir múltiples depósitos $D = \{d_1, d_2, \ldots, d_p\}$:

$$\text{depot}(v_k) \in D \quad \forall v_k \in V$$

Cada camión parte de su depósito asignado.

### 8.3 Flota Heterogénea

Diferentes capacidades por tipo de camión:

$$Q_k \quad \forall k \in \{1, \ldots, n\}$$

Donde $Q_k$ puede variar según el tipo de vehículo.

### 8.4 Pickup and Delivery

Incluir recolecciones además de entregas:

- $P^+$: Conjunto de entregas (deliveries)
- $P^-$: Conjunto de recolecciones (pickups)
- Restricción de precedencia: Pickup debe ocurrir antes que delivery

### 8.5 Optimización Dinámica (Online)

Incluir nuevos pedidos durante el día:

- Re-optimización parcial
- Inserción de pedidos en rutas existentes
- Balance entre calidad de solución y tiempo de respuesta

---

## 9. Consideraciones Prácticas

### 9.1 Parámetros Recomendados

| Parámetro | Valor Sugerido | Justificación |
|-----------|----------------|---------------|
| $Q$ | 20-40 paquetes | Capacidad típica de vehículo pequeño |
| $s_i$ | 3-5 minutos | Tiempo promedio de entrega |
| $T_{\max}$ | 8 horas (480 min) | Jornada laboral estándar |
| $\beta$ | 0.80-0.85 | Factor de seguridad para utilización |
| $\alpha$ | 0.1-0.5 | Peso de penalización por prioridad |
| $M$ | $10 \cdot T_{\max}$ | Big-M suficientemente grande |

### 9.2 Fuentes de Datos

**APIs Recomendadas:**

1. **Google Maps Distance Matrix API**
   - Precisión: ⭐⭐⭐⭐⭐
   - Costo: $$$ (gratis hasta 40,000 requests/mes)
   - Tráfico en tiempo real: ✅
-
2. **OSRM (Open Source Routing Machine)**
   - Precisión: ⭐⭐⭐⭐
   - Costo: Gratis (self-hosted o público)
   - Tráfico en tiempo real: ❌

3. **OpenRouteService**
   - Precisión: ⭐⭐⭐⭐
   - Costo: Gratis (2000 requests/día)
   - Tráfico en tiempo real: ❌

### 9.3 Librerías de Optimización

**Para Clustering:**
- `scikit-learn`: K-means estándar
- `k-means-constrained`: K-means con restricción de capacidad
- Implementación custom con `scipy.optimize`

**Para TSP/VRP:**
- `ortools` (Google OR-Tools): Recomendado ⭐⭐⭐⭐⭐
- `python-tsp`: Para TSP específicamente
- `pulp` o `pyomo`: Para formular el modelo manualmente

---

## 10. Conclusiones

### 10.1 Resumen

Se han presentado dos enfoques para resolver el problema de ruteo de última milla en e-commerce:

1. **Capacitated K-means + TSP:** Enfoque integrado que garantiza factibilidad de capacidad desde el clustering
2. **Two-Phase Approach:** Enfoque modular que optimiza primero geográficamente y luego ajusta por capacidad

Ambos enfoques son viables y tienen ventajas según el contexto de aplicación.

### 10.2 Recomendación

Para el proyecto, se sugiere:

1. **Implementar ambos enfoques** y comparar resultados
2. **Usar distancia Haversine** para clustering (rápido)
3. **Usar API de routing** para TSP (preciso)
4. **Validar con datos reales** de al menos 50-100 pedidos
5. **Medir métricas** de calidad y tiempo de ejecución

### 10.3 Trabajo Futuro

- Incorporar predicción de demanda para planificación multi-día
- Optimización multi-objetivo (costo vs nivel de servicio)
- Aprendizaje automático para mejorar clustering
- Ruteo dinámico con pedidos que llegan en tiempo real

---

## Referencias

1. Dantzig, G. B., & Ramser, J. H. (1959). The truck dispatching problem. *Management Science*, 6(1), 80-91.

2. Miller, C. E., Tucker, A. W., & Zemlin, R. A. (1960). Integer programming formulation of traveling salesman problems. *Journal of the ACM*, 7(4), 326-329.

3. Clarke, G., & Wright, J. W. (1964). Scheduling of vehicles from a central depot to a number of delivery points. *Operations Research*, 12(4), 568-581.

4. Toth, P., & Vigo, D. (2014). *Vehicle routing: problems, methods, and applications*. SIAM.

5. Google OR-Tools Documentation. (2024). *Vehicle Routing Problem*. https://developers.google.com/optimization/routing

6. Laporte, G. (2009). Fifty years of vehicle routing. *Transportation Science*, 43(4), 408-416.

---

**Documento preparado para:** Proyecto de Optimización - Gerardo  
**Versión:** 1.0  

**Última actualización:** Noviembre 2025


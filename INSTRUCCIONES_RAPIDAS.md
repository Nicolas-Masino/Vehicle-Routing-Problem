# Instrucciones Rápidas - VRP Streamlit

## Inicio Rápido

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Ejecutar la aplicación

```bash
streamlit run app_vrp.py
```

### 3. Usar la aplicación

**Opción A - Generar pedidos aleatorios:**
1. En el panel izquierdo, ir a la pestaña "Generar Aleatorio"
2. Elegir número de pedidos (ej: 20)
3. Click en "Generar Pedidos Aleatorios"
4. Click en "Optimizar Rutas"

**Opción B - Cargar CSV:**
1. En el panel izquierdo, ir a la pestaña "Subir CSV"
2. Subir el archivo `pedidos_ejemplo.csv`
3. Click en "Optimizar Rutas"

## Formato CSV Requerido

```csv
order_id,lat,lon
1,-34.603,-58.381
2,-34.610,-58.400
```

Columnas **obligatorias**: `lat`, `lon`

## Archivos Importantes

- `app_vrp.py` - Aplicación principal ⭐
- `requirements.txt` - Dependencias
- `pedidos_ejemplo.csv` - CSV de ejemplo
- `utils/barrios copy.csv` - Polígonos de CABA (requerido)

## Parámetros Recomendados para Primera Prueba

- **Ubicación**: Retiro (por defecto)
- **Camiones**: 3
- **Capacidad**: 15
- **Pedidos**: 20 (generar aleatorio con seed 42)

## Solución de Problemas Comunes

**Error: ModuleNotFoundError**
```bash
pip install -r requirements.txt
```

**Error: archivo de barrios no encontrado**
- Verificar que existe: `utils/barrios copy.csv`

**No se encuentra solución**
- Reducir número de pedidos
- Aumentar número de camiones o capacidad

## Características Principales

✅ Layout de 3 columnas
✅ Configuración de depósito y flota
✅ Carga de pedidos por CSV o generación aleatoria
✅ Optimización con OR-Tools
✅ Visualización con Folium (rutas reales de OSRM)
✅ Tabs por camión + vista general
✅ Listado de órdenes de entrega
✅ Métricas detalladas y generales
✅ Validaciones de entrada
✅ Caché de matrices de distancia

## Rendimiento

- Primera ejecución: ~10-20 segundos (calcula matriz de distancias)
- Ejecuciones siguientes: ~5-10 segundos (usa caché)
- Máximo recomendado: 50 pedidos

## Próximos Pasos

1. Probar con diferentes configuraciones
2. Cargar tus propios pedidos en CSV
3. Experimentar con diferentes ubicaciones de depósito
4. Comparar resultados con diferentes números de camiones

---

Para más detalles, consulta `README_APP.md`

import pandas as pd
import numpy as np
  
def optimizar_ruta_fake(df, velocidad_prom):
    if df.empty:
        return df, 0, 0

    # Simular ruta ordenada aleatoriamente
    ruta = df.sample(frac=1).reset_index(drop=True)

    # Distancia simulada
    distancias = np.random.uniform(1, 5, size=len(df))
    distancia_total = distancias.sum()
    tiempo_total = distancia_total / velocidad_prom

    ruta["orden"] = range(1, len(df) + 1)
    return ruta, distancia_total, tiempo_total

"""
Módulo de Análisis de Sensibilidad para VRP
Calcula métricas económicas y análisis de sensibilidad de parámetros
"""

import pandas as pd
from typing import Dict, List, Tuple, Optional


class AnalizadorSensibilidad:
    """
    Analiza la sensibilidad económica de la solución VRP optimizada.
    Calcula costos, ingresos, márgenes y rangos de variación de parámetros.
    """

    def __init__(self,
                 distancia_total_km: float,
                 num_rutas: int,
                 num_pedidos: int,
                 distancias_por_ruta: List[float],
                 precio_nafta: float,
                 rendimiento_vehiculo: float,
                 precio_base_por_pedido: float,
                 precio_por_km: float,
                 costo_chofer_por_hora: float,
                 velocidad_promedio_kmh: float):
        """
        Inicializa el analizador con los datos de la solución optimizada.

        Args:
            distancia_total_km: Distancia total de todas las rutas (km)
            num_rutas: Número de rutas/vehículos utilizados
            num_pedidos: Número total de pedidos/paquetes entregados
            distancias_por_ruta: Lista con la distancia de cada ruta (km)
            precio_nafta: Precio del litro de nafta ($/litro)
            rendimiento_vehiculo: Rendimiento del vehículo (km/litro)
            precio_base_por_pedido: Precio base cobrado por cada pedido ($)
            precio_por_km: Precio variable cobrado por km ($/km)
            costo_chofer_por_hora: Costo del chofer por hora ($/h)
            velocidad_promedio_kmh: Velocidad promedio del vehículo (km/h)
        """
        self.distancia_total_km = distancia_total_km
        self.num_rutas = num_rutas
        self.num_pedidos = num_pedidos
        self.distancias_por_ruta = distancias_por_ruta
        self.precio_nafta = precio_nafta
        self.rendimiento_vehiculo = rendimiento_vehiculo
        self.precio_base_por_pedido = precio_base_por_pedido
        self.precio_por_km = precio_por_km
        self.costo_chofer_por_hora = costo_chofer_por_hora
        self.velocidad_promedio_kmh = velocidad_promedio_kmh

        # Validaciones
        if rendimiento_vehiculo <= 0:
            raise ValueError("El rendimiento del vehículo debe ser mayor a 0")
        if velocidad_promedio_kmh <= 0:
            raise ValueError("La velocidad promedio debe ser mayor a 0")
        if precio_nafta < 0 or precio_base_por_pedido < 0 or precio_por_km < 0 or costo_chofer_por_hora < 0:
            raise ValueError("Los precios no pueden ser negativos")
        if num_pedidos <= 0:
            raise ValueError("El número de pedidos debe ser mayor a 0")

    def calcular_costo_nafta_por_km(self) -> float:
        """
        Calcula el costo de nafta por kilómetro.

        Returns:
            Costo en $ por km
        """
        return self.precio_nafta / self.rendimiento_vehiculo

    def calcular_tiempo_total_horas(self) -> float:
        """
        Calcula el tiempo total de operación en horas.

        Returns:
            Tiempo total en horas
        """
        return self.distancia_total_km / self.velocidad_promedio_kmh

    def calcular_costos_operacion(self) -> Dict[str, float]:
        """
        Calcula los costos totales de operación.

        Returns:
            Diccionario con costos detallados:
            - costo_nafta_por_km: Costo de nafta por km ($/km)
            - costo_total_nafta: Costo total de nafta ($)
            - tiempo_total_horas: Tiempo total de operación (horas)
            - costo_total_chofer: Costo total del chofer ($)
            - costo_total: Costo total de operación (nafta + chofer) ($)
            - costos_por_ruta: Lista de costos totales por cada ruta ($)
        """
        # Costos de nafta
        costo_nafta_por_km = self.calcular_costo_nafta_por_km()
        costo_total_nafta = costo_nafta_por_km * self.distancia_total_km

        # Costos de chofer
        tiempo_total_horas = self.calcular_tiempo_total_horas()
        costo_total_chofer = self.costo_chofer_por_hora * tiempo_total_horas

        # Costo total
        costo_total = costo_total_nafta + costo_total_chofer

        # Costos por ruta (proporcional a distancia/tiempo de cada ruta)
        costos_por_ruta = []
        for dist in self.distancias_por_ruta:
            tiempo_ruta = dist / self.velocidad_promedio_kmh
            costo_nafta_ruta = costo_nafta_por_km * dist
            costo_chofer_ruta = self.costo_chofer_por_hora * tiempo_ruta
            costos_por_ruta.append(costo_nafta_ruta + costo_chofer_ruta)

        return {
            'costo_nafta_por_km': costo_nafta_por_km,
            'costo_total_nafta': costo_total_nafta,
            'tiempo_total_horas': tiempo_total_horas,
            'costo_total_chofer': costo_total_chofer,
            'costo_total': costo_total,
            'costos_por_ruta': costos_por_ruta
        }

    def calcular_ingresos(self) -> Dict[str, float]:
        """
        Calcula los ingresos totales por envíos.
        Modelo: Ingreso = (Pedidos × Precio Base) + (Distancia × Precio por km)

        Returns:
            Diccionario con ingresos detallados:
            - ingreso_base: Ingreso por precios base ($)
            - ingreso_variable: Ingreso por precio por km ($)
            - ingreso_total: Ingreso total ($)
            - ingresos_por_ruta: Lista de ingresos por cada ruta ($)
        """
        ingreso_base = self.num_pedidos * self.precio_base_por_pedido
        ingreso_variable = self.distancia_total_km * self.precio_por_km
        ingreso_total = ingreso_base + ingreso_variable

        # Distribuir ingresos por ruta (proporcional a distancia de cada ruta)
        # Nota: Los ingresos base se distribuyen proporcionalmente
        ingresos_por_ruta = []
        for dist in self.distancias_por_ruta:
            proporcion = dist / self.distancia_total_km if self.distancia_total_km > 0 else 0
            ingreso_ruta = (proporcion * ingreso_base) + (dist * self.precio_por_km)
            ingresos_por_ruta.append(ingreso_ruta)

        return {
            'ingreso_base': ingreso_base,
            'ingreso_variable': ingreso_variable,
            'ingreso_total': ingreso_total,
            'ingresos_por_ruta': ingresos_por_ruta
        }

    def calcular_margen(self) -> Dict[str, float]:
        """
        Calcula el margen de ganancia.

        Returns:
            Diccionario con:
            - margen_total: Margen total en $ (ingresos - costos)
            - rentabilidad_porcentaje: Rentabilidad como % de ingresos
            - margenes_por_ruta: Lista de márgenes por cada ruta ($)
        """
        costos = self.calcular_costos_operacion()
        ingresos = self.calcular_ingresos()

        margen_total = ingresos['ingreso_total'] - costos['costo_total']

        # Evitar división por cero
        rentabilidad = (margen_total / ingresos['ingreso_total'] * 100) if ingresos['ingreso_total'] > 0 else 0

        margenes_por_ruta = [
            ing - cost
            for ing, cost in zip(ingresos['ingresos_por_ruta'], costos['costos_por_ruta'])
        ]

        return {
            'margen_total': margen_total,
            'rentabilidad_porcentaje': rentabilidad,
            'margenes_por_ruta': margenes_por_ruta
        }

    def analizar_sensibilidad_nafta(self) -> Dict[str, float]:
        """
        Analiza la sensibilidad del precio de nafta.
        Calcula cuánto puede variar el precio sin generar pérdidas.

        Returns:
            Diccionario con:
            - precio_nafta_actual: Precio actual ($/litro)
            - costo_nafta_actual: Costo de nafta actual ($)
            - precio_nafta_breakeven: Precio de nafta en punto de equilibrio ($/litro)
            - aumento_permitido: Cuánto puede aumentar el precio sin pérdida ($/litro)
            - aumento_permitido_porcentaje: Aumento permitido en %
            - lower_bound: Límite inferior (0)
            - upper_bound: Límite superior para rentabilidad ($/litro)
        """
        costos = self.calcular_costos_operacion()
        ingresos = self.calcular_ingresos()

        # Precio de nafta en punto de equilibrio (margen = 0)
        # Ingreso = Costo_nafta + Costo_chofer
        # ingreso_total = (precio_nafta_BE / rendimiento) × dist + costo_chofer_actual
        # precio_nafta_BE = (ingreso_total - costo_chofer_actual) × rendimiento / dist

        if self.distancia_total_km > 0:
            precio_nafta_breakeven = ((ingresos['ingreso_total'] - costos['costo_total_chofer']) * self.rendimiento_vehiculo) / self.distancia_total_km
            precio_nafta_breakeven = max(0, precio_nafta_breakeven)  # No puede ser negativo
        else:
            precio_nafta_breakeven = float('inf')

        # Cuánto puede aumentar el precio de nafta
        aumento_permitido = precio_nafta_breakeven - self.precio_nafta

        # Porcentaje de aumento permitido
        aumento_porcentaje = (aumento_permitido / self.precio_nafta * 100) if self.precio_nafta > 0 else float('inf')

        return {
            'precio_nafta_actual': self.precio_nafta,
            'costo_nafta_actual': costos['costo_total_nafta'],
            'precio_nafta_breakeven': precio_nafta_breakeven,
            'aumento_permitido': aumento_permitido,
            'aumento_permitido_porcentaje': aumento_porcentaje,
            'lower_bound': 0,  # El precio no puede ser negativo
            'upper_bound': precio_nafta_breakeven  # Límite para no tener pérdidas
        }

    def analizar_sensibilidad_precio_base(self) -> Dict[str, float]:
        """
        Analiza la sensibilidad del precio base por pedido.
        Calcula el precio base mínimo para no tener pérdidas.

        Returns:
            Diccionario con:
            - precio_base_actual: Precio base actual ($/pedido)
            - ingreso_base_actual: Ingreso por precio base actual ($)
            - precio_base_breakeven: Precio base mínimo para break-even ($/pedido)
            - margen_disponible: Cuánto puede bajar el precio sin pérdida ($/pedido)
            - margen_disponible_porcentaje: Margen disponible en %
            - lower_bound: Límite inferior para rentabilidad ($/pedido)
            - upper_bound: Límite superior (infinito)
        """
        costos = self.calcular_costos_operacion()
        ingresos = self.calcular_ingresos()

        # Precio base mínimo en punto de equilibrio
        # (precio_base_BE × num_pedidos) + (precio_por_km × dist) = costo_total
        # precio_base_BE = (costo_total - precio_por_km × dist) / num_pedidos

        if self.num_pedidos > 0:
            precio_base_breakeven = (costos['costo_total'] - (self.precio_por_km * self.distancia_total_km)) / self.num_pedidos
            # No puede ser negativo
            precio_base_breakeven = max(0, precio_base_breakeven)
        else:
            precio_base_breakeven = 0

        # Cuánto puede bajar el precio base
        margen_disponible = self.precio_base_por_pedido - precio_base_breakeven

        # Porcentaje del margen
        margen_porcentaje = (margen_disponible / self.precio_base_por_pedido * 100) if self.precio_base_por_pedido > 0 else 0

        return {
            'precio_base_actual': self.precio_base_por_pedido,
            'ingreso_base_actual': ingresos['ingreso_base'],
            'precio_base_breakeven': precio_base_breakeven,
            'margen_disponible': margen_disponible,
            'margen_disponible_porcentaje': margen_porcentaje,
            'lower_bound': precio_base_breakeven,  # Mínimo para no perder
            'upper_bound': float('inf')  # No hay límite superior
        }

    def analizar_sensibilidad_precio_por_km(self) -> Dict[str, float]:
        """
        Analiza la sensibilidad del precio por km.
        Calcula el precio por km mínimo para no tener pérdidas.

        Returns:
            Diccionario con:
            - precio_por_km_actual: Precio por km actual ($/km)
            - ingreso_variable_actual: Ingreso por precio por km actual ($)
            - precio_por_km_breakeven: Precio por km mínimo para break-even ($/km)
            - margen_disponible: Cuánto puede bajar el precio sin pérdida ($/km)
            - margen_disponible_porcentaje: Margen disponible en %
            - lower_bound: Límite inferior para rentabilidad ($/km)
            - upper_bound: Límite superior (infinito)
        """
        costos = self.calcular_costos_operacion()
        ingresos = self.calcular_ingresos()

        # Precio por km mínimo en punto de equilibrio
        # (precio_base × num_pedidos) + (precio_por_km_BE × dist) = costo_total
        # precio_por_km_BE = (costo_total - precio_base × num_pedidos) / dist

        if self.distancia_total_km > 0:
            precio_por_km_breakeven = (costos['costo_total'] - (self.precio_base_por_pedido * self.num_pedidos)) / self.distancia_total_km
            # No puede ser negativo
            precio_por_km_breakeven = max(0, precio_por_km_breakeven)
        else:
            precio_por_km_breakeven = 0

        # Cuánto puede bajar el precio por km
        margen_disponible = self.precio_por_km - precio_por_km_breakeven

        # Porcentaje del margen
        margen_porcentaje = (margen_disponible / self.precio_por_km * 100) if self.precio_por_km > 0 else 0

        return {
            'precio_por_km_actual': self.precio_por_km,
            'ingreso_variable_actual': ingresos['ingreso_variable'],
            'precio_por_km_breakeven': precio_por_km_breakeven,
            'margen_disponible': margen_disponible,
            'margen_disponible_porcentaje': margen_porcentaje,
            'lower_bound': precio_por_km_breakeven,  # Mínimo para no perder
            'upper_bound': float('inf')  # No hay límite superior
        }

    def analizar_sensibilidad_costo_chofer(self) -> Dict[str, float]:
        """
        Analiza la sensibilidad del costo del chofer por hora.
        Calcula cuánto puede variar el costo sin generar pérdidas.

        Returns:
            Diccionario con:
            - costo_chofer_actual: Costo actual del chofer ($/h)
            - costo_chofer_total_actual: Costo total del chofer actual ($)
            - costo_chofer_breakeven: Costo del chofer en punto de equilibrio ($/h)
            - aumento_permitido: Cuánto puede aumentar el costo sin pérdida ($/h)
            - aumento_permitido_porcentaje: Aumento permitido en %
            - lower_bound: Límite inferior (0)
            - upper_bound: Límite superior para rentabilidad ($/h)
        """
        costos = self.calcular_costos_operacion()
        ingresos = self.calcular_ingresos()

        # Costo del chofer en punto de equilibrio (margen = 0)
        # Ingreso = Costo_nafta + Costo_chofer
        # ingreso_total = costo_nafta_actual + (costo_chofer_BE × tiempo)
        # costo_chofer_BE = (ingreso_total - costo_nafta_actual) / tiempo

        tiempo_total_horas = self.calcular_tiempo_total_horas()

        if tiempo_total_horas > 0:
            costo_chofer_breakeven = (ingresos['ingreso_total'] - costos['costo_total_nafta']) / tiempo_total_horas
            costo_chofer_breakeven = max(0, costo_chofer_breakeven)  # No puede ser negativo
        else:
            costo_chofer_breakeven = float('inf')

        # Cuánto puede aumentar el costo del chofer
        aumento_permitido = costo_chofer_breakeven - self.costo_chofer_por_hora

        # Porcentaje de aumento permitido
        aumento_porcentaje = (aumento_permitido / self.costo_chofer_por_hora * 100) if self.costo_chofer_por_hora > 0 else float('inf')

        return {
            'costo_chofer_actual': self.costo_chofer_por_hora,
            'costo_chofer_total_actual': costos['costo_total_chofer'],
            'costo_chofer_breakeven': costo_chofer_breakeven,
            'aumento_permitido': aumento_permitido,
            'aumento_permitido_porcentaje': aumento_porcentaje,
            'lower_bound': 0,  # El costo no puede ser negativo
            'upper_bound': costo_chofer_breakeven  # Límite para no tener pérdidas
        }

    def generar_reporte_completo(self) -> Dict[str, any]:
        """
        Genera un reporte completo con todos los análisis.

        Returns:
            Diccionario con todas las métricas y análisis
        """
        return {
            'costos': self.calcular_costos_operacion(),
            'ingresos': self.calcular_ingresos(),
            'margen': self.calcular_margen(),
            'sensibilidad_nafta': self.analizar_sensibilidad_nafta(),
            'sensibilidad_precio_base': self.analizar_sensibilidad_precio_base(),
            'sensibilidad_precio_por_km': self.analizar_sensibilidad_precio_por_km(),
            'sensibilidad_costo_chofer': self.analizar_sensibilidad_costo_chofer()
        }

    def generar_tabla_lingo(self) -> pd.DataFrame:
        """
        Genera una tabla estilo LINGO con el análisis de sensibilidad.

        Returns:
            DataFrame con columnas similares a LINGO:
            - Variable
            - Valor Actual
            - Costo/Ingreso Parcial
            - Precio Mínimo
            - Precio Máximo
            - Margen de Variación
        """
        sens_nafta = self.analizar_sensibilidad_nafta()
        sens_base = self.analizar_sensibilidad_precio_base()
        sens_por_km = self.analizar_sensibilidad_precio_por_km()
        sens_chofer = self.analizar_sensibilidad_costo_chofer()

        data = [
            {
                'Variable': 'Precio Nafta ($/L)',
                'Valor Actual': f"${sens_nafta['precio_nafta_actual']:,.2f}",
                'Costo/Ingreso Parcial': f"Costo: ${sens_nafta['costo_nafta_actual']:,.2f}",
                'Precio Mínimo': f"${sens_nafta['lower_bound']:,.2f}",
                'Precio Máximo': f"${sens_nafta['upper_bound']:,.2f}",
                'Margen de Variación': f"+${sens_nafta['aumento_permitido']:,.2f} (+{sens_nafta['aumento_permitido_porcentaje']:.1f}%)"
            },
            {
                'Variable': 'Costo Chofer ($/h)',
                'Valor Actual': f"${sens_chofer['costo_chofer_actual']:,.2f}",
                'Costo/Ingreso Parcial': f"Costo: ${sens_chofer['costo_chofer_total_actual']:,.2f}",
                'Precio Mínimo': f"${sens_chofer['lower_bound']:,.2f}",
                'Precio Máximo': f"${sens_chofer['upper_bound']:,.2f}",
                'Margen de Variación': f"+${sens_chofer['aumento_permitido']:,.2f} (+{sens_chofer['aumento_permitido_porcentaje']:.1f}%)"
            },
            {
                'Variable': 'Precio Base ($/pedido)',
                'Valor Actual': f"${sens_base['precio_base_actual']:,.2f}",
                'Costo/Ingreso Parcial': f"Ingreso: ${sens_base['ingreso_base_actual']:,.2f}",
                'Precio Mínimo': f"${sens_base['lower_bound']:,.2f}",
                'Precio Máximo': '∞',
                'Margen de Variación': f"-${sens_base['margen_disponible']:,.2f} (-{sens_base['margen_disponible_porcentaje']:.1f}%)"
            },
            {
                'Variable': 'Precio por km ($/km)',
                'Valor Actual': f"${sens_por_km['precio_por_km_actual']:,.2f}",
                'Costo/Ingreso Parcial': f"Ingreso: ${sens_por_km['ingreso_variable_actual']:,.2f}",
                'Precio Mínimo': f"${sens_por_km['lower_bound']:,.2f}",
                'Precio Máximo': '∞',
                'Margen de Variación': f"-${sens_por_km['margen_disponible']:,.2f} (-{sens_por_km['margen_disponible_porcentaje']:.1f}%)"
            }
        ]

        return pd.DataFrame(data)

    def obtener_interpretaciones(self) -> List[str]:
        """
        Genera interpretaciones en lenguaje natural de los resultados.

        Returns:
            Lista de strings con interpretaciones
        """
        sens_nafta = self.analizar_sensibilidad_nafta()
        sens_chofer = self.analizar_sensibilidad_costo_chofer()
        sens_base = self.analizar_sensibilidad_precio_base()
        sens_por_km = self.analizar_sensibilidad_precio_por_km()
        margen = self.calcular_margen()
        ingresos = self.calcular_ingresos()
        costos = self.calcular_costos_operacion()

        interpretaciones = []

        # Interpretación de rentabilidad general
        if margen['margen_total'] > 0:
            interpretaciones.append(
                f"✓ La operación es RENTABLE con un margen de \\${margen['margen_total']:,.2f} "
                f"({margen['rentabilidad_porcentaje']:.1f}% de rentabilidad)"
            )
        elif margen['margen_total'] == 0:
            interpretaciones.append(
                "⚠ La operación está en PUNTO DE EQUILIBRIO (margen = 0)"
            )
        else:
            interpretaciones.append(
                f"✗ La operación tiene PÉRDIDA de \\${abs(margen['margen_total']):,.2f} "
                f"({margen['rentabilidad_porcentaje']:.1f}%)"
            )

        # Detalle de ingresos y costos
        interpretaciones.append(
            f"💵 **Composición de Ingresos**: "
            f"Base \\${ingresos['ingreso_base']:,.2f} ({self.num_pedidos} pedidos × \\${self.precio_base_por_pedido:,.2f}) + "
            f"Variable \\${ingresos['ingreso_variable']:,.2f} ({self.distancia_total_km:.1f} km × \\${self.precio_por_km:,.2f}/km)"
        )

        interpretaciones.append(
            f"💰 **Composición de Costos**: "
            f"Nafta \\${costos['costo_total_nafta']:,.2f} + "
            f"Chofer \\${costos['costo_total_chofer']:,.2f} ({costos['tiempo_total_horas']:.1f}h × \\${self.costo_chofer_por_hora:,.2f}/h)"
        )

        # Interpretación de sensibilidad de nafta
        if sens_nafta['aumento_permitido'] > 0:
            interpretaciones.append(
                f"⛽ **Precio Nafta**: Puede aumentar hasta \\${sens_nafta['aumento_permitido']:,.2f}/L más "
                f"(+{sens_nafta['aumento_permitido_porcentaje']:.1f}%) sin generar pérdidas. "
                f"Rango: \\${sens_nafta['lower_bound']:,.2f}/L - \\${sens_nafta['upper_bound']:,.2f}/L"
            )
        else:
            interpretaciones.append(
                f"⛽ **Precio Nafta**: El precio actual (\\${sens_nafta['precio_nafta_actual']:,.2f}/L) "
                f"supera el punto de equilibrio (\\${sens_nafta['precio_nafta_breakeven']:,.2f}/L). "
                f"Se necesita reducir costos o aumentar precios al cliente."
            )

        # Interpretación de sensibilidad del costo del chofer
        if sens_chofer['aumento_permitido'] > 0:
            interpretaciones.append(
                f"🚗 **Costo Chofer**: Puede aumentar hasta \\${sens_chofer['aumento_permitido']:,.2f}/h más "
                f"(+{sens_chofer['aumento_permitido_porcentaje']:.1f}%) sin generar pérdidas. "
                f"Rango: \\${sens_chofer['lower_bound']:,.2f}/h - \\${sens_chofer['upper_bound']:,.2f}/h"
            )
        else:
            interpretaciones.append(
                f"🚗 **Costo Chofer**: El costo actual (\\${sens_chofer['costo_chofer_actual']:,.2f}/h) "
                f"supera el punto de equilibrio (\\${sens_chofer['costo_chofer_breakeven']:,.2f}/h). "
                f"Se necesita reducir costos o aumentar precios al cliente."
            )

        # Interpretación de sensibilidad de precio base
        if sens_base['lower_bound'] <= 0.01:  # Precio mínimo es prácticamente $0
            interpretaciones.append(
                f"📦 **Precio Base por Pedido**: El ingreso por precio por km (\\${ingresos['ingreso_variable']:,.2f}) "
                f"ya cubre todos los costos (\\${costos['costo_total']:,.2f}). "
                f"Podrías bajar el precio base hasta \\$0 y aún ser rentable. "
                f"Margen disponible: \\${sens_base['margen_disponible']:,.2f}/pedido ({sens_base['margen_disponible_porcentaje']:.1f}%)"
            )
        elif sens_base['margen_disponible'] > 0:
            interpretaciones.append(
                f"📦 **Precio Base por Pedido**: Manteniendo el precio por km en \\${self.precio_por_km:,.2f}/km, "
                f"el precio base mínimo es \\${sens_base['lower_bound']:,.2f}/pedido. "
                f"Actualmente (\\${sens_base['precio_base_actual']:,.2f}/pedido) tienes un margen de \\${sens_base['margen_disponible']:,.2f}/pedido "
                f"({sens_base['margen_disponible_porcentaje']:.1f}%)."
            )
        else:
            interpretaciones.append(
                f"📦 **Precio Base por Pedido**: El precio actual (\\${sens_base['precio_base_actual']:,.2f}/pedido) "
                f"está por debajo del mínimo requerido. "
                f"Manteniendo el precio por km actual, debes cobrar al menos \\${sens_base['lower_bound']:,.2f}/pedido."
            )

        # Interpretación de sensibilidad de precio por km
        if sens_por_km['lower_bound'] <= 0.01:  # Precio mínimo es prácticamente $0
            interpretaciones.append(
                f"📏 **Precio por km**: El ingreso por precio base (\\${ingresos['ingreso_base']:,.2f}) "
                f"ya cubre todos los costos (\\${costos['costo_total']:,.2f}). "
                f"Podrías bajar el precio por km hasta \\$0 y aún ser rentable. "
                f"Margen disponible: \\${sens_por_km['margen_disponible']:,.2f}/km ({sens_por_km['margen_disponible_porcentaje']:.1f}%)"
            )
        elif sens_por_km['margen_disponible'] > 0:
            interpretaciones.append(
                f"📏 **Precio por km**: Manteniendo el precio base en \\${self.precio_base_por_pedido:,.2f}/pedido, "
                f"el precio por km mínimo es \\${sens_por_km['lower_bound']:,.2f}/km. "
                f"Actualmente (\\${sens_por_km['precio_por_km_actual']:,.2f}/km) tienes un margen de \\${sens_por_km['margen_disponible']:,.2f}/km "
                f"({sens_por_km['margen_disponible_porcentaje']:.1f}%)."
            )
        else:
            interpretaciones.append(
                f"📏 **Precio por km**: El precio actual (\\${sens_por_km['precio_por_km_actual']:,.2f}/km) "
                f"está por debajo del mínimo requerido. "
                f"Manteniendo el precio base actual, debes cobrar al menos \\${sens_por_km['lower_bound']:,.2f}/km."
            )

        return interpretaciones


# Función auxiliar para formatear moneda
def formatear_moneda(valor: float, escapar_markdown: bool = True) -> str:
    """
    Formatea un valor numérico como moneda.

    Args:
        valor: Valor numérico a formatear
        escapar_markdown: Si True, escapa el símbolo $ para Markdown

    Returns:
        String formateado como moneda
    """
    if escapar_markdown:
        return f"\\${valor:,.2f}"
    else:
        return f"${valor:,.2f}"

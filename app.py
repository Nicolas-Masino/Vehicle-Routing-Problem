import streamlit as st
import pandas as pd
from utils.map import generar_mapa
from utils.fake import optimizar_ruta_fake

st.set_page_config(page_title="Optimizador de Rutas - Andreani", layout="wide")

st.title("Optimizador de Rutas de Entrega - Andreani")

st.sidebar.header("Configuración")
modo_carga = st.sidebar.radio("Método de carga de pedidos:", ["Manual", "Archivo CSV"])

if modo_carga == "Manual":
    st.sidebar.subheader("Agregar pedido")
    with st.sidebar.form(key='manual_form'):
        direccion = st.text_input("Dirección")
        lat = st.number_input("Latitud", format="%.6f")
        lon = st.number_input("Longitud", format="%.6f")
        agregar = st.form_submit_button("Agregar")
    if "pedidos" not in st.session_state:
        st.session_state["pedidos"] = []
    if agregar:
        st.session_state["pedidos"].append({"direccion": direccion, "lat": lat, "lon": lon})
        st.success("Pedido agregado exitosamente")

    pedidos_df = pd.DataFrame(st.session_state["pedidos"])

else:
    archivo = st.sidebar.file_uploader("Subir archivo CSV", type=["csv"])
    if archivo:
        pedidos_df = pd.read_csv(archivo)
        st.success(f"Archivo cargado con {len(pedidos_df)} pedidos.")
    else:
        pedidos_df = pd.DataFrame()

if not pedidos_df.empty:
    st.subheader("Pedidos cargados")
    st.dataframe(pedidos_df, use_container_width=True)

    # Panel de configuración de optimización
    st.sidebar.header("Parámetros de optimización")
    tipo_vehiculo = st.sidebar.selectbox("Tipo de vehículo", ["Moto", "Camioneta", "Camión"])
    hora_inicio = st.sidebar.time_input("Hora de inicio")
    velocidad_prom = st.sidebar.slider("Velocidad promedio (km/h)", 20, 120, 60)

    # Simular optimización
    if st.button("Optimizar Ruta"):
        st.info("Calculando ruta óptima (simulada)...")
        ruta, distancia_total, tiempo_total = optimizar_ruta_fake(pedidos_df, velocidad_prom)

        st.success("Optimización completada")

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Distancia total (km)", f"{distancia_total:.2f}")
        with col2:
            st.metric("Tiempo estimado (h)", f"{tiempo_total:.2f}")

        mapa = generar_mapa(ruta)
        st.components.v1.html(mapa._repr_html_(), height=600)
else:
    st.warning("Cargá pedidos manualmente o desde un archivo CSV para comenzar.")


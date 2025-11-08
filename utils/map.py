import folium

def generar_mapa(ruta):
    if ruta.empty:
        return folium.Map(location=[-34.6037, -58.3816], zoom_start=12)  # Buenos Aires

    m = folium.Map(location=[ruta["lat"].mean(), ruta["lon"].mean()], zoom_start=12)
    for _, row in ruta.iterrows():
        folium.Marker(
            location=[row["lat"], row["lon"]],
            popup=row["direccion"],
            tooltip=row["direccion"]
        ).add_to(m)

    # Dibujar líneas de la ruta
    coords = ruta[["lat", "lon"]].values.tolist()
    folium.PolyLine(coords, color="blue", weight=2.5, opacity=0.8).add_to(m)
    return m

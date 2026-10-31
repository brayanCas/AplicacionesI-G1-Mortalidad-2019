"""Funciones que crean cada gráfico con Plotly Express.

Cada función recibe la tabla ya calculada (ver datos.py) y devuelve una figura.
"""
import plotly.express as px

from datos import GRUPOS_EDAD

# Colores de la aplicación
AZUL = "#1F497D"
DORADO = "#FFC000"
COLORES_SEXO = {"Masculino": AZUL, "Femenino": DORADO, "Indeterminado": "#7F7F7F"}


def dar_formato(figura, alto=420):
    """Estilo común para todos los gráficos."""
    figura.update_layout(template="plotly_white", height=alto,
                         margin=dict(l=40, r=20, t=50, b=40))
    return figura


def crear_mapa(tabla):
    """Mapa de burbujas: el tamaño y el color indican el total de muertes."""
    figura = px.scatter_geo(
        tabla, lat="Latitud", lon="Longitud", size="Muertes", color="Muertes",
        hover_name="Departamento", scope="south america", size_max=40,
        color_continuous_scale="YlOrRd",
        title="Muertes por departamento, Colombia 2019",
    )
    figura.update_geos(fitbounds="locations", showcountries=True, showland=True,
                       landcolor="#F2F2F2")
    return dar_formato(figura, alto=520)


def crear_lineas(tabla, titulo):
    """Gráfico de líneas: muertes por mes."""
    figura = px.line(tabla, x="Mes", y="Muertes", markers=True, title=titulo)
    figura.update_traces(line_color=AZUL)
    return dar_formato(figura)


def crear_barras_violentas(tabla):
    """Gráfico de barras: ciudades con más homicidios por arma de fuego."""
    figura = px.bar(tabla, x="Ciudad", y="Homicidios", text="Homicidios",
                    title="5 ciudades con más homicidios por arma de fuego (X95)")
    figura.update_traces(marker_color=AZUL, textposition="outside")
    return dar_formato(figura)


def crear_circular(tabla):
    """Gráfico circular: las 10 ciudades con menos muertes."""
    figura = px.pie(tabla, names="Ciudad", values="Muertes",
                    title="10 ciudades con menor mortalidad (menos muertes registradas)")
    return dar_formato(figura)


def crear_barras_apiladas(tabla):
    """Barras apiladas: muertes por sexo en cada departamento."""
    orden = tabla.groupby("Departamento")["Muertes"].sum().sort_values(ascending=False).index
    figura = px.bar(tabla, x="Departamento", y="Muertes", color="Sexo", barmode="stack",
                    color_discrete_map=COLORES_SEXO,
                    category_orders={"Departamento": list(orden)},
                    title="Muertes por sexo en cada departamento")
    figura.update_xaxes(tickangle=-45)
    return dar_formato(figura, alto=520)


def crear_histograma(tabla, titulo):
    """Histograma: muertes por categoría de edad (ordenadas de menor a mayor edad)."""
    orden = [nombre for nombre, _, _ in GRUPOS_EDAD]
    figura = px.histogram(tabla, x="Categoría de edad", y="Muertes", histfunc="sum",
                          category_orders={"Categoría de edad": orden}, title=titulo)
    figura.update_traces(marker_color=AZUL)
    figura.update_layout(bargap=0.05, yaxis_title="Muertes")
    figura.update_xaxes(tickangle=-40)
    return dar_formato(figura, alto=520)

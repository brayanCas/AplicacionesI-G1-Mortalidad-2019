"""Aplicación web con Dash: mortalidad en Colombia, año 2019.

Para ejecutarla en el computador:   python app.py
Luego abrir en el navegador:        http://127.0.0.1:8050
"""
from dash import Dash, Input, Output, dash_table, dcc, html

import datos
import graficos

# ---------------------------------------------------------------------------
# 1. Cargar los datos y calcular las tablas que no cambian
# ---------------------------------------------------------------------------
muertes, causas, divipola = datos.cargar_datos()

tabla_mapa = datos.muertes_por_departamento(muertes, divipola)
tabla_violentas = datos.ciudades_mas_violentas(muertes, divipola)
tabla_menor_mortalidad = datos.ciudades_menor_mortalidad(muertes, divipola)
tabla_causas = datos.principales_causas(muertes, causas)
tabla_sexo = datos.muertes_por_sexo_y_departamento(muertes, divipola)

# En la tabla de causas se muestran los números con punto de miles (35.088)
tabla_causas["Total de casos"] = tabla_causas["Total de casos"].map(
    lambda numero: f"{numero:,}".replace(",", "."))

# ---------------------------------------------------------------------------
# 2. Crear la aplicación
# ---------------------------------------------------------------------------
app = Dash(__name__, title="Mortalidad en Colombia 2019")
server = app.server  # lo necesita el servidor (gunicorn) al desplegar en Render


def tarjeta(*contenido):
    """Caja blanca que contiene un gráfico o una tabla."""
    return html.Div(list(contenido), className="tarjeta")


# ---------------------------------------------------------------------------
# 3. Diseño de la página
# ---------------------------------------------------------------------------
total_muertes = f"{len(muertes):,}".replace(",", ".")

app.layout = html.Div([
    # Contenedor Principal del Encabezado (Texto + Imagen)
    html.Div([
        # Bloque de texto a la izquierda
        html.Div([
            html.H1("Mortalidad en Colombia, 2019"),
            html.P(f"{total_muertes} defunciones no fetales registradas por el DANE (Estadísticas Vitales)"),
            html.P([
                "Brayan Alberto Castellanos Vargas", 
                html.Br(), 
                "Aplicaciones I"
            ]),
        ], className="texto-encabezado"),
        
        # Imagen de la Universidad
html.Img(
            src="/assets/logoLASALLE.webp", 
            className="logo-universidad"
        )
    ], className="encabezado"),
        
    

    html.Div([
        html.Div([
            html.Label("Departamento (filtra el gráfico de líneas y el histograma):"),
            dcc.Dropdown(id="filtro-departamento", options=datos.lista_departamentos(divipola),
                         value="TODOS", clearable=False),
        ], className="filtro"),

        html.Div([
            tarjeta(dcc.Graph(figure=graficos.crear_mapa(tabla_mapa))),
            tarjeta(html.H3("10 principales causas de muerte"),
                    dash_table.DataTable(
                        data=tabla_causas.to_dict("records"),
                        columns=[{"name": columna, "id": columna} for columna in tabla_causas.columns],
                        style_header={"backgroundColor": graficos.AZUL, "color": "white",
                                      "fontWeight": "bold"},
                        style_cell={"textAlign": "left", "padding": "6px", "whiteSpace": "normal",
                                    "height": "auto", "fontFamily": "Arial", "fontSize": "13px"},
                        style_cell_conditional=[{"if": {"column_id": "Total de casos"},
                                                 "textAlign": "right"}],
                    )),
            tarjeta(dcc.Graph(id="grafico-lineas")),
            tarjeta(dcc.Graph(id="grafico-histograma")),
            tarjeta(dcc.Graph(figure=graficos.crear_barras_violentas(tabla_violentas))),
            tarjeta(dcc.Graph(figure=graficos.crear_circular(tabla_menor_mortalidad))),
        ], className="cuadricula"),

        tarjeta(dcc.Graph(figure=graficos.crear_barras_apiladas(tabla_sexo))),

        html.P("Fuente: DANE, Estadísticas Vitales 2019 (NoFetal2019, CodigosDeMuerte y Divipola).",
               className="pie"),
    ], className="contenido"),
])


# ---------------------------------------------------------------------------
# 4. Interactividad: al cambiar el departamento se actualizan dos gráficos
# ---------------------------------------------------------------------------
@app.callback(
    Output("grafico-lineas", "figure"),
    Output("grafico-histograma", "figure"),
    Input("filtro-departamento", "value"),
)
def actualizar_graficos(codigo_departamento):
    """Recalcula el gráfico de líneas y el histograma para el departamento elegido."""
    muertes_elegidas = datos.filtrar_por_departamento(muertes, codigo_departamento)

    if codigo_departamento == "TODOS":
        lugar = "Colombia"
    else:
        lugar = divipola.loc[divipola["COD_DEPARTAMENTO"] == codigo_departamento,
                             "DEPARTAMENTO"].iloc[0]

    figura_lineas = graficos.crear_lineas(
        datos.muertes_por_mes(muertes_elegidas), f"Muertes por mes en {lugar}, 2019")
    figura_histograma = graficos.crear_histograma(
        datos.muertes_por_grupo_edad(muertes_elegidas), f"Muertes por categoría de edad en {lugar}")
    return figura_lineas, figura_histograma


# ---------------------------------------------------------------------------
# 5. Ejecutar la aplicación
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)

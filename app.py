"""Aplicación web con Streamlit: mortalidad en Colombia, año 2019.

Para ejecutarla en el computador:    streamlit run app.py
Luego se abrirá automáticamente en el navegador.
"""
import streamlit as st
import datos
import graficos
import base64

def img_a_base64(ruta_imagen):
    try:
        with open(ruta_imagen, "rb") as archivo:
            encoded = base64.b64encode(archivo.read()).decode("utf-8")
        return f"data:image/webp;base64,{encoded}"
    except Exception:
        return ""

logo_base64 = img_a_base64("assets/logoLASALLE.webp")

# ---------------------------------------------------------------------------
# 1. Configuración inicial de la página
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Mortalidad en Colombia 2019",
    page_icon="📊",
    layout="wide"
)
st.markdown("""
<style>
    /* 1. Estilo del Encabezado Azul Institucional */
    .encabezado-personalizado {
        background-color: #1b365d;
        color: white;
        padding: 30px;
        border-radius: 12px;
        margin-bottom: 25px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .encabezado-personalizado h1 {
        color: #f39c12 !important; /* Color dorado para el título principal */
        margin-bottom: 10px;
        font-size: 2rem;
    }
    .encabezado-personalizado p {
        color: #ffffff;
        margin: 0;
    }

    /* 2. Redondear y mejorar las Tarjetas (Containers) */
    div[data-testid="stVerticalBlock"] div[data-testid="stContainer"] {
        background-color: #ffffff;
        border-radius: 12px !important;
        padding: 15px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        border: 1px solid #e1e8ed !important;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# 2. Cargar los datos y calcular las tablas que no cambian
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

total_muertes = f"{len(muertes):,}".replace(",", ".")

# ---------------------------------------------------------------------------
# 3. Diseño de la interfaz (Layout)
# ---------------------------------------------------------------------------

# Encabezado con contenedor estilizado azul institucional y logo en Base64
st.markdown(f"""
<div class="encabezado-personalizado">
    <div>
        <h1>Mortalidad en Colombia, 2019</h1>
        <p><b>{total_muertes}</b> defunciones no fetales registradas por el DANE (Estadísticas Vitales)</p>
        <p style="margin-top: 8px; font-size: 0.95rem;">Brayan Alberto Castellanos Vargas<br>Aplicaciones I</p>
    </div>
    <div>
        <img src="{logo_base64}" style="max-height: 75px; width: auto; background: white; padding: 6px 10px; border-radius: 8px;" />
    </div>
</div>
""", unsafe_allow_html=True)

st.divider()

# ---------------------------------------------------------------------------
# 4. Filtro interactivo de Departamento
# ---------------------------------------------------------------------------
opciones_deptos = datos.lista_departamentos(divipola)

# Asegurarnos de extraer correctamente los valores si vienen en formato dict
lista_opciones_limpia = []
for item in opciones_deptos:
    if isinstance(item, dict):
        lista_opciones_limpia.append(item.get("label", str(item)))
    else:
        lista_opciones_limpia.append(str(item))

seleccion_usuario = st.selectbox(
    "Departamento (filtra el gráfico de líneas y el histograma):",
    options=lista_opciones_limpia,
    index=0
)

# Convertir la selección de vuelta al formato o código que espera tu función de datos.py
if isinstance(opciones_deptos[0], dict):
    # Buscamos el 'value' correspondiente al 'label' seleccionado
    codigo_departamento = next(
        (item["value"] for item in opciones_deptos if item["label"] == seleccion_usuario), 
        "TODOS"
    )
else:
    codigo_departamento = seleccion_usuario

# ---------------------------------------------------------------------------
# 5. Lógica de filtrado en tiempo real para los gráficos interactivos
# ---------------------------------------------------------------------------
muertes_elegidas = datos.filtrar_por_departamento(muertes, codigo_departamento)

if codigo_departamento == "TODOS":
    lugar = "Colombia"
else:
    lugar = divipola.loc[
        divipola["COD_DEPARTAMENTO"] == codigo_departamento, "DEPARTAMENTO"
    ].iloc[0]

figura_lineas = graficos.crear_lineas(
    datos.muertes_por_mes(muertes_elegidas), f"Muertes por mes en {lugar}, 2019"
)
figura_histograma = graficos.crear_histograma(
    datos.muertes_por_grupo_edad(muertes_elegidas), f"Muertes por categoría de edad en {lugar}"
)

# ---------------------------------------------------------------------------
# 6. Cuadrícula de Contenido (Tarjetas con gráficos y tablas)
# ---------------------------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.plotly_chart(graficos.crear_mapa(tabla_mapa), use_container_width=True)
        
    with st.container(border=True):
        st.plotly_chart(graficos.crear_barras_violentas(tabla_violentas), use_container_width=True)
        
    with st.container(border=True):
        st.plotly_chart(graficos.crear_circular(tabla_menor_mortalidad), use_container_width=True)

with col2:
    with st.container(border=True):
        st.markdown("### 10 principales causas de muerte")
        # Reemplazo de DataTable por st.dataframe optimizado para Streamlit
        st.dataframe(
            tabla_causas, 
            use_container_width=True, 
            hide_index=True
        )
        
    with st.container(border=True):
        st.plotly_chart(figura_lineas, use_container_width=True)
        
    with st.container(border=True):
        st.plotly_chart(figura_histograma, use_container_width=True)

# Tarjeta a ancho completo inferior
with st.container(border=True):
    st.plotly_chart(graficos.crear_barras_apiladas(tabla_sexo), use_container_width=True)

# Pie de página
st.markdown("---")
st.caption("Fuente: DANE, Estadísticas Vitales 2019 (NoFetal2019, CodigosDeMuerte y Divipola).")
"""Funciones para cargar los datos y calcular las tablas de cada gráfico.

Cada función recibe los datos de mortalidad y devuelve una tabla (DataFrame)
pequeña y lista para graficar.
"""
from pathlib import Path

import pandas as pd

CARPETA_DATOS = Path(__file__).parent / "data"

NOMBRES_MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio",
                 "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

NOMBRES_SEXO = {"1": "Masculino", "2": "Femenino", "3": "Indeterminado"}

# Categorías de edad según la tabla de la actividad: (nombre, código inicial, código final)
GRUPOS_EDAD = [
    ("Mortalidad neonatal (menor de 1 mes)", 0, 4),
    ("Mortalidad infantil (1 a 11 meses)", 5, 6),
    ("Primera infancia (1 a 4 años)", 7, 8),
    ("Niñez (5 a 14 años)", 9, 10),
    ("Adolescencia (15 a 19 años)", 11, 11),
    ("Juventud (20 a 29 años)", 12, 13),
    ("Adultez temprana (30 a 44 años)", 14, 16),
    ("Adultez intermedia (45 a 59 años)", 17, 19),
    ("Vejez (60 a 84 años)", 20, 24),
    ("Longevidad (85 a 100+ años)", 25, 28),
    ("Edad desconocida", 29, 29),
]


def cargar_datos():
    """Lee los tres archivos CSV de la carpeta data/ y los devuelve."""
    muertes = pd.read_csv(CARPETA_DATOS / "muertes_2019.csv", dtype=str)
    muertes["MES"] = muertes["MES"].astype(int)
    muertes["GRUPO_EDAD1"] = muertes["GRUPO_EDAD1"].astype(int)

    causas = pd.read_csv(CARPETA_DATOS / "causas_muerte.csv", dtype=str)
    divipola = pd.read_csv(CARPETA_DATOS / "divipola.csv",
                           dtype={"COD_DANE": str, "COD_DEPARTAMENTO": str})
    return muertes, causas, divipola


def lista_departamentos(divipola):
    """Opciones para el menú desplegable: 'Todos' y luego cada departamento."""
    departamentos = divipola[["COD_DEPARTAMENTO", "DEPARTAMENTO"]].drop_duplicates()
    departamentos = departamentos.sort_values("DEPARTAMENTO")
    opciones = [{"label": "Todos los departamentos", "value": "TODOS"}]
    for _, fila in departamentos.iterrows():
        opciones.append({"label": fila["DEPARTAMENTO"], "value": fila["COD_DEPARTAMENTO"]})
    return opciones


def filtrar_por_departamento(muertes, codigo_departamento):
    """Devuelve solo las muertes del departamento elegido (o todas)."""
    if codigo_departamento == "TODOS":
        return muertes
    return muertes[muertes["COD_DEPARTAMENTO"] == codigo_departamento]


def muertes_por_departamento(muertes, divipola):
    """Total de muertes por departamento, con su ubicación para el mapa.

    La ubicación de cada departamento es el promedio de las coordenadas de sus municipios.
    """
    total = muertes.groupby("COD_DEPARTAMENTO").size().reset_index(name="Muertes")
    ubicacion = divipola.groupby("COD_DEPARTAMENTO").agg(
        Departamento=("DEPARTAMENTO", "first"),
        Latitud=("LATITUD", "mean"),
        Longitud=("LONGITUD", "mean"),
    ).reset_index()
    return total.merge(ubicacion, on="COD_DEPARTAMENTO")


def muertes_por_mes(muertes):
    """Total de muertes de cada mes (enero a diciembre)."""
    por_mes = muertes.groupby("MES").size().reindex(range(1, 13), fill_value=0)
    return pd.DataFrame({"Mes": NOMBRES_MESES, "Muertes": por_mes.values})


def ciudades_mas_violentas(muertes, divipola, cantidad=5):
    """Ciudades con más homicidios por arma de fuego (código CIE-10 que empieza por X95)."""
    homicidios = muertes[muertes["COD_MUERTE"].str.startswith("X95")]
    total = homicidios.groupby("COD_DANE").size().reset_index(name="Homicidios")
    total = total.merge(divipola[["COD_DANE", "MUNICIPIO"]], on="COD_DANE")
    total = total.rename(columns={"MUNICIPIO": "Ciudad"})
    return total.sort_values("Homicidios", ascending=False).head(cantidad)


def ciudades_menor_mortalidad(muertes, divipola, cantidad=10):
    """Ciudades con menos muertes registradas (se ignoran las que tienen cero).

    Si varias ciudades empatan, se ordenan alfabéticamente.
    """
    total = muertes.groupby("COD_DANE").size().reset_index(name="Muertes")
    nombres = divipola[["COD_DANE", "MUNICIPIO", "DEPARTAMENTO"]]
    total = total.merge(nombres, on="COD_DANE")
    total["Ciudad"] = total["MUNICIPIO"] + " (" + total["DEPARTAMENTO"] + ")"
    total = total.sort_values(["Muertes", "Ciudad"], ascending=[True, True])
    return total.head(cantidad)[["Ciudad", "Muertes"]]


def principales_causas(muertes, causas, cantidad=10):
    """Las causas de muerte más frecuentes con su código, nombre y total."""
    total = muertes.groupby("COD_MUERTE").size().reset_index(name="Total de casos")
    total = total.sort_values("Total de casos", ascending=False).head(cantidad)
    total = total.merge(causas, left_on="COD_MUERTE", right_on="codigo", how="left")
    total = total.rename(columns={"COD_MUERTE": "Código", "nombre": "Causa de muerte"})
    return total[["Código", "Causa de muerte", "Total de casos"]]


def muertes_por_sexo_y_departamento(muertes, divipola):
    """Muertes de cada sexo en cada departamento (para las barras apiladas)."""
    total = muertes.groupby(["COD_DEPARTAMENTO", "SEXO"]).size().reset_index(name="Muertes")
    total["Sexo"] = total["SEXO"].map(NOMBRES_SEXO)
    nombres = divipola[["COD_DEPARTAMENTO", "DEPARTAMENTO"]].drop_duplicates()
    total = total.merge(nombres, on="COD_DEPARTAMENTO")
    return total.rename(columns={"DEPARTAMENTO": "Departamento"})[["Departamento", "Sexo", "Muertes"]]


def nombre_grupo_edad(codigo):
    """Convierte un código GRUPO_EDAD1 (0 a 29) en su categoría de edad."""
    for nombre, inicio, fin in GRUPOS_EDAD:
        if inicio <= codigo <= fin:
            return nombre
    return "Edad desconocida"


def muertes_por_grupo_edad(muertes):
    """Total de muertes en cada categoría de edad, en orden de edad."""
    categorias = muertes["GRUPO_EDAD1"].map(nombre_grupo_edad)
    orden = [nombre for nombre, _, _ in GRUPOS_EDAD]
    total = categorias.value_counts().reindex(orden, fill_value=0)
    return pd.DataFrame({"Categoría de edad": orden, "Muertes": total.values})

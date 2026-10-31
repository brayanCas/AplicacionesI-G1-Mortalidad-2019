"""Convierte los archivos Excel del DANE en archivos CSV livianos.

Solo hay que ejecutarlo UNA vez (o cuando cambien los archivos de origen):

    python preparar_datos.py

Lee los Excel que están en la carpeta "datos_originales" y crea tres archivos
CSV dentro de la carpeta "data". La aplicación usa solo esos CSV porque se
cargan en menos de un segundo, mientras que el Excel de mortalidad (19 MB)
tarda más de un minuto y gasta mucha memoria (importante en servidores gratuitos).

Requiere:  pip install pandas openpyxl
"""
from pathlib import Path

import pandas as pd

CARPETA_ORIGEN = Path(__file__).parent / "datos_originales"
CARPETA_DESTINO = Path(__file__).parent / "data"

ARCHIVO_MORTALIDAD = "Anexo1_NoFetal2019_CE_15-03-23.xlsx"
ARCHIVO_CAUSAS = "Anexo2_CodigosDeMuerte_CE_15-03-23.xlsx"
ARCHIVO_DIVIPOLA = "Divipola_CE_.xlsx"

# Nombres demasiado largos para los gráficos
NOMBRES_CORTOS = {
    "ARCHIPIÉLAGO DE SAN ANDRÉS, PROVIDENCIA Y SANTA CATALINA": "SAN ANDRÉS Y PROVIDENCIA",
    "BOGOTÁ, D.C.": "BOGOTÁ D.C.",
}


def nombre_bonito(nombres):
    """Pasa de MAYÚSCULAS a Formato Título y deja en minúscula 'de', 'del', 'y', etc."""
    nombres = nombres.str.title()
    for palabra in [" De ", " Del ", " La ", " Las ", " Los ", " Y "]:
        nombres = nombres.str.replace(palabra, palabra.lower(), regex=False)
    return nombres


def preparar_muertes():
    """Deja solo las columnas que usa la aplicación."""
    print("Leyendo mortalidad (puede tardar un par de minutos)...")
    muertes = pd.read_excel(CARPETA_ORIGEN / ARCHIVO_MORTALIDAD,
                            sheet_name="No_Fetales_2019", dtype=str)
    columnas = ["COD_DANE", "COD_DEPARTAMENTO", "MES", "SEXO", "GRUPO_EDAD1", "COD_MUERTE"]
    muertes = muertes[columnas]
    muertes.to_csv(CARPETA_DESTINO / "muertes_2019.csv", index=False)
    print(f"  muertes_2019.csv: {len(muertes)} filas")


def preparar_causas():
    """Crea el catálogo código -> nombre de la causa.

    En los datos, algunas causas vienen con 3 caracteres (por ejemplo I10) y
    en el catálogo aparecen como I10X. Aquí se deja el código tal como viene
    en los datos de mortalidad.
    """
    causas = pd.read_excel(CARPETA_ORIGEN / ARCHIVO_CAUSAS, header=None, dtype=str, skiprows=9)
    causas = causas.iloc[:, [2, 4, 5]]
    causas.columns = ["codigo_3", "codigo_4", "nombre"]
    termina_en_x = causas["codigo_4"].str.endswith("X")
    causas["codigo"] = causas["codigo_4"].where(~termina_en_x, causas["codigo_3"])
    causas = causas[["codigo", "nombre"]].drop_duplicates("codigo")
    causas.to_csv(CARPETA_DESTINO / "causas_muerte.csv", index=False)
    print(f"  causas_muerte.csv: {len(causas)} filas")


def preparar_divipola():
    """Une los nombres de municipios (Hoja1) con sus coordenadas (Hoja3)."""
    nombres = pd.read_excel(CARPETA_ORIGEN / ARCHIVO_DIVIPOLA, sheet_name="Hoja1", dtype=str)
    nombres = nombres[["COD_DANE", "COD_DEPARTAMENTO", "DEPARTAMENTO", "MUNICIPIO"]]

    coordenadas = pd.read_excel(CARPETA_ORIGEN / ARCHIVO_DIVIPOLA, sheet_name="Hoja3",
                                header=None, dtype=str, skiprows=2)
    coordenadas = coordenadas.iloc[:, [2, 5, 6]]
    coordenadas.columns = ["COD_DANE", "LONGITUD", "LATITUD"]
    # En el Excel los decimales vienen con coma (-75,58) y hay que pasarlos a punto
    for columna in ["LONGITUD", "LATITUD"]:
        coordenadas[columna] = coordenadas[columna].str.replace(",", ".").astype(float)

    divipola = nombres.merge(coordenadas, on="COD_DANE", how="inner")
    divipola["DEPARTAMENTO"] = nombre_bonito(divipola["DEPARTAMENTO"].replace(NOMBRES_CORTOS))
    divipola["MUNICIPIO"] = nombre_bonito(divipola["MUNICIPIO"])
    divipola.to_csv(CARPETA_DESTINO / "divipola.csv", index=False)
    print(f"  divipola.csv: {len(divipola)} filas")


if __name__ == "__main__":
    CARPETA_DESTINO.mkdir(exist_ok=True)
    preparar_muertes()
    preparar_causas()
    preparar_divipola()
    print("Listo. Ya puedes ejecutar:  python app.py")

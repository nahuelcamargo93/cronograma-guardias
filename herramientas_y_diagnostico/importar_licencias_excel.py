"""
importar_licencias_excel.py — Importa LPP/LAR desde un Excel a la BD.

Formato esperado del Excel (licencias_input.xlsx):
  Columnas: Persona | Tipo | Fecha_inicio | Fecha_fin

Las fechas pueden estar en formato YYYY-MM-DD o DD/MM/YYYY.
Es seguro de correr varias veces: duplicados se omiten automaticamente.
"""

import pandas as pd
from datetime import datetime
import db as database

ARCHIVO_EXCEL = "licencias_input.xlsx"


def normalizar_fecha(valor):
    """Convierte fecha a formato ISO YYYY-MM-DD independientemente del formato de entrada."""
    if pd.isna(valor):
        raise ValueError("Fecha vacia")
    if isinstance(valor, (datetime,)):
        return valor.strftime("%Y-%m-%d")
    s = str(valor).strip()
    # Probar formatos comunes
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    raise ValueError(f"Formato de fecha no reconocido: '{s}'")


def importar():
    database.inicializar_db()

    try:
        df = pd.read_excel(ARCHIVO_EXCEL)
    except FileNotFoundError:
        print(f"[ERROR] No se encontro el archivo '{ARCHIVO_EXCEL}'.")
        return

    # Validar columnas
    columnas_requeridas = {"Persona", "Tipo", "Fecha_inicio", "Fecha_fin"}
    if not columnas_requeridas.issubset(df.columns):
        faltantes = columnas_requeridas - set(df.columns)
        print(f"[ERROR] Faltan columnas en el Excel: {faltantes}")
        return

    print("=" * 60)
    print(f"  IMPORTANDO LICENCIAS DESDE '{ARCHIVO_EXCEL}'")
    print("=" * 60)

    insertadas = 0
    omitidas = 0
    errores = 0

    for i, row in df.iterrows():
        nombre = str(row["Persona"]).strip()
        tipo   = str(row["Tipo"]).strip().upper()

        try:
            fecha_ini = normalizar_fecha(row["Fecha_inicio"])
            fecha_fin = normalizar_fecha(row["Fecha_fin"])
        except ValueError as e:
            print(f"  [ERR] Fila {i+2}: {nombre} - {e}")
            errores += 1
            continue

        if tipo not in ("LPP", "LAR"):
            print(f"  [ERR] Fila {i+2}: tipo invalido '{tipo}' para {nombre}")
            errores += 1
            continue

        # Advertir si fecha_fin < fecha_inicio
        if fecha_fin < fecha_ini:
            print(f"  [!]  {nombre} ({tipo}): fecha_fin ({fecha_fin}) < fecha_inicio ({fecha_ini}) — revisar!")

        try:
            # Verificar si ya existe
            with database.get_connection() as conn:
                existe = conn.execute(
                    "SELECT 1 FROM licencias WHERE nombre=? AND tipo=? AND fecha_inicio=? AND fecha_fin=?",
                    (nombre, tipo, fecha_ini, fecha_fin)
                ).fetchone()

            if existe:
                print(f"  [-] {nombre:<22} {tipo}  {fecha_ini} -> {fecha_fin}  (ya existe, omitido)")
                omitidas += 1
            else:
                database.insertar_licencia(nombre, tipo, fecha_ini, fecha_fin)
                print(f"  [OK] {nombre:<22} {tipo}  {fecha_ini} -> {fecha_fin}")
                insertadas += 1
        except Exception as e:
            print(f"  [ERR] {nombre} ({tipo}): {e}")
            errores += 1

    print("\n" + "=" * 60)
    print(f"  {insertadas} insertadas | {omitidas} ya existian | {errores} errores")
    print("=" * 60)

    print("\nEstado actual de la tabla licencias:")
    database.listar_licencias()


if __name__ == "__main__":
    importar()

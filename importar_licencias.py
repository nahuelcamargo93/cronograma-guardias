# -*- coding: utf-8 -*-
"""
importar_licencias.py — Script de importación única de LPP y LAR a la BD.

Lee los datos hardcodeados de data.py y los inserta en la tabla `licencias`.
Es seguro de correr varias veces: duplicados se omiten automáticamente.

Columnas de la tabla: Persona | Tipo | Fecha_inicio | Fecha_fin
"""

import db as database
from data import PERSONAL

# ---------------------------------------------------------------------------
# Datos adicionales que NO estaban en data.py (podés agregar acá antes de correr)
# Formato: (nombre, tipo, fecha_inicio, fecha_fin)
# Ejemplo: ("Lic. Perez", "LAR", "2026-03-01", "2026-03-14")
LICENCIAS_EXTRA = [
    # ("Lic. Ejemplo", "LAR", "2026-03-01", "2026-03-14"),
]
# ---------------------------------------------------------------------------


def importar():
    database.inicializar_db()

    nombres_validos = {p["Nombre"] for p in PERSONAL}
    insertadas = 0
    errores = 0

    print("=" * 60)
    print("  IMPORTACION DE LICENCIAS (LPP / LAR) -> BD")
    print("=" * 60)

    def procesar(licencias_dict, tipo):
        nonlocal insertadas, errores
        for nombre, rangos in licencias_dict.items():
            if nombre not in nombres_validos:
                print(f"  [!] Persona no encontrada en PERSONAL: '{nombre}' -> se omite")
                errores += 1
                continue
            for rango in rangos:
                # Saltar entradas vacías como ("",) o ()
                if not rango or len(rango) < 2 or not rango[0]:
                    print(f"  [-] {nombre} ({tipo}): rango vacio, se omite")
                    continue
                ini, fin = rango[0], rango[1]
                try:
                    database.insertar_licencia(nombre, tipo, ini, fin)
                    print(f"  [OK] {nombre:<22} {tipo}  {ini} -> {fin}")
                    insertadas += 1
                except Exception as e:
                    print(f"  [ERR] {nombre} ({tipo}) {ini}->{fin}: {e}")
                    errores += 1

    print("\n--- LPP ---")
    procesar(LPP, "LPP")

    print("\n--- LAR ---")
    procesar(LAR, "LAR")

    if LICENCIAS_EXTRA:
        print("\n--- EXTRAS ---")
        for nombre, tipo, ini, fin in LICENCIAS_EXTRA:
            if nombre not in nombres_validos:
                print(f"  [!] '{nombre}' no encontrado en PERSONAL -> se omite")
                errores += 1
                continue
            try:
                database.insertar_licencia(nombre, tipo, ini, fin)
                print(f"  [OK] {nombre:<22} {tipo}  {ini} -> {fin}")
                insertadas += 1
            except Exception as e:
                print(f"  [ERR] {nombre} ({tipo}) {ini}->{fin}: {e}")
                errores += 1

    print("\n" + "=" * 60)
    print(f"  Resultado: {insertadas} licencias insertadas, {errores} errores/omisiones")
    print("=" * 60)

    print("\nEstado actual de la tabla licencias:")
    database.listar_licencias()


if __name__ == "__main__":
    importar()

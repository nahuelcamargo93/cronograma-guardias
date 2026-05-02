"""
importar_excel.py — Script ONE-SHOT para importar cronogramas históricos a la BD.

Corre UNA SOLA VEZ para poblar guardias_historial.db con datos del pasado.
NO se ejecuta junto con main.py.

Uso:
    python importar_excel.py

El Excel debe tener:
  - Fila 1: "Turno" en col A, luego fechas como encabezados en el resto
  - Col A:  nombre del turno (puede repetirse para múltiples vacantes)
  - Celdas: nombre del kinesiólogo asignado, o vacío
"""

import openpyxl
import pandas as pd
from datetime import date, timedelta
from db import inicializar_db, get_connection, sincronizar_personal, _calcular_bloques_largos
from data import PERSONAL

# ─── CONFIGURACIÓN ────────────────────────────────────────────────────────────

EXCEL_PATH = "cronograma_para_importar.xlsx"
HOJA       = "Hoja1"

# Fechas del período que cubre el Excel (inclusive)
FECHA_INICIO_HIST = "2026-01-05"
FECHA_FIN_HIST    = "2026-05-24"

# Feriados dentro del período histórico (rangos inclusive)
# Cada tupla es (inicio, fin) en formato "YYYY-MM-DD"
FERIADOS_HIST_RANGOS = [
    ("2026-02-14", "2026-02-17"),
    ("2026-03-21", "2026-03-24"),
    ("2026-04-02", "2026-04-05"),
    ("2026-05-01", "2026-05-03"),
    ("2026-05-23", "2026-05-24"),  # el 25/5 ya es del próximo cronograma
]

NOTAS = "Importado desde cronograma_para_importar.xlsx (historial 2026)"

# ─── LÓGICA ────────────────────────────────────────────────────────────────────

def expandir_feriados(rangos):
    """Convierte lista de rangos en set de fechas individuales."""
    feriados = set()
    for ini_str, fin_str in rangos:
        ini = date.fromisoformat(ini_str)
        fin = date.fromisoformat(fin_str)
        d = ini
        while d <= fin:
            feriados.add(d.isoformat())
            d += timedelta(days=1)
    return feriados


def leer_guardias_excel(path, hoja):
    """
    Lee el Excel y devuelve lista de dicts:
    [{"nombre": ..., "fecha": "YYYY-MM-DD", "turno": ...}, ...]
    """
    wb = openpyxl.load_workbook(path)
    ws = wb[hoja]

    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        raise ValueError("El Excel está vacío.")

    header = rows[0]  # Fila 1: ["Turno", fecha1, fecha2, ...]
    fechas = []
    for val in header[1:]:
        if val is None:
            fechas.append(None)
        elif hasattr(val, 'date'):
            fechas.append(val.date().isoformat())
        else:
            try:
                fechas.append(pd.to_datetime(str(val)).strftime("%Y-%m-%d"))
            except Exception:
                fechas.append(None)

    guardias = []
    for row in rows[1:]:
        turno_raw = row[0]
        if not turno_raw:
            continue
        turno = str(turno_raw).strip().replace(" ", "_")
        # Normalizar acentos comunes
        turno = turno.replace("Ma\u00f1ana", "Mañana")

        for col_idx, fecha in enumerate(fechas):
            if fecha is None:
                continue
            nombre = row[col_idx + 1]
            if nombre and str(nombre).strip():
                guardias.append({
                    "nombre": str(nombre).strip(),
                    "fecha":  fecha,
                    "turno":  turno,
                })

    return guardias


def calcular_horas(turno):
    if turno.startswith("Noche") or turno.startswith("Dia"):
        return 12
    return 6


def main():
    print("=" * 60)
    print("  IMPORTADOR DE HISTORIAL -- guardias_historial.db")
    print("=" * 60)

    # Inicializar BD
    inicializar_db()

    import pandas as pd
    df_personal = pd.DataFrame(PERSONAL)
    sincronizar_personal(df_personal)
    print(f"[OK] Personal sincronizado ({len(df_personal)} personas)")

    # Leer Excel
    print(f"\nLeyendo: {EXCEL_PATH} / hoja '{HOJA}'...")
    guardias = leer_guardias_excel(EXCEL_PATH, HOJA)
    print(f"[OK] {len(guardias)} asignaciones encontradas en el Excel")

    # Calcular bloques de finde largo del período histórico
    fecha_ini_dt = date.fromisoformat(FECHA_INICIO_HIST)
    fecha_fin_dt = date.fromisoformat(FECHA_FIN_HIST)
    dias_totales = (fecha_fin_dt - fecha_ini_dt).days + 1
    offset_dia   = fecha_ini_dt.weekday()  # 0=Lun

    # Feriados como indices
    feriados_set = expandir_feriados(FERIADOS_HIST_RANGOS)
    feriados_indices = set()
    for d in range(dias_totales):
        f = (fecha_ini_dt + timedelta(days=d)).isoformat()
        if f in feriados_set:
            feriados_indices.add(d)

    bloques = _calcular_bloques_largos(fecha_ini_dt, dias_totales, feriados_indices, offset_dia)

    print(f"\nPeriodo: {FECHA_INICIO_HIST} -> {FECHA_FIN_HIST} ({dias_totales} dias, {dias_totales//7} semanas)")
    print(f"Feriados individuales: {len(feriados_indices)} dias")
    print(f"Bloques finde largo detectados: {len(bloques)}")
    for b in bloques:
        fi = (fecha_ini_dt + timedelta(days=b[0])).isoformat()
        ff = (fecha_ini_dt + timedelta(days=b[-1])).isoformat()
        print(f"  > {fi} -> {ff} ({len(b)} dias)")

    # Set de índices que son finde
    finde_indices = set(
        d for d in range(dias_totales)
        if ((d + offset_dia) % 7) >= 5 or d in feriados_indices
    )

    # Confirmar antes de insertar
    print(f"\nConfirmar importacion? Se creara 1 cronograma historico con {len(guardias)} guardias. (s/n): ", end="")
    resp = input().strip().lower()
    if resp != "s":
        print("Importacion cancelada.")
        return

    with get_connection() as conn:
        # Cabecera
        cur = conn.execute("""
            INSERT INTO cronogramas (fecha_inicio, fecha_fin, creado_en, notas)
            VALUES (?, ?, datetime('now'), ?)
        """, (FECHA_INICIO_HIST, FECHA_FIN_HIST, NOTAS))
        cronograma_id = cur.lastrowid

        # Bloques de finde largo
        for bloque in bloques:
            fi = (fecha_ini_dt + timedelta(days=bloque[0])).isoformat()
            ff = (fecha_ini_dt + timedelta(days=bloque[-1])).isoformat()
            tipo = min(len(bloque), 4)
            conn.execute("""
                INSERT INTO bloques_finde_largo (cronograma_id, fecha_inicio, fecha_fin, tipo)
                VALUES (?, ?, ?, ?)
            """, (cronograma_id, fi, ff, tipo))

        # Guardias
        ok = 0
        skip = 0
        nombres_validos = set(df_personal['Nombre'].tolist())
        for g in guardias:
            if g['nombre'] not in nombres_validos:
                print(f"  [SKIP] Nombre no reconocido: '{g['nombre']}'")
                skip += 1
                continue
            fecha_dt = date.fromisoformat(g['fecha'])
            d = (fecha_dt - fecha_ini_dt).days
            es_finde = 1 if d in finde_indices else 0
            horas = calcular_horas(g['turno'])
            conn.execute("""
                INSERT INTO guardias (cronograma_id, nombre, fecha, turno, horas, es_finde)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (cronograma_id, g['nombre'], g['fecha'], g['turno'], horas, es_finde))
            ok += 1

    print(f"\n[OK] Importacion completada (id={cronograma_id})")
    print(f"   Guardias insertadas: {ok}")
    if skip:
        print(f"   Guardias omitidas (nombre no reconocido): {skip}")

    # Resumen de horas por persona
    print("\nResumen de horas importadas por kinesiologo:")
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT nombre, SUM(horas), COUNT(*) 
            FROM guardias WHERE cronograma_id = ?
            GROUP BY nombre ORDER BY nombre
        """, (cronograma_id,)).fetchall()
    for nombre, horas_tot, cnt in rows:
        print(f"  {nombre:<22} {horas_tot:>4}hs  ({cnt} turnos)")


if __name__ == "__main__":
    main()

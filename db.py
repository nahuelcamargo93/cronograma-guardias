"""
db.py — Módulo de base de datos SQLite para el historial de guardias.
Archivo de BD: guardias_historial.db (en la misma carpeta que el proyecto)

Tablas:
  personal             — tabla dimensional con nombre y rol
  cronogramas          — cabecera de cada período generado
  guardias             — cada guardia asignada (hecho crudo)
  bloques_finde_largo  — bloques de 3+ días no-laborables por período
  licencias            — LPP y LAR por persona con fecha_inicio y fecha_fin
"""

import sqlite3
import os
from datetime import datetime, date, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "guardias_historial.db")

# Licencias cargadas en memoria una vez al inicio (via init_licencias())
LAR: dict = {}
LPP: dict = {}


def init_licencias():
    """Carga LAR y LPP desde la BD en los dicts de módulo. Llamar una vez al inicio."""
    global LAR, LPP
    raw = cargar_licencias_db()
    LAR = {}
    LPP = {}
    for nombre, rangos in raw.items():
        for (tipo, fi, ff) in rangos:
            if tipo == 'LAR':
                LAR.setdefault(nombre, []).append((fi, ff))
            elif tipo == 'LPP':
                LPP.setdefault(nombre, []).append((fi, ff))


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def inicializar_db():
    """Crea las tablas si no existen. Seguro de llamar múltiples veces."""
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS personal (
                nombre TEXT PRIMARY KEY,
                rol    TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS cronogramas (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha_inicio TEXT NOT NULL,
                fecha_fin    TEXT NOT NULL,
                creado_en    TEXT,
                notas        TEXT
            );

            CREATE TABLE IF NOT EXISTS guardias (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                cronograma_id INTEGER NOT NULL REFERENCES cronogramas(id) ON DELETE CASCADE,
                nombre        TEXT NOT NULL REFERENCES personal(nombre),
                fecha         TEXT NOT NULL,
                turno         TEXT NOT NULL,
                horas         INTEGER NOT NULL,
                es_finde      INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS bloques_finde_largo (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                cronograma_id INTEGER NOT NULL REFERENCES cronogramas(id) ON DELETE CASCADE,
                fecha_inicio  TEXT NOT NULL,
                fecha_fin     TEXT NOT NULL,
                tipo          INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS licencias (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre       TEXT NOT NULL REFERENCES personal(nombre),
                tipo         TEXT NOT NULL CHECK(tipo IN ('LPP', 'LAR')),
                fecha_inicio TEXT NOT NULL,
                fecha_fin    TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_guardias_nombre  ON guardias(nombre);
            CREATE INDEX IF NOT EXISTS idx_guardias_fecha   ON guardias(fecha);
            CREATE INDEX IF NOT EXISTS idx_bloques_inicio   ON bloques_finde_largo(fecha_inicio);
            CREATE INDEX IF NOT EXISTS idx_licencias_nombre ON licencias(nombre);
            CREATE INDEX IF NOT EXISTS idx_licencias_inicio ON licencias(fecha_inicio);
        """)


def sincronizar_personal(df_personal):
    """Inserta o actualiza el personal en la tabla dimensional."""
    with get_connection() as conn:
        for _, persona in df_personal.iterrows():
            conn.execute("""
                INSERT INTO personal (nombre, rol) VALUES (?, ?)
                ON CONFLICT(nombre) DO UPDATE SET rol = excluded.rol
            """, (persona['Nombre'], persona['Rol']))


def _calcular_bloques_largos(fecha_inicio_dt, dias_totales, feriados_indices, offset_dia):
    """Devuelve lista de bloques (lista de índices de día) de 3+ días no-laborables."""
    es_descanso = [
        (((d + offset_dia) % 7) >= 5 or d in feriados_indices)
        for d in range(dias_totales)
    ]
    bloques = []
    actual = []
    for d in range(dias_totales):
        if es_descanso[d]:
            actual.append(d)
        else:
            if len(actual) >= 3:
                bloques.append(actual[:])
            actual = []
    if len(actual) >= 3:
        bloques.append(actual)
    return bloques


def cargar_historial(df_personal, fecha_corte_str):
    """
    Carga acumulados históricos ANTERIORES a fecha_corte_str.
    Retorna dict: {nombre: {campo: valor}} con los valores _Previos.
    Los campos Findes_Habiles_Previos se calculan como total de semanas
    históricas (aproximación conservadora, sin datos de licencias pasadas).
    """
    with get_connection() as conn:
        # Horas acumuladas
        horas_map = dict(conn.execute("""
            SELECT nombre, COALESCE(SUM(horas), 0)
            FROM guardias
            WHERE fecha < ?
            GROUP BY nombre
        """, (fecha_corte_str,)).fetchall())

        # Fines de semana trabajados (semanas ISO distintas con guardia en finde)
        fstrab_map = dict(conn.execute("""
            SELECT nombre, COUNT(DISTINCT strftime('%Y-%W', fecha))
            FROM guardias
            WHERE es_finde = 1 AND fecha < ?
            GROUP BY nombre
        """, (fecha_corte_str,)).fetchall())

        # Total de semanas en período histórico (para Findes_Habiles aproximado)
        total_semanas_hist = conn.execute("""
            SELECT COUNT(DISTINCT strftime('%Y-%W', fecha))
            FROM guardias
            WHERE es_finde = 1 AND fecha < ?
        """, (fecha_corte_str,)).fetchone()[0] or 0

        # Bloques de finde largo históricos
        bloques_rows = conn.execute("""
            SELECT id, fecha_inicio, fecha_fin, tipo
            FROM bloques_finde_largo
            WHERE fecha_inicio < ?
        """, (fecha_corte_str,)).fetchall()

    # Para cada bloque: ¿quién trabajó?
    fl3_trab = {n: 0 for n in df_personal['Nombre']}
    fl4_trab = {n: 0 for n in df_personal['Nombre']}

    with get_connection() as conn:
        for bloque_id, fi, ff, tipo in bloques_rows:
            trabajaron = {r[0] for r in conn.execute("""
                SELECT DISTINCT nombre FROM guardias
                WHERE fecha BETWEEN ? AND ? AND es_finde = 1
            """, (fi, ff)).fetchall()}

            for nombre in df_personal['Nombre']:
                if nombre in trabajaron:
                    if tipo == 3:
                        fl3_trab[nombre] += 1
                    else:
                        fl4_trab[nombre] += 1

    resultado = {}
    for nombre in df_personal['Nombre']:
        resultado[nombre] = {
            'Horas_Anuales_Previas':   horas_map.get(nombre, 0),
            'Findes_Semanas_Previos':  fstrab_map.get(nombre, 0),
            'Findes_Habiles_Previos':  total_semanas_hist,  # aprox: mismas semanas para todos
            'Findes_Largos_3_Previos': fl3_trab.get(nombre, 0),
            'Findes_Largos_4_Previos': fl4_trab.get(nombre, 0),
        }
    return resultado


def guardar_cronograma(df_resultados, df_personal, fecha_inicio, fecha_fin,
                       feriados_indices, offset_dia, dias_del_bloque, notas=""):
    """
    Persiste un cronograma aceptado en la BD.
    Guarda: cabecera en cronogramas, cada guardia en guardias,
    y los bloques de finde largo en bloques_finde_largo.
    """
    fecha_inicio_dt = date.fromisoformat(fecha_inicio)
    bloques = _calcular_bloques_largos(fecha_inicio_dt, dias_del_bloque, feriados_indices, offset_dia)

    # Set de índices que son finde
    finde_indices = set(
        d for d in range(dias_del_bloque)
        if ((d + offset_dia) % 7) >= 5 or d in feriados_indices
    )

    with get_connection() as conn:
        # 1. Cabecera
        cur = conn.execute("""
            INSERT INTO cronogramas (fecha_inicio, fecha_fin, creado_en, notas)
            VALUES (?, ?, ?, ?)
        """, (fecha_inicio, fecha_fin,
              datetime.now().isoformat(timespec='seconds'), notas))
        cronograma_id = cur.lastrowid

        # 2. Bloques de finde largo
        for bloque in bloques:
            fi = (fecha_inicio_dt + timedelta(days=bloque[0])).isoformat()
            ff = (fecha_inicio_dt + timedelta(days=bloque[-1])).isoformat()
            tipo = min(len(bloque), 4)
            conn.execute("""
                INSERT INTO bloques_finde_largo (cronograma_id, fecha_inicio, fecha_fin, tipo)
                VALUES (?, ?, ?, ?)
            """, (cronograma_id, fi, ff, tipo))

        # 3. Guardias individuales
        for _, row in df_resultados.iterrows():
            fecha = row['Fecha']
            turno = row['Turno']
            nombre = row['Kinesiologo']
            horas = 12 if (turno.startswith('Noche') or turno.startswith('Dia')) else 6
            d = (date.fromisoformat(fecha) - fecha_inicio_dt).days
            es_finde = 1 if d in finde_indices else 0

            conn.execute("""
                INSERT INTO guardias (cronograma_id, nombre, fecha, turno, horas, es_finde)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (cronograma_id, nombre, fecha, turno, horas, es_finde))

    print(f"✅ Cronograma guardado en BD (id={cronograma_id}): {fecha_inicio} → {fecha_fin}")
    return cronograma_id


def listar_cronogramas():
    """Muestra todos los cronogramas guardados en la BD."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT id, fecha_inicio, fecha_fin, creado_en, notas
            FROM cronogramas ORDER BY fecha_inicio
        """).fetchall()
    if not rows:
        print("No hay cronogramas guardados en la BD.")
        return
    print(f"\n{'ID':<5} {'Inicio':<12} {'Fin':<12} {'Creado':<20} Notas")
    print("-" * 70)
    for r in rows:
        print(f"{r[0]:<5} {r[1]:<12} {r[2]:<12} {r[3]:<20} {r[4] or ''}")


def insertar_licencia(nombre, tipo, fecha_inicio, fecha_fin):
    """
    Inserta una licencia individual. Si ya existe exactamente la misma
    (mismo nombre, tipo, inicio y fin) la omite silenciosamente.
    """
    tipo = tipo.upper()
    if tipo not in ('LPP', 'LAR'):
        raise ValueError(f"Tipo de licencia inválido: '{tipo}'. Debe ser 'LPP' o 'LAR'.")
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO licencias (nombre, tipo, fecha_inicio, fecha_fin)
            SELECT ?, ?, ?, ?
            WHERE NOT EXISTS (
                SELECT 1 FROM licencias
                WHERE nombre = ? AND tipo = ? AND fecha_inicio = ? AND fecha_fin = ?
            )
        """, (nombre, tipo, fecha_inicio, fecha_fin,
              nombre, tipo, fecha_inicio, fecha_fin))


def cargar_licencias_db(fecha_inicio_str=None, fecha_fin_str=None):
    """
    Devuelve todas las licencias que se superponen con el rango dado.
    Si no se pasan fechas, devuelve todas.
    Formato: dict {nombre: [(tipo, fecha_inicio, fecha_fin), ...]}
    """
    with get_connection() as conn:
        if fecha_inicio_str and fecha_fin_str:
            rows = conn.execute("""
                SELECT nombre, tipo, fecha_inicio, fecha_fin
                FROM licencias
                WHERE fecha_inicio <= ? AND fecha_fin >= ?
                ORDER BY nombre, fecha_inicio
            """, (fecha_fin_str, fecha_inicio_str)).fetchall()
        else:
            rows = conn.execute("""
                SELECT nombre, tipo, fecha_inicio, fecha_fin
                FROM licencias
                ORDER BY nombre, fecha_inicio
            """).fetchall()

    resultado = {}
    for nombre, tipo, fi, ff in rows:
        resultado.setdefault(nombre, []).append((tipo, fi, ff))
    return resultado


def listar_licencias():
    """Imprime todas las licencias cargadas en la BD."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT nombre, tipo, fecha_inicio, fecha_fin
            FROM licencias
            ORDER BY tipo, fecha_inicio, nombre
        """).fetchall()
    if not rows:
        print("No hay licencias cargadas en la BD.")
        return
    print(f"\n{'Nombre':<22} {'Tipo':<5} {'Inicio':<12} {'Fin'}")
    print("-" * 55)
    for r in rows:
        print(f"{r[0]:<22} {r[1]:<5} {r[2]:<12} {r[3]}")

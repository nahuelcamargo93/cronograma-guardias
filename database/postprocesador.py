"""
database/postprocesador.py — Postprocesador de resultados de OR-Tools.

Responsabilidad única: Traducir la matriz de variables binarias (que pueden usar
IDs numéricos o nombres strings) resuelta por el solver de OR-Tools, reconstruir
las asignaciones con sus nombres de negocio correspondientes, y persistir los
resultados en la base de datos de forma limpia.
"""

from datetime import datetime, date, timedelta
from .connection import get_connection
from .queries import _calcular_bloques_largos


def postprocesar_y_guardar(
    solver,
    turnos: dict,
    traductor,
    fecha_inicio: str,
    fecha_fin: str,
    feriados_indices: list[int],
    offset_dia: int,
    dias_del_bloque: int,
    notas: str = "",
    df_cat_semanas = None,
    flrs_asignados: list[dict] = None
) -> int:
    """Traduce los resultados del solver y los guarda en la base de datos.

    Soporta claves híbridas de turnos:
      - Enteros (nuevas): (emp_idx, dia, turno_idx)
      - Strings (legacy): (nombre, dia, turno)

    Retorna:
        int: El ID del cronograma insertado (cronograma_id).
    """
    fecha_inicio_dt = date.fromisoformat(fecha_inicio)
    bloques = _calcular_bloques_largos(fecha_inicio_dt, dias_del_bloque, feriados_indices, offset_dia)

    # Set de índices de días que son fines de semana o feriados
    finde_indices = set(
        d for d in range(dias_del_bloque)
        if ((d + offset_dia) % 7) >= 5 or d in feriados_indices
    )

    with get_connection() as conn:
        # 1. Crear cabecera de cronograma
        cur = conn.execute("""
            INSERT INTO cronogramas (fecha_inicio, fecha_fin, creado_en, notas, estado)
            VALUES (?, ?, ?, ?, 'borrador')
        """, (fecha_inicio, fecha_fin,
              datetime.now().isoformat(timespec='seconds'), notas))
        cronograma_id = cur.lastrowid

        # 2. Guardar bloques de fin de semana largo
        for bloque in bloques:
            fi = (fecha_inicio_dt + timedelta(days=bloque[0])).isoformat()
            ff = (fecha_inicio_dt + timedelta(days=bloque[-1])).isoformat()
            tipo = min(len(bloque), 4)
            conn.execute("""
                INSERT INTO bloques_finde_largo (cronograma_id, fecha_inicio, fecha_fin, tipo)
                VALUES (?, ?, ?, ?)
            """, (cronograma_id, fi, ff, tipo))

        # 3. Guardar guardias individuales
        cur_t = conn.execute("SELECT nombre, horas FROM turnos_config WHERE servicio_id = ?", (traductor.servicio_id,))
        mapa_horas = {r[0]: r[1] for r in cur_t.fetchall()}

        for (emp_key, dia, turno_key), var in turnos.items():
            if solver.Value(var) == 1:
                # Traducir empleado
                if isinstance(emp_key, int):
                    nombre = traductor.id_emp[emp_key]
                else:
                    nombre = emp_key

                # Traducir turno
                if isinstance(turno_key, int):
                    turno = traductor.id_turno[turno_key]
                    horas = traductor.horas_turno(turno_key)
                else:
                    turno = turno_key
                    if turno in traductor.turno_id:
                        horas = traductor.horas_turno(traductor.turno_id[turno])
                    else:
                        horas = mapa_horas.get(turno, 6)

                fecha_actual = (fecha_inicio_dt + timedelta(days=dia)).strftime("%Y-%m-%d")
                es_finde = 1 if dia in finde_indices else 0

                conn.execute("""
                    INSERT INTO guardias (cronograma_id, nombre, fecha, turno, horas, es_finde, servicio_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (cronograma_id, nombre, fecha_actual, turno, horas, es_finde, traductor.servicio_id))

        # 4. Guardar categorías semanales del solver
        if df_cat_semanas is not None and not df_cat_semanas.empty:
            for _, row in df_cat_semanas.iterrows():
                nombre = row['Nombre']
                if isinstance(nombre, int):
                    nombre = traductor.id_emp[nombre]
                conn.execute("""
                    INSERT INTO semanas_categorias (cronograma_id, nombre, fecha_lunes, categoria)
                    VALUES (?, ?, ?, ?)
                """, (cronograma_id, nombre, row['Fecha_Lunes'], row['Categoria']))

        # 5. Guardar FLR asignados
        if flrs_asignados:
            for f in flrs_asignados:
                nombre = f['nombre']
                if isinstance(nombre, int):
                    nombre = traductor.id_emp[nombre]
                conn.execute("""
                    INSERT INTO flr_asignados (cronograma_id, nombre, fecha_inicio, fecha_fin)
                    VALUES (?, ?, ?, ?)
                """, (cronograma_id, nombre, f['fecha_inicio'], f['fecha_fin']))

    print(f"[OK] [Postprocesador] Cronograma guardado en BD (id={cronograma_id}): {fecha_inicio} -> {fecha_fin}")
    return cronograma_id

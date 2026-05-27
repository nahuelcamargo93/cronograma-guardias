from .connection import get_connection
import sqlite3
import json
from datetime import datetime, date, timedelta
from models import Empleado, Turno

LAR = {}
LPP = {}
LM  = {}
CM  = {}

def init_licencias():
    """Carga LAR, LPP, LM y CM desde la BD en los dicts de módulo. Llamar una vez al inicio."""
    global LAR, LPP, LM, CM
    raw = cargar_licencias_db()
    LAR.clear()
    LPP.clear()
    LM.clear()
    CM.clear()
    for nombre, rangos in raw.items():
        for (tipo, fi, ff) in rangos:
            tipo_up = tipo.upper()
            if tipo_up == 'LAR':
                LAR.setdefault(nombre, []).append((fi, ff))
            elif tipo_up == 'LPP':
                LPP.setdefault(nombre, []).append((fi, ff))
            elif tipo_up == 'LM':
                LM.setdefault(nombre, []).append((fi, ff))
            elif tipo_up == 'CM':
                CM.setdefault(nombre, []).append((fi, ff))
                
    # (Se eliminó la carga automática de FLRs aquí para evitar bloqueos en re-ejecuciones)
    pass


def cargar_datos_personales_bd(df_personal):
    """Agrega las columnas de la BD (cumpleaños, es_madre, es_padre, régimen, horas reglamentarias) al DataFrame de personal en memoria."""
    with get_connection() as conn:
        rows = conn.execute("SELECT nombre, fecha_cumpleanos, es_madre, es_padre, regimen_trabajo, horas_mensuales_reglamentarias FROM personal").fetchall()
        
    info = {r[0]: {
        'fecha_cumpleanos': r[1], 
        'es_madre': r[2], 
        'es_padre': r[3],
        'regimen_trabajo': r[4],
        'horas_mensuales_reglamentarias': r[5]
    } for r in rows}
    
    df_personal['fecha_cumpleanos'] = df_personal['Nombre'].map(lambda n: info.get(n, {}).get('fecha_cumpleanos'))
    df_personal['es_madre'] = df_personal['Nombre'].map(lambda n: info.get(n, {}).get('es_madre', 0))
    df_personal['es_padre'] = df_personal['Nombre'].map(lambda n: info.get(n, {}).get('es_padre', 0))
    df_personal['regimen_trabajo'] = df_personal['Nombre'].map(lambda n: info.get(n, {}).get('regimen_trabajo'))
    df_personal['horas_mensuales_reglamentarias'] = df_personal['Nombre'].map(lambda n: info.get(n, {}).get('horas_mensuales_reglamentarias'))
    return df_personal

def obtener_personal_db(servicio_id):
    """Retorna la lista de personal para un servicio específico."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT nombre, categoria, rol FROM personal WHERE servicio_id = ? AND COALESCE(activo, 1) = 1 ORDER BY nombre", 
            (servicio_id,)
        ).fetchall()
        
        # Obtener puestos habilitados (todos) y cuáles son primarios
        puestos_rows = conn.execute("""
            SELECT pp.personal_nombre, p.nombre, COALESCE(pp.es_primario, 1) as es_primario
            FROM personal_puestos pp
            JOIN puestos p ON pp.puesto_id = p.id
            WHERE p.servicio_id = ?
        """, (servicio_id,)).fetchall()
        
        puestos_map = {}
        puestos_primarios_map = {}
        for p_nombre, p_puesto, es_prim in puestos_rows:
            puestos_map.setdefault(p_nombre, set()).add(p_puesto)
            if es_prim:
                puestos_primarios_map.setdefault(p_nombre, set()).add(p_puesto)
            
    return [{'Nombre': r[0], 'Categoria': r[1], 'Rol': r[2],
             'Puestos_Habilitados': list(puestos_map.get(r[0], [])),
             'Puestos_Primarios': list(puestos_primarios_map.get(r[0], []))} for r in rows]

def sincronizar_personal(df_personal):
    """Inserta o actualiza el personal en la tabla dimensional."""
    with get_connection() as conn:
        for _, persona in df_personal.iterrows():
            categoria = persona.get('Categoria') if 'Categoria' in persona else None
            conn.execute("""
                INSERT INTO personal (nombre, categoria, rol) VALUES (?, ?, ?)
                ON CONFLICT(nombre) DO UPDATE SET categoria = excluded.categoria, rol = excluded.rol
            """, (persona['Nombre'], categoria, persona['Rol']))


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
    Solo considera cronogramas con estado='aprobado'.
    Retorna dict: {nombre: {campo: valor}} con los valores _Previos.
    """
    with get_connection() as conn:
        # Horas acumuladas (solo de cronogramas aprobados)
        horas_map = dict(conn.execute("""
            SELECT g.nombre, COALESCE(SUM(g.horas), 0)
            FROM guardias g
            JOIN cronogramas c ON g.cronograma_id = c.id
            WHERE g.fecha < ? AND c.estado = 'aprobado'
            GROUP BY g.nombre
        """, (fecha_corte_str,)).fetchall())

        # Feriados trabajados históricos (solo de cronogramas aprobados)
        from data import FERIADOS as data_feriados
        placeholders = ",".join("?" for _ in data_feriados)
        feriados_trab_map = {}
        if data_feriados:
            feriados_trab_map = dict(conn.execute(f"""
                SELECT g.nombre, COUNT(DISTINCT g.fecha)
                FROM guardias g
                JOIN cronogramas c ON g.cronograma_id = c.id
                WHERE g.fecha < ? AND c.estado = 'aprobado' AND g.fecha IN ({placeholders})
                GROUP BY g.nombre
            """, [fecha_corte_str] + data_feriados).fetchall())

        # Fines de semana trabajados (solo de cronogramas aprobados)
        fstrab_map = dict(conn.execute("""
            SELECT g.nombre, COUNT(DISTINCT strftime('%Y-%W', g.fecha))
            FROM guardias g
            JOIN cronogramas c ON g.cronograma_id = c.id
            WHERE g.es_finde = 1 AND g.fecha < ? AND c.estado = 'aprobado'
            GROUP BY g.nombre
        """, (fecha_corte_str,)).fetchall())

        # Fecha de inicio de historial por persona (solo de cronogramas aprobados)
        fecha_ini_map = dict(conn.execute("""
            SELECT g.nombre, MIN(g.fecha)
            FROM guardias g
            JOIN cronogramas c ON g.cronograma_id = c.id
            WHERE g.fecha < ? AND c.estado = 'aprobado'
            GROUP BY g.nombre
        """, (fecha_corte_str,)).fetchall())

        # Total de semanas en período histórico (solo de cronogramas aprobados)
        total_semanas_hist = conn.execute("""
            SELECT COUNT(DISTINCT strftime('%Y-%W', g.fecha))
            FROM guardias g
            JOIN cronogramas c ON g.cronograma_id = c.id
            WHERE g.es_finde = 1 AND g.fecha < ? AND c.estado = 'aprobado'
        """, (fecha_corte_str,)).fetchone()[0] or 0

        # Bloques de finde largo históricos (solo de cronogramas aprobados)
        bloques_rows = conn.execute("""
            SELECT bfl.id, bfl.fecha_inicio, bfl.fecha_fin, bfl.tipo
            FROM bloques_finde_largo bfl
            JOIN cronogramas c ON bfl.cronograma_id = c.id
            WHERE bfl.fecha_inicio < ? AND c.estado = 'aprobado'
        """, (fecha_corte_str,)).fetchall()

    # Para cada bloque: ¿quién trabajó? (solo guardias de cronogramas aprobados)
    fl3_trab = {n: 0 for n in df_personal['Nombre']}
    fl4_trab = {n: 0 for n in df_personal['Nombre']}

    with get_connection() as conn:
        for bloque_id, fi, ff, tipo in bloques_rows:
            trabajaron = {r[0] for r in conn.execute("""
                SELECT DISTINCT g.nombre FROM guardias g
                JOIN cronogramas c ON g.cronograma_id = c.id
                WHERE g.fecha BETWEEN ? AND ? AND g.es_finde = 1
                  AND c.estado = 'aprobado'
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
            'Findes_Habiles_Previos':  total_semanas_hist,
            'Findes_Largos_3_Previos': fl3_trab.get(nombre, 0),
            'Findes_Largos_4_Previos': fl4_trab.get(nombre, 0),
            'Fecha_Inicio_Historial':  fecha_ini_map.get(nombre),
            'Feriados_Previos':        feriados_trab_map.get(nombre, 0),
        }
    return resultado


def cargar_guardias_previas(fecha_inicio_str, dias_atras=28, servicio_id=None):
    """
    Retorna las guardias asignadas del ULTIMO cronograma aprobado para este servicio.
    Devuelve dict: { nombre: [ { 'fecha': 'YYYY-MM-DD', 'turno': 'Noche', 'horas': 12 }, ... ] }
    Ignora dias_atras para buscar directamente el ultimo bloque entero.
    """
    with get_connection() as conn:
        # 1. Buscar el ID del ultimo cronograma aprobado
        if servicio_id is not None:
            ultimo_cr_query = """
                SELECT DISTINCT c.id FROM cronogramas c
                JOIN guardias g ON c.id = g.cronograma_id
                JOIN personal p ON g.nombre = p.nombre
                WHERE c.estado = 'aprobado' AND c.fecha_inicio < ? AND p.servicio_id = ?
                ORDER BY c.fecha_inicio DESC
                LIMIT 1
            """
            row_cr = conn.execute(ultimo_cr_query, [fecha_inicio_str, servicio_id]).fetchone()
        else:
            ultimo_cr_query = """
                SELECT id FROM cronogramas
                WHERE estado = 'aprobado' AND fecha_inicio < ?
                ORDER BY fecha_inicio DESC
                LIMIT 1
            """
            row_cr = conn.execute(ultimo_cr_query, [fecha_inicio_str]).fetchone()
        
        if not row_cr:
            return {} # No hay cronogramas previos aprobados
        
        cronograma_id = row_cr[0]

        # 2. Traer todas las guardias de ese cronograma
        query = """
            SELECT g.nombre, g.fecha, g.turno, g.horas 
            FROM guardias g
            JOIN personal p ON g.nombre = p.nombre
            WHERE g.cronograma_id = ?
        """
        params = [cronograma_id]
        
        if servicio_id is not None:
            query += " AND p.servicio_id = ?"
            params.append(servicio_id)
            
        rows = conn.execute(query, params).fetchall()
        
    historial = {}
    for nombre, fecha, turno, horas in rows:
        historial.setdefault(nombre, []).append({
            'fecha': fecha,
            'turno': turno,
            'horas': horas
        })
    return historial


def guardar_cronograma(df_resultados, df_personal, fecha_inicio, fecha_fin,
                       feriados_indices, offset_dia, dias_del_bloque, notas="", df_cat_semanas=None):
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
        cur = conn.execute("""
            INSERT INTO cronogramas (fecha_inicio, fecha_fin, creado_en, notas, estado)
            VALUES (?, ?, ?, ?, 'borrador')
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
        cur_t = conn.execute("SELECT nombre, horas FROM turnos_config")
        mapa_horas = {r[0]: r[1] for r in cur_t.fetchall()}

        for _, row in df_resultados.iterrows():
            fecha = row['Fecha']
            turno = row['Turno']
            nombre = row['Personal']
            horas = mapa_horas.get(turno, 6)
            d = (date.fromisoformat(fecha) - fecha_inicio_dt).days
            es_finde = 1 if d in finde_indices else 0

            conn.execute("""
                INSERT INTO guardias (cronograma_id, nombre, fecha, turno, horas, es_finde)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (cronograma_id, nombre, fecha, turno, horas, es_finde))

        # 4. Categorías semanales del solver
        if df_cat_semanas is not None and not df_cat_semanas.empty:
            for _, row in df_cat_semanas.iterrows():
                conn.execute("""
                    INSERT INTO semanas_categorias (cronograma_id, nombre, fecha_lunes, categoria)
                    VALUES (?, ?, ?, ?)
                """, (cronograma_id, row['Nombre'], row['Fecha_Lunes'], row['Categoria']))

    print(f"[OK] Cronograma guardado en BD (id={cronograma_id}): {fecha_inicio} -> {fecha_fin}")
    return cronograma_id

def guardar_flrs_asignados(cronograma_id, flrs_asignados):
    if not flrs_asignados: return
    with get_connection() as conn:
        for f in flrs_asignados:
            conn.execute("""
                INSERT INTO flr_asignados (cronograma_id, nombre, fecha_inicio, fecha_fin)
                VALUES (?, ?, ?, ?)
            """, (cronograma_id, f['nombre'], f['fecha_inicio'], f['fecha_fin']))
    print(f"[OK] {len(flrs_asignados)} FLRs asignados guardados en BD.")



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
    if tipo not in ('LPP', 'LAR', 'CM', 'LM'):
        raise ValueError(f"Tipo de licencia inválido: '{tipo}'. Debe ser 'LPP', 'LAR', 'CM' o 'LM'.")
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



def cargar_reglas_servicio(servicio_id=1):
    """
    Devuelve las reglas combinadas para un servicio.
    Prioriza las reglas de servicio sobre las de la organización.
    """
    with get_connection() as conn:
        # Obtener organizacion_id del servicio
        org_id = conn.execute("SELECT organizacion_id FROM servicios WHERE id = ?", (servicio_id,)).fetchone()[0]
        
        # Reglas de organización
        rows_org = conn.execute("""
            SELECT codigo_regla, parametros_json
            FROM organizaciones_reglas
            WHERE organizacion_id = ? AND activo = 1
        """, (org_id,)).fetchall()
        
        # Reglas de servicio
        rows_serv = conn.execute("""
            SELECT codigo_regla, parametros_json
            FROM servicios_reglas
            WHERE servicio_id = ? AND activo = 1
        """, (servicio_id,)).fetchall()
    
    reglas = {}
    # Cargar org (base)
    for codigo, params in rows_org:
        try: reglas[codigo] = json.loads(params) if params else {}
        except: reglas[codigo] = {}
        
    # Sobrescribir con servicio (específico)
    for codigo, params in rows_serv:
        try: reglas[codigo] = json.loads(params) if params else {}
        except: reglas[codigo] = {}
        
    return reglas

def cargar_reglas_personal(servicio_id=1):
    """Devuelve un diccionario con las reglas individuales por persona de un servicio.
       { 'Nombre': { 'CODIGO_REGLA': [{parametros_json}, ...] } }
    """
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT pr.personal_nombre, pr.codigo_regla, pr.parametros_json
            FROM personal_reglas pr
            JOIN personal p ON pr.personal_nombre = p.nombre
            WHERE p.servicio_id = ? AND pr.activo = 1 AND COALESCE(p.activo, 1) = 1
        """, (servicio_id,)).fetchall()
    
    reglas = {}
    for nombre, codigo, params in rows:
        if nombre not in reglas:
            reglas[nombre] = {}
        if codigo not in reglas[nombre]:
            reglas[nombre][codigo] = []
            
        try:
            parsed = json.loads(params) if params else {}
            if isinstance(parsed, list):
                reglas[nombre][codigo].extend(parsed)
            else:
                reglas[nombre][codigo].append(parsed)
        except json.JSONDecodeError:
            pass
    return reglas

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

def migrar_demanda_a_db(demanda_turnos, ajustes_vacantes=None, servicio_id=1, fecha_inicio_cronograma=None):
    """
    Migra la configuración desde data.py a las nuevas tablas de la BD.
    fecha_inicio_cronograma es necesaria para convertir los índices de semana de AJUSTES_VACANTES en fechas.
    """
    with get_connection() as conn:
        # 1. Mapear todos los nombres de turnos únicos
        nombres_turnos = set(demanda_turnos.get("Semana", {}).keys()) | set(demanda_turnos.get("Finde_Feriado", {}).keys())
        
        # 2. Insertar en turnos_config
        for orden, nombre in enumerate(nombres_turnos):
            # Obtener horas y vacantes base
            info_sem = demanda_turnos.get("Semana", {}).get(nombre, {})
            info_fin = demanda_turnos.get("Finde_Feriado", {}).get(nombre, {})
            
            horas = info_sem.get("Horas") or info_fin.get("Horas", 6)
            v_sem = info_sem.get("Vacantes", 0)
            v_fin = info_fin.get("Vacantes", 0)
            
            # Estimación de hora_inicio basada en el nombre
            h_inicio = "08:00"
            if "Tarde" in nombre: h_inicio = "14:00"
            elif "Noche" in nombre: h_inicio = "20:00"
            elif "Dia" in nombre: h_inicio = "08:00"

            # Determinar días permitidos por defecto
            dias_permitidos = "0,1,2,3,4,5,6"
            if v_sem > 0 and v_fin == 0:
                dias_permitidos = "0,1,2,3,4"
            elif v_sem == 0 and v_fin > 0:
                dias_permitidos = "5,6"

            conn.execute("""
                INSERT INTO turnos_config (servicio_id, nombre, hora_inicio, horas, vacantes_semana, vacantes_finde, dias_semana, orden)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(servicio_id, nombre) DO UPDATE SET
                    horas = excluded.horas,
                    vacantes_semana = excluded.vacantes_semana,
                    vacantes_finde = excluded.vacantes_finde,
                    dias_semana = excluded.dias_semana
            """, (servicio_id, nombre, h_inicio, horas, v_sem, v_fin, dias_permitidos, orden))

        # 3. Migrar ajustes si hay fecha de referencia
        if ajustes_vacantes and fecha_inicio_cronograma:
            base_dt = date.fromisoformat(fecha_inicio_cronograma)
            for sem_idx, cambios in ajustes_vacantes.items():
                f_ini = (base_dt + timedelta(weeks=sem_idx)).isoformat()
                f_fin = (base_dt + timedelta(weeks=sem_idx, days=6)).isoformat()
                
                for nombre_turno, vacantes in cambios.items():
                    # Obtener ID del turno
                    row = conn.execute("SELECT id FROM turnos_config WHERE servicio_id = ? AND nombre = ?", 
                                     (servicio_id, nombre_turno)).fetchone()
                    if row:
                        t_id = row[0]
                        conn.execute("""
                            INSERT INTO turnos_ajustes (turno_config_id, fecha_inicio, fecha_fin, vacantes)
                            VALUES (?, ?, ?, ?)
                        """, (t_id, f_ini, f_fin, vacantes))

    print(f"Migracion de demanda completada para servicio {servicio_id}")

def cargar_configuracion_turnos(servicio_id=1, fecha_inicio=None, fecha_fin=None):
    """
    Carga la configuración WFM: Oferta (Turnos) y Demanda (Vacantes).
    Retorna: config_oferta, metadata_turnos, demanda_base, demanda_ajustes
    """
    with get_connection() as conn:
        # 1. Cargar Oferta (Turnos Config) con Nombre del Puesto
        rows_turnos = conn.execute("""
            SELECT tc.id, tc.nombre, tc.horas, tc.hora_inicio, tc.dias_semana, tc.puesto_id, p.nombre as puesto_nombre
            FROM turnos_config tc
            LEFT JOIN puestos p ON tc.puesto_id = p.id
            WHERE tc.servicio_id = ? AND tc.activo = 1
            ORDER BY tc.orden
        """, (servicio_id,)).fetchall()
        
        config = { "Semana": {}, "Finde_Feriado": {}, "Metadata": {} }
        turnos_info = {}
        for r_id, nombre, horas, h_ini, d_sem, p_id, p_nom in rows_turnos:
            # Poblamos la estructura antigua para que main.py pueda crear las variables sin chillar
            config["Semana"][nombre] = {"Horas": horas, "Dias_Habilitados": d_sem}
            config["Finde_Feriado"][nombre] = {"Horas": horas, "Dias_Habilitados": d_sem}
            config["Metadata"][nombre] = {"hora_inicio": h_ini, "puesto_id": p_id, "puesto_nombre": p_nom}
            
            turnos_info[nombre] = {
                "hora_inicio": h_ini, 
                "horas": horas, 
                "puesto_id": p_id, 
                "puesto_nombre": p_nom,
                "dias_semana": d_sem
            }

        # 2. Cargar Demanda Base
        rows_demanda = conn.execute("""
            SELECT dc.id, p.nombre as puesto, dc.tipo_dia, dc.hora_inicio, dc.hora_fin, dc.cantidad_min, dc.cantidad_max, dc.puesto_id, dc.dias_semana
            FROM demanda_config dc
            JOIN puestos p ON dc.puesto_id = p.id
            WHERE p.servicio_id = ? AND dc.activo = 1
        """, (servicio_id,)).fetchall()

        demanda_req = {"Semana": [], "Finde_Feriado": []}
        for d_id, puesto, t_dia, h_ini, h_fin, c_min, c_max, p_id, d_sem in rows_demanda:
            item = {
                "id": d_id,
                "puesto": puesto,
                "puesto_id": p_id,
                "hora_inicio": h_ini,
                "hora_fin": h_fin,
                "cantidad_min": c_min,
                "cantidad_max": c_max,
                "dias_semana": d_sem
            }
            demanda_req[t_dia].append(item)

        # 3. Cargar Ajustes de Demanda
        ajustes = {} # { (fecha_ini, fecha_fin): [lista de ajustes] }
        if fecha_inicio and fecha_fin:
            rows_ajustes = conn.execute("""
                SELECT da.fecha_inicio, da.fecha_fin, da.demanda_config_id, da.cantidad_min, da.cantidad_max, da.dias_semana
                FROM demanda_ajustes da
                JOIN demanda_config dc ON da.demanda_config_id = dc.id
                JOIN puestos p ON dc.puesto_id = p.id
                WHERE p.servicio_id = ? AND da.activo = 1 AND dc.activo = 1
                  AND ((da.fecha_inicio BETWEEN ? AND ?) OR (da.fecha_fin BETWEEN ? AND ?))
            """, (servicio_id, fecha_inicio, fecha_fin, fecha_inicio, fecha_fin)).fetchall()
            
            for fi, ff, d_c_id, c_min, c_max, d_over in rows_ajustes:
                ajustes.setdefault((fi, ff), []).append({
                    "demanda_config_id": d_c_id,
                    "cantidad_min": c_min,
                    "cantidad_max": c_max,
                    "dias_override": d_over
                })
        
        return config, turnos_info, demanda_req, ajustes


def cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin):
    """
    Carga los ajustes temporales de reglas personales que se solapan con el rango dado.
    Permite suspender o sobrescribir reglas individuales por persona para un periodo especifico.
    Retorna: {nombre: [{codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json}, ...]}
    """
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json
            FROM personal_reglas_ajustes
            WHERE fecha_inicio <= ? AND fecha_fin >= ? AND activo = 1
            ORDER BY personal_nombre, codigo_regla
        """, (fecha_fin, fecha_inicio)).fetchall()

    resultado = {}
    for nombre, codigo, fi, ff, accion, params in rows:
        resultado.setdefault(nombre, []).append({
            'codigo_regla': codigo,
            'fecha_inicio': fi,
            'fecha_fin':    ff,
            'accion':       accion,
            'params':       json.loads(params) if params else None
        })
    return resultado


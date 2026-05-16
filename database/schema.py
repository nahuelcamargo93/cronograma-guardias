from .connection import get_connection, DB_PATH
import sqlite3
from datetime import datetime, date, timedelta

def inicializar_db():
    """Crea las tablas si no existen. Seguro de llamar múltiples veces."""
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS organizaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS servicios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                organizacion_id INTEGER NOT NULL REFERENCES organizaciones(id),
                nombre TEXT NOT NULL,
                UNIQUE(organizacion_id, nombre)
            );

            CREATE TABLE IF NOT EXISTS personal (
                nombre TEXT PRIMARY KEY,
                rol    TEXT NOT NULL,
                servicio_id INTEGER REFERENCES servicios(id),
                fecha_cumpleanos TEXT,
                es_madre INTEGER DEFAULT 0,
                es_padre INTEGER DEFAULT 0,
                regimen_trabajo TEXT,
                horas_mensuales_reglamentarias INTEGER
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

            CREATE TABLE IF NOT EXISTS flr_asignados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cronograma_id INTEGER NOT NULL REFERENCES cronogramas(id) ON DELETE CASCADE,
                nombre TEXT NOT NULL REFERENCES personal(nombre),
                fecha_inicio TEXT NOT NULL,
                fecha_fin TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS licencias (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre       TEXT NOT NULL REFERENCES personal(nombre),
                tipo         TEXT NOT NULL CHECK(tipo IN ('LPP', 'LAR', 'LM')),
                fecha_inicio TEXT NOT NULL,
                fecha_fin    TEXT NOT NULL,
                metadata     TEXT
            );

            -- MOTOR DE REGLAS MULTI-TENANT --
            CREATE TABLE IF NOT EXISTS reglas_catalogo (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_regla TEXT NOT NULL UNIQUE,
                tipo TEXT NOT NULL CHECK(tipo IN ('HARD', 'SOFT')),
                descripcion TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS organizaciones_reglas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                organizacion_id INTEGER NOT NULL REFERENCES organizaciones(id),
                regla_id INTEGER NOT NULL REFERENCES reglas_catalogo(id),
                parametros_json TEXT,
                UNIQUE(organizacion_id, regla_id)
            );

            CREATE TABLE IF NOT EXISTS servicios_reglas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                servicio_id INTEGER NOT NULL REFERENCES servicios(id),
                regla_id INTEGER NOT NULL REFERENCES reglas_catalogo(id),
                parametros_json TEXT,
                UNIQUE(servicio_id, regla_id)
            );

            CREATE TABLE IF NOT EXISTS personal_reglas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                personal_nombre TEXT NOT NULL REFERENCES personal(nombre),
                regla_id INTEGER NOT NULL REFERENCES reglas_catalogo(id),
                parametros_json TEXT,
                UNIQUE(personal_nombre, regla_id)
            );

            CREATE TABLE IF NOT EXISTS puestos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                servicio_id INTEGER NOT NULL REFERENCES servicios(id),
                nombre TEXT NOT NULL,
                UNIQUE(servicio_id, nombre)
            );

            CREATE TABLE IF NOT EXISTS demanda_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                puesto_id INTEGER NOT NULL REFERENCES puestos(id),
                tipo_dia TEXT NOT NULL CHECK(tipo_dia IN ('Semana', 'Finde_Feriado')),
                hora_inicio TEXT NOT NULL,
                hora_fin TEXT NOT NULL,
                cantidad_min INTEGER,
                cantidad_max INTEGER,
                UNIQUE(puesto_id, tipo_dia, hora_inicio, hora_fin)
            );

            CREATE TABLE IF NOT EXISTS demanda_ajustes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                demanda_config_id INTEGER NOT NULL REFERENCES demanda_config(id) ON DELETE CASCADE,
                fecha_inicio TEXT NOT NULL,
                fecha_fin TEXT NOT NULL,
                cantidad_min INTEGER,
                cantidad_max INTEGER,
                dias_semana TEXT
            );

            CREATE TABLE IF NOT EXISTS turnos_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                servicio_id INTEGER NOT NULL REFERENCES servicios(id),
                nombre TEXT NOT NULL,
                hora_inicio TEXT,
                horas INTEGER NOT NULL,
                dias_semana TEXT DEFAULT '0,1,2,3,4,5,6',
                orden INTEGER DEFAULT 0,
                activo INTEGER DEFAULT 1,
                UNIQUE(servicio_id, nombre)
            );

            CREATE TABLE IF NOT EXISTS turnos_ajustes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                turno_config_id INTEGER NOT NULL REFERENCES turnos_config(id) ON DELETE CASCADE,
                fecha_inicio TEXT NOT NULL,
                fecha_fin TEXT NOT NULL,
                vacantes INTEGER NOT NULL,
                dias_semana TEXT -- Sobrescribe los dias del turno si no es NULL
            );

            CREATE TABLE IF NOT EXISTS personal_reglas_ajustes (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                personal_nombre TEXT NOT NULL REFERENCES personal(nombre),
                codigo_regla    TEXT NOT NULL,
                fecha_inicio    TEXT NOT NULL,
                fecha_fin       TEXT NOT NULL,
                accion          TEXT NOT NULL DEFAULT 'SUSPENDER' CHECK(accion IN ('SUSPENDER', 'SOBRESCRIBIR')),
                parametros_json TEXT,
                activo          INTEGER NOT NULL DEFAULT 1
            );

            CREATE INDEX IF NOT EXISTS idx_guardias_nombre  ON guardias(nombre);
            CREATE INDEX IF NOT EXISTS idx_guardias_fecha   ON guardias(fecha);
            CREATE INDEX IF NOT EXISTS idx_bloques_inicio   ON bloques_finde_largo(fecha_inicio);
            CREATE INDEX IF NOT EXISTS idx_licencias_nombre ON licencias(nombre);
            CREATE INDEX IF NOT EXISTS idx_licencias_inicio ON licencias(fecha_inicio);
            CREATE INDEX IF NOT EXISTS idx_turnos_config_serv ON turnos_config(servicio_id);
            CREATE INDEX IF NOT EXISTS idx_turnos_ajustes_fecha ON turnos_ajustes(fecha_inicio);
            CREATE INDEX IF NOT EXISTS idx_pra_nombre_regla ON personal_reglas_ajustes(personal_nombre, codigo_regla);
        """)
        
        # Migraciones seguras para tablas existentes
        try:
            conn.execute("ALTER TABLE personal ADD COLUMN servicio_id INTEGER REFERENCES servicios(id)")
        except sqlite3.OperationalError: pass
        
        try:
            conn.execute("ALTER TABLE personal ADD COLUMN fecha_cumpleanos TEXT")
        except sqlite3.OperationalError: pass
        
        try:
            conn.execute("ALTER TABLE personal ADD COLUMN es_madre INTEGER DEFAULT 0")
        except sqlite3.OperationalError: pass
        
        try:
            conn.execute("ALTER TABLE personal ADD COLUMN es_padre INTEGER DEFAULT 0")
        except sqlite3.OperationalError: pass
        
        try:
            conn.execute("ALTER TABLE personal ADD COLUMN regimen_trabajo TEXT")
        except sqlite3.OperationalError: pass

        try:
            conn.execute("ALTER TABLE personal ADD COLUMN horas_mensuales_reglamentarias INTEGER")
        except sqlite3.OperationalError: pass
        
        try:
            conn.execute("ALTER TABLE turnos_config ADD COLUMN dias_semana TEXT DEFAULT '0,1,2,3,4,5,6'")
        except sqlite3.OperationalError: pass

        try:
            conn.execute("ALTER TABLE turnos_config ADD COLUMN puesto_id INTEGER REFERENCES puestos(id)")
        except sqlite3.OperationalError: pass

        try:
            conn.execute("ALTER TABLE turnos_ajustes ADD COLUMN dias_semana TEXT")
        except sqlite3.OperationalError: pass

        # Migraciones para demanda_config y demanda_ajustes a rangos
        try:
            conn.execute("ALTER TABLE demanda_config ADD COLUMN cantidad_min INTEGER")
            conn.execute("ALTER TABLE demanda_config ADD COLUMN cantidad_max INTEGER")
            # Set default values from the old column
            conn.execute("UPDATE demanda_config SET cantidad_min = cantidad, cantidad_max = cantidad")
        except sqlite3.OperationalError: pass
        
        try:
            conn.execute("ALTER TABLE demanda_ajustes ADD COLUMN cantidad_min INTEGER")
            conn.execute("ALTER TABLE demanda_ajustes ADD COLUMN cantidad_max INTEGER")
            conn.execute("UPDATE demanda_ajustes SET cantidad_min = cantidad, cantidad_max = cantidad")
        except sqlite3.OperationalError: pass

        try:
            conn.execute("ALTER TABLE licencias ADD COLUMN metadata TEXT")
        except sqlite3.OperationalError: pass

        # personal_reglas_ajustes ya se crea via CREATE TABLE IF NOT EXISTS en executescript

        # Asegurar datos iniciales HCRC -> Kinesiología Crítica
        conn.execute("INSERT OR IGNORE INTO organizaciones (id, nombre) VALUES (1, 'HCRC')")
        conn.execute("INSERT OR IGNORE INTO servicios (id, organizacion_id, nombre) VALUES (1, 1, 'Kinesiologia Critica')")
        
        # Vincular personal existente al servicio 1 si no tienen servicio
        conn.execute("UPDATE personal SET servicio_id = 1 WHERE servicio_id IS NULL")

def inicializar_datos_wfm():
    """Puebla las tablas de la nueva arquitectura WFM con los datos base provistos por el usuario."""
    with get_connection() as conn:
        servicio_id = 1
        # 1. Puestos
        for p in ['UTI', 'UCO', 'General', 'Especial']:
            conn.execute("INSERT OR IGNORE INTO puestos (servicio_id, nombre) VALUES (?, ?)", (servicio_id, p))
        
        p_uti = conn.execute("SELECT id FROM puestos WHERE nombre='UTI' AND servicio_id=?", (servicio_id,)).fetchone()[0]
        p_uco = conn.execute("SELECT id FROM puestos WHERE nombre='UCO' AND servicio_id=?", (servicio_id,)).fetchone()[0]
        p_gen = conn.execute("SELECT id FROM puestos WHERE nombre='General' AND servicio_id=?", (servicio_id,)).fetchone()[0]
        p_esp = conn.execute("SELECT id FROM puestos WHERE nombre='Especial' AND servicio_id=?", (servicio_id,)).fetchone()[0]

        # 2. Demanda Config
        demandas = [
            (p_uti, 'Semana', '08:00', '14:00', 5, 5),
            (p_uti, 'Semana', '14:00', '20:00', 4, 4),
            (p_uti, 'Finde_Feriado', '08:00', '20:00', 2, 2),
            
            (p_uco, 'Semana', '08:00', '14:00', 2, 2),
            (p_uco, 'Semana', '14:00', '20:00', 1, 1),
            (p_uco, 'Finde_Feriado', '08:00', '20:00', 1, 1),

            (p_gen, 'Semana', '20:00', '08:00', 2, 2),
            (p_gen, 'Finde_Feriado', '20:00', '08:00', 2, 2)
        ]
        for p_id, td, hi, hf, c_min, c_max in demandas:
            conn.execute("""
                INSERT OR IGNORE INTO demanda_config (puesto_id, tipo_dia, hora_inicio, hora_fin, cantidad_min, cantidad_max)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (p_id, td, hi, hf, c_min, c_max))
            conn.execute("""
                UPDATE demanda_config 
                SET cantidad_min = ?, cantidad_max = ?
                WHERE puesto_id = ? AND tipo_dia = ? AND hora_inicio = ? AND hora_fin = ?
            """, (c_min, c_max, p_id, td, hi, hf))

        # 3. Turnos Config (Actualizar o Insertar)
        turnos_actualizacion = [
            ('Mañana_UTI', '08:00', 6, '0,1,2,3,4', p_uti, 1),
            ('Mañana_UCO', '08:00', 6, '0,1,2,3,4', p_uco, 2),
            ('Mañana_especial', '08:00', 6, '0,1,2,3,4,5,6', p_esp, 3),
            
            ('Dia_UTI', '08:00', 12, '0,1,2,3,4,5,6', p_uti, 4),
            ('Dia_UCO', '08:00', 12, '0,1,2,3,4,5,6', p_uco, 5),
            
            ('Tarde_UTI', '14:00', 6, '0,1,2,3,4', p_uti, 6),
            ('Tarde_UCO', '14:00', 6, '0,1,2,3,4', p_uco, 7),
            ('Tarde_especial', '14:00', 6, '0,1,2,3,4,5,6', p_esp, 8),
            
            ('Noche', '20:00', 12, '0,1,2,3,4,5,6', p_gen, 9),
        ]
        for nom, hi, hs, d_sem, p_id, ordn in turnos_actualizacion:
            conn.execute("""
                UPDATE turnos_config 
                SET hora_inicio = ?, horas = ?, dias_semana = ?, puesto_id = ?, orden = ?
                WHERE nombre = ? AND servicio_id = ?
            """, (hi, hs, d_sem, p_id, ordn, nom, servicio_id))
            
            conn.execute("""
                INSERT OR IGNORE INTO turnos_config (servicio_id, nombre, hora_inicio, horas, dias_semana, puesto_id, orden)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (servicio_id, nom, hi, hs, d_sem, p_id, ordn))

def inicializar_catalogo_reglas():
    """Puebla la tabla reglas_catalogo con las reglas base del sistema."""
    reglas_base = [
        ('MAX_HORAS_SEMANA', 'HARD', 'Límite máximo de horas por semana'),
        ('DESC_POST_NOCHE', 'HARD', 'Horas de descanso obligatorias post guardia nocturna'),
        ('UN_TURNO_POR_DIA', 'HARD', 'Restriccion universal: una persona no puede tener mas de un turno asignado el mismo dia. No tiene parametros configurables.'),
        ('EXCLUIR_TURNOS', 'HARD', 'Prohibición explícita de ciertos turnos para una persona'),
        ('ASIGNACION_FIJA', 'HARD', 'Fuerza a la persona a un turno específico en días específicos'),
        ('MIN_TURNOS', 'HARD', 'Limite minimo de un tipo de turno especifico por bloque semanal. JSON: [{"turno": "Mañana_UTI", "min_por_semana": 4}]'),
        ('MAX_TURNOS', 'HARD', 'Limite maximo de un tipo de turno especifico por bloque semanal. JSON: [{"turno": "Noche", "max_por_semana": 2}]'),
        ('PESO_EQUIDAD_FINDES', 'SOFT', 'Peso de penalización por exceder findes semanales'),
        ('PESO_BRECHA_ANUAL', 'SOFT', 'Peso de penalización por diferencia de horas anuales'),
        ('PESO_BRECHA_MENSUAL', 'SOFT', 'Peso de penalización por diferencia de horas en el mes'),
        ('PESO_BRECHA_SEG', 'SOFT', 'Peso de penalización por diferencia de seguimientos'),
        ('PESO_EQUIDAD_FL3', 'SOFT', 'Peso de penalización por desigualdad en findes largos de 3 días'),
        ('PESO_EQUIDAD_FL4', 'SOFT', 'Peso de penalización por desigualdad en findes largos de 4 días'),
        ('BONUS_SEG_TOTAL', 'SOFT', 'Premio por completar semanas de seguimiento'),
        ('BONUS_SEG_PUNTOS', 'SOFT', 'Premio por cada día de seguimiento individual'),
        ('BONUS_COMBO_FINDE', 'SOFT', 'Premio por trabajar Sabado y Domingo juntos'),
        ('BONUS_PREFERENCIAS', 'SOFT', 'Premio por cumplir preferencias individuales'),
        ('PESO_MIX_HORARIO', 'SOFT', 'Penalización por mezclar mañana y tarde en la misma semana'),
        ('PESO_INCONSISTENCIA', 'SOFT', 'Penalización por cambiar de tipo de turno (ej: UTI a UCO) en la semana'),
        ('TURNOS_PREFERENCIALES', 'SOFT', 'Preferencias individuales de turnos y días'),
        ('CUMPLEANOS_LIBRE', 'HARD', 'El profesional tiene franco obligatorio el día de su cumpleaños'),
        ('DIA_MADRE_PADRE_LIBRE', 'HARD', 'El profesional tiene franco obligatorio el día de la madre o del padre según corresponda'),
        ('PESO_BRECHA_MENSUAL_CALENDARIO', 'SOFT', 'Peso de penalización por diferencia de horas en el mes calendario'),
        ('PESO_EQUIDAD_FINDES_MENSUAL_CALENDARIO', 'SOFT', 'Peso de penalización por desigualdad de findes en mes calendario'),
        ('LIMITES_SOFT_RULES', 'SOFT', 'Límites base para dimensionar el solver (Semanas_Base, Min_Horas, Max_Horas_Limite, etc)'),
        ('MAX_HORAS_MES_CALENDARIO', 'HARD', 'Límite máximo estricto de horas a trabajar por mes calendario. JSON: {"max_horas": 144}'),
        ('DESCANSO_ENTRE_TURNOS', 'HARD', 'Horas mínimas de descanso entre el fin de un turno y el comienzo del siguiente. JSON: {"horas": 12}')
    ]
    with get_connection() as conn:
        for codigo, tipo, desc in reglas_base:
            conn.execute("""
                INSERT OR IGNORE INTO reglas_catalogo (codigo_regla, tipo, descripcion)
                VALUES (?, ?, ?)
            """, (codigo, tipo, desc))



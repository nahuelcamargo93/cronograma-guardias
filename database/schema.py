from .connection import get_connection, DB_PATH
import sqlite3
from datetime import datetime, date, timedelta

def migrar_db_a_codigo_regla(conn):
    """Migra el esquema de la base de datos reemplazando regla_id por codigo_regla en tablas de reglas."""
    try:
        cur = conn.execute("PRAGMA table_info(servicios_reglas)")
        columns = [row[1] for row in cur.fetchall()]
    except sqlite3.OperationalError:
        return # La tabla no existe aún

    if 'regla_id' in columns:
        print("Iniciando migración de base de datos a schema con codigo_regla...")
        # 1. Crear tablas temporales con el esquema nuevo
        conn.execute("""
            CREATE TABLE IF NOT EXISTS organizaciones_reglas_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                organizacion_id INTEGER NOT NULL REFERENCES organizaciones(id),
                codigo_regla TEXT NOT NULL REFERENCES reglas_catalogo(codigo_regla) ON UPDATE CASCADE ON DELETE CASCADE,
                parametros_json TEXT,
                UNIQUE(organizacion_id, codigo_regla)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS servicios_reglas_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                servicio_id INTEGER NOT NULL REFERENCES servicios(id),
                codigo_regla TEXT NOT NULL REFERENCES reglas_catalogo(codigo_regla) ON UPDATE CASCADE ON DELETE CASCADE,
                parametros_json TEXT,
                UNIQUE(servicio_id, codigo_regla)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS personal_reglas_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                personal_nombre TEXT NOT NULL REFERENCES personal(nombre),
                codigo_regla TEXT NOT NULL REFERENCES reglas_catalogo(codigo_regla) ON UPDATE CASCADE ON DELETE CASCADE,
                parametros_json TEXT,
                UNIQUE(personal_nombre, codigo_regla)
            )
        """)

        # 2. Pasar los datos resolviendo regla_id a codigo_regla
        conn.execute("""
            INSERT INTO organizaciones_reglas_new (id, organizacion_id, codigo_regla, parametros_json)
            SELECT o.id, o.organizacion_id, r.codigo_regla, o.parametros_json
            FROM organizaciones_reglas o
            JOIN reglas_catalogo r ON o.regla_id = r.id
        """)
        conn.execute("""
            INSERT INTO servicios_reglas_new (id, servicio_id, codigo_regla, parametros_json)
            SELECT s.id, s.servicio_id, r.codigo_regla, s.parametros_json
            FROM servicios_reglas s
            JOIN reglas_catalogo r ON s.regla_id = r.id
        """)
        conn.execute("""
            INSERT INTO personal_reglas_new (id, personal_nombre, codigo_regla, parametros_json)
            SELECT p.id, p.personal_nombre, r.codigo_regla, p.parametros_json
            FROM personal_reglas p
            JOIN reglas_catalogo r ON p.regla_id = r.id
        """)

        # 3. Borrar tablas viejas y renombrar las nuevas
        conn.execute("DROP TABLE organizaciones_reglas")
        conn.execute("DROP TABLE servicios_reglas")
        conn.execute("DROP TABLE personal_reglas")

        conn.execute("ALTER TABLE organizaciones_reglas_new RENAME TO organizaciones_reglas")
        conn.execute("ALTER TABLE servicios_reglas_new RENAME TO servicios_reglas")
        conn.execute("ALTER TABLE personal_reglas_new RENAME TO personal_reglas")
        print("Migración de base de datos finalizada con éxito.")


def inicializar_db():
    """Crea las tablas si no existen. Seguro de llamar múltiples veces."""
    with get_connection() as conn:
        migrar_db_a_codigo_regla(conn)
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
                categoria TEXT,
                rol    TEXT NOT NULL,
                servicio_id INTEGER REFERENCES servicios(id),
                fecha_cumpleanos TEXT,
                es_madre INTEGER DEFAULT 0,
                es_padre INTEGER DEFAULT 0,
                regimen_trabajo TEXT,
                horas_mensuales_reglamentarias INTEGER,
                activo INTEGER DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS cronogramas (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha_inicio TEXT NOT NULL,
                fecha_fin    TEXT NOT NULL,
                creado_en    TEXT,
                notas        TEXT,
                estado       TEXT DEFAULT 'aprobado'
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

            CREATE TABLE IF NOT EXISTS semanas_categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cronograma_id INTEGER NOT NULL REFERENCES cronogramas(id) ON DELETE CASCADE,
                nombre TEXT NOT NULL REFERENCES personal(nombre),
                fecha_lunes TEXT NOT NULL,
                categoria TEXT NOT NULL,
                UNIQUE(cronograma_id, nombre, fecha_lunes)
            );

            CREATE TABLE IF NOT EXISTS licencias (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre       TEXT NOT NULL REFERENCES personal(nombre),
                tipo         TEXT NOT NULL CHECK(tipo IN ('LPP', 'LAR', 'CM', 'LM')),
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
                codigo_regla TEXT NOT NULL REFERENCES reglas_catalogo(codigo_regla) ON UPDATE CASCADE ON DELETE CASCADE,
                parametros_json TEXT,
                activo INTEGER DEFAULT 1,
                UNIQUE(organizacion_id, codigo_regla)
            );

            CREATE TABLE IF NOT EXISTS servicios_reglas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                servicio_id INTEGER NOT NULL REFERENCES servicios(id),
                codigo_regla TEXT NOT NULL REFERENCES reglas_catalogo(codigo_regla) ON UPDATE CASCADE ON DELETE CASCADE,
                parametros_json TEXT,
                activo INTEGER DEFAULT 1,
                UNIQUE(servicio_id, codigo_regla)
            );

            CREATE TABLE IF NOT EXISTS personal_reglas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                personal_nombre TEXT NOT NULL REFERENCES personal(nombre),
                codigo_regla TEXT NOT NULL REFERENCES reglas_catalogo(codigo_regla) ON UPDATE CASCADE ON DELETE CASCADE,
                parametros_json TEXT,
                activo INTEGER DEFAULT 1,
                UNIQUE(personal_nombre, codigo_regla)
            );

            CREATE TABLE IF NOT EXISTS puestos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                servicio_id INTEGER NOT NULL REFERENCES servicios(id),
                nombre TEXT NOT NULL,
                UNIQUE(servicio_id, nombre)
            );

            CREATE TABLE IF NOT EXISTS personal_puestos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                personal_nombre TEXT NOT NULL REFERENCES personal(nombre) ON DELETE CASCADE,
                puesto_id INTEGER NOT NULL REFERENCES puestos(id) ON DELETE CASCADE,
                UNIQUE(personal_nombre, puesto_id)
            );

            CREATE TABLE IF NOT EXISTS demanda_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                puesto_id INTEGER NOT NULL REFERENCES puestos(id),
                tipo_dia TEXT NOT NULL CHECK(tipo_dia IN ('Semana', 'Finde_Feriado')),
                hora_inicio TEXT NOT NULL,
                hora_fin TEXT NOT NULL,
                cantidad_min INTEGER,
                cantidad_max INTEGER,
                dias_semana TEXT,
                activo INTEGER DEFAULT 1,
                UNIQUE(puesto_id, tipo_dia, hora_inicio, hora_fin, dias_semana)
            );

            CREATE TABLE IF NOT EXISTS demanda_ajustes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                demanda_config_id INTEGER NOT NULL REFERENCES demanda_config(id) ON DELETE CASCADE,
                fecha_inicio TEXT NOT NULL,
                fecha_fin TEXT NOT NULL,
                cantidad_min INTEGER,
                cantidad_max INTEGER,
                dias_semana TEXT,
                activo INTEGER DEFAULT 1
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
                dias_semana TEXT, -- Sobrescribe los dias del turno si no es NULL
                activo INTEGER DEFAULT 1
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

            CREATE TABLE IF NOT EXISTS servicios_reglas_ajustes (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                servicio_id     INTEGER NOT NULL REFERENCES servicios(id),
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
            CREATE INDEX IF NOT EXISTS idx_sra_servicio_regla ON servicios_reglas_ajustes(servicio_id, codigo_regla);

            CREATE TABLE IF NOT EXISTS infracciones_debug (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cronograma_id INTEGER NOT NULL REFERENCES cronogramas(id) ON DELETE CASCADE,
                codigo_regla TEXT NOT NULL,
                detalle TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_infracciones_crono ON infracciones_debug(cronograma_id);

            CREATE TABLE IF NOT EXISTS feriados (
                fecha TEXT PRIMARY KEY,
                descripcion TEXT
            );

            CREATE TABLE IF NOT EXISTS feriados_exclusiones (
                fecha TEXT NOT NULL REFERENCES feriados(fecha) ON DELETE CASCADE,
                servicio_id INTEGER NOT NULL REFERENCES servicios(id) ON DELETE CASCADE,
                PRIMARY KEY (fecha, servicio_id)
            );
        """)
        
        # Migraciones seguras para tablas existentes
        try:
            conn.execute("ALTER TABLE cronogramas ADD COLUMN estado TEXT DEFAULT 'aprobado'")
        except sqlite3.OperationalError: pass
        
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
            conn.execute("ALTER TABLE personal ADD COLUMN activo INTEGER DEFAULT 1")
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

        try:
            conn.execute("ALTER TABLE licencias ADD COLUMN activa INTEGER DEFAULT 1")
        except sqlite3.OperationalError: pass

        try:
            conn.execute("ALTER TABLE licencias ADD COLUMN servicio_id INTEGER REFERENCES servicios(id)")
        except sqlite3.OperationalError: pass
        try:
            conn.execute("""
                UPDATE licencias
                SET servicio_id = (
                    SELECT p.servicio_id FROM personal p WHERE p.nombre = licencias.nombre
                )
                WHERE servicio_id IS NULL
            """)
        except Exception as e:
            print(f"[schema] Error migración servicio_id en licencias: {e}")

        # Agregar columna activo a las tablas que no lo tenian
        tablas_a_migrar_activo = [
            "organizaciones_reglas", "servicios_reglas", "personal_reglas",
            "demanda_config", "demanda_ajustes", "turnos_ajustes"
        ]
        for t_name in tablas_a_migrar_activo:
            try:
                conn.execute(f"ALTER TABLE {t_name} ADD COLUMN activo INTEGER DEFAULT 1")
            except sqlite3.OperationalError:
                pass

        # Migración para actualizar la restricción UNIQUE de demanda_config e incluir dias_semana
        try:
            cur = conn.execute("PRAGMA table_info(demanda_config)")
            columns = [row[1] for row in cur.fetchall()]
            if 'dias_semana' not in columns:
                conn.execute("ALTER TABLE demanda_config RENAME TO demanda_config_old")
                conn.execute("""
                    CREATE TABLE demanda_config (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        puesto_id INTEGER NOT NULL REFERENCES puestos(id),
                        tipo_dia TEXT NOT NULL CHECK(tipo_dia IN ('Semana', 'Finde_Feriado')),
                        hora_inicio TEXT NOT NULL,
                        hora_fin TEXT NOT NULL,
                        cantidad_min INTEGER,
                        cantidad_max INTEGER,
                        dias_semana TEXT,
                        activo INTEGER DEFAULT 1,
                        UNIQUE(puesto_id, tipo_dia, hora_inicio, hora_fin, dias_semana)
                    )
                """)
                conn.execute("""
                    INSERT INTO demanda_config (id, puesto_id, tipo_dia, hora_inicio, hora_fin, cantidad_min, cantidad_max)
                    SELECT id, puesto_id, tipo_dia, hora_inicio, hora_fin, cantidad_min, cantidad_max
                    FROM demanda_config_old
                """)
                conn.execute("DROP TABLE demanda_config_old")
                print("Migración de demanda_config finalizada con éxito.")
        except Exception as e:
            print(f"Error migrando demanda_config: {e}")

        # personal_reglas_ajustes ya se crea via CREATE TABLE IF NOT EXISTS en executescript

        # --- TAREA 1.1: Añadir servicio_id a tablas clave para filtrado directo en DB Browser ---

        # 1. personal_reglas.servicio_id
        try:
            conn.execute("ALTER TABLE personal_reglas ADD COLUMN servicio_id INTEGER REFERENCES servicios(id)")
        except sqlite3.OperationalError: pass
        try:
            conn.execute("""
                UPDATE personal_reglas
                SET servicio_id = COALESCE(
                    (SELECT p.servicio_id FROM personal p WHERE p.nombre = personal_reglas.personal_nombre),
                    1
                )
                WHERE servicio_id IS NULL
            """)
        except Exception as e:
            print(f"[schema] Error migración servicio_id en personal_reglas: {e}")

        # 2. personal_reglas_ajustes.servicio_id
        try:
            conn.execute("ALTER TABLE personal_reglas_ajustes ADD COLUMN servicio_id INTEGER REFERENCES servicios(id)")
        except sqlite3.OperationalError: pass
        try:
            conn.execute("""
                UPDATE personal_reglas_ajustes
                SET servicio_id = COALESCE(
                    (SELECT p.servicio_id FROM personal p WHERE p.nombre = personal_reglas_ajustes.personal_nombre),
                    1
                )
                WHERE servicio_id IS NULL
            """)
        except Exception as e:
            print(f"[schema] Error migración servicio_id en personal_reglas_ajustes: {e}")

        # 3. personal_puestos.servicio_id
        try:
            conn.execute("ALTER TABLE personal_puestos ADD COLUMN servicio_id INTEGER REFERENCES servicios(id)")
        except sqlite3.OperationalError: pass
        try:
            conn.execute("""
                UPDATE personal_puestos
                SET servicio_id = COALESCE(
                    (SELECT p.servicio_id FROM personal p WHERE p.nombre = personal_puestos.personal_nombre),
                    1
                )
                WHERE servicio_id IS NULL
            """)
        except Exception as e:
            print(f"[schema] Error migración servicio_id en personal_puestos: {e}")

        # 4. guardias.servicio_id
        try:
            conn.execute("ALTER TABLE guardias ADD COLUMN servicio_id INTEGER REFERENCES servicios(id)")
        except sqlite3.OperationalError: pass
        try:
            conn.execute("""
                UPDATE guardias
                SET servicio_id = COALESCE(
                    (SELECT p.servicio_id FROM personal p WHERE p.nombre = guardias.nombre),
                    1
                )
                WHERE servicio_id IS NULL
            """)
        except Exception as e:
            print(f"[schema] Error migración servicio_id en guardias: {e}")

        # Asegurar datos iniciales HCRC -> Kinesiología Crítica
        conn.execute("INSERT OR IGNORE INTO organizaciones (id, nombre) VALUES (1, 'HCRC')")
        conn.execute("INSERT OR IGNORE INTO servicios (id, organizacion_id, nombre) VALUES (1, 1, 'Kinesiologia Critica')")
        
        # Asegurar COM Juana Koslay -> Personal de Monitoreo
        conn.execute("INSERT OR IGNORE INTO organizaciones (nombre) VALUES ('COM Juana Koslay')")
        org_row = conn.execute("SELECT id FROM organizaciones WHERE nombre = 'COM Juana Koslay'").fetchone()
        if org_row:
            conn.execute("INSERT OR IGNORE INTO servicios (organizacion_id, nombre) VALUES (?, 'Personal de Monitoreo')", (org_row[0],))
            
        # Vincular personal existente al servicio 1 si no tienen servicio
        conn.execute("UPDATE personal SET servicio_id = 1 WHERE servicio_id IS NULL")

        # Migración de personal_puestos
        try:
            empleados_migrar = conn.execute("SELECT nombre, rol, categoria, servicio_id FROM personal").fetchall()
            puestos_db = conn.execute("SELECT id, nombre, servicio_id FROM puestos").fetchall()
            
            puestos_map = {}
            for p_id, p_nom, p_serv in puestos_db:
                puestos_map[(p_serv, p_nom)] = p_id
            
            for emp_nombre, emp_rol, emp_cat, emp_serv in empleados_migrar:
                puestos_a_asignar = []
                if emp_serv == 1:
                    if emp_cat == 'Ambos':
                        puestos_a_asignar.extend(['UTI', 'UCO'])
                    elif emp_rol == 'UTI':
                        puestos_a_asignar.append('UTI')
                    elif emp_rol == 'UCO':
                        puestos_a_asignar.append('UCO')
                    elif emp_rol == 'General':
                        puestos_a_asignar.append('General')
                    elif emp_rol == 'Especial':
                        puestos_a_asignar.append('Especial')
                    else:
                        puestos_a_asignar.append(emp_rol)
                else:
                    puestos_a_asignar.append(emp_rol)
                
                for p_nom in puestos_a_asignar:
                    p_id = puestos_map.get((emp_serv, p_nom))
                    if p_id:
                        conn.execute(
                            "INSERT OR IGNORE INTO personal_puestos (personal_nombre, puesto_id) VALUES (?, ?)", 
                            (emp_nombre, p_id)
                        )
        except Exception as e:
            print(f"Error en migración automática de personal_puestos: {e}")

        # Asegurar feriados por defecto
        try:
            default_feriados = [
                ("2026-05-25", "Revolución de Mayo"),
                ("2026-06-15", "Paso a la Inmortalidad del Gral. Güemes"),
                ("2026-06-20", "Paso a la Inmortalidad del Gral. Belgrano"),
                ("2026-07-09", "Día de la Independencia")
            ]
            for f_fecha, f_desc in default_feriados:
                conn.execute("INSERT OR IGNORE INTO feriados (fecha, descripcion) VALUES (?, ?)", (f_fecha, f_desc))
        except Exception as e:
            print(f"Error al inicializar feriados: {e}")

        # Asegurar catálogo de reglas completo
        try:
            inicializar_catalogo_reglas(conn)
        except Exception as e:
            print(f"Error al inicializar catálogo de reglas: {e}")

        # Asegurar regla FINDE_POST_LICENCIA configurada para servicio_id = 2 como "completo"
        try:
            conn.execute("""
                INSERT OR IGNORE INTO servicios_reglas (servicio_id, codigo_regla, parametros_json, activo)
                VALUES (2, 'FINDE_POST_LICENCIA', '{"configuracion": "completo"}', 1)
            """)
            conn.execute("""
                UPDATE servicios_reglas 
                SET parametros_json = '{"configuracion": "completo"}', activo = 1
                WHERE servicio_id = 2 AND codigo_regla = 'FINDE_POST_LICENCIA'
            """)
        except Exception as e:
            print(f"Error al inicializar regla FINDE_POST_LICENCIA en servicio 2: {e}")

        # Asegurar regla FRANCOS_FIN_MES configurada para servicio_id = 3 y personal Polleti Natalia
        try:
            conn.execute("""
                INSERT OR IGNORE INTO servicios_reglas (servicio_id, codigo_regla, parametros_json, activo)
                VALUES (3, 'FRANCOS_FIN_MES', '{"por_dias": {"5": 2, "4": 1}, "peso": 5000}', 1)
            """)
            conn.execute("""
                UPDATE servicios_reglas 
                SET parametros_json = '{"por_dias": {"5": 2, "4": 1}, "peso": 5000}', activo = 1
                WHERE servicio_id = 3 AND codigo_regla = 'FRANCOS_FIN_MES'
            """)
            
            # Verificar si existe POLETTI NATALIA en la BD antes de insertar la regla personal
            # El usuario la mencionó como "Polleti Natalia", en la BD figura como "POLETTI NATALIA"
            res_p = conn.execute("SELECT nombre FROM personal WHERE nombre = 'POLETTI NATALIA'").fetchone()
            if not res_p:
                # Fallback por si acaso
                res_p = conn.execute("SELECT nombre FROM personal WHERE nombre LIKE '%POLETTI NATALIA%'").fetchone()
            
            if res_p:
                nombre_exacto = res_p[0]
                conn.execute("""
                    INSERT OR IGNORE INTO personal_reglas (personal_nombre, codigo_regla, parametros_json, activo, servicio_id)
                    VALUES (?, 'FRANCOS_FIN_MES', '{"por_dias": {"5": 3, "4": 2}, "peso": 5000}', 1, 3)
                """, (nombre_exacto,))
                conn.execute("""
                    UPDATE personal_reglas 
                    SET parametros_json = '{"por_dias": {"5": 3, "4": 2}, "peso": 5000}', activo = 1
                    WHERE personal_nombre = ? AND codigo_regla = 'FRANCOS_FIN_MES'
                """, (nombre_exacto,))
        except Exception as e:
            print(f"Error al inicializar regla FRANCOS_FIN_MES para servicio 3 / Natalia Polleti: {e}")




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
            ('Dia_especial', '08:00', 12, '0,1,2,3,4,5,6', p_esp, 10),
            
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

        # 4. Asegurar Puestos y Turnos para Personal de Monitoreo (Organizacion 2, Servicio 1)
        monit_row = conn.execute("SELECT id FROM servicios WHERE nombre = 'Personal de Monitoreo'").fetchone()
        if monit_row:
            monit_serv_id = monit_row[0]
            
            # Asegurar puestos
            conn.execute("INSERT OR IGNORE INTO puestos (servicio_id, nombre) VALUES (?, 'Supervisor')", (monit_serv_id,))
            conn.execute("INSERT OR IGNORE INTO puestos (servicio_id, nombre) VALUES (?, 'Monitorista')", (monit_serv_id,))
            
            p_sup = conn.execute("SELECT id FROM puestos WHERE nombre='Supervisor' AND servicio_id=?", (monit_serv_id,)).fetchone()[0]
            p_mon = conn.execute("SELECT id FROM puestos WHERE nombre='Monitorista' AND servicio_id=?", (monit_serv_id,)).fetchone()[0]
            
            monit_turnos = [
                ('00-06_Supervisor', '00:00', 6, '0,1,2,3,4,5,6', p_sup, 1),
                ('06-12_Supervisor', '06:00', 6, '0,1,2,3,4,5,6', p_sup, 2),
                ('12-18_Supervisor', '12:00', 6, '0,1,2,3,4,5,6', p_sup, 3),
                ('18-24_Supervisor', '18:00', 6, '0,1,2,3,4,5,6', p_sup, 4),
                ('00-06_Monitorista', '00:00', 6, '0,1,2,3,4,5,6', p_mon, 5),
                ('06-12_Monitorista', '06:00', 6, '0,1,2,3,4,5,6', p_mon, 6),
                ('12-18_Monitorista', '12:00', 6, '0,1,2,3,4,5,6', p_mon, 7),
                ('18-24_Monitorista', '18:00', 6, '0,1,2,3,4,5,6', p_mon, 8),
            ]
            for nom, hi, hs, d_sem, p_id, ordn in monit_turnos:
                conn.execute("""
                    UPDATE turnos_config 
                    SET hora_inicio = ?, horas = ?, dias_semana = ?, puesto_id = ?, orden = ?, activo = 1
                    WHERE nombre = ? AND servicio_id = ?
                """, (hi, hs, d_sem, p_id, ordn, nom, monit_serv_id))
                
                conn.execute("""
                    INSERT OR IGNORE INTO turnos_config (servicio_id, nombre, hora_inicio, horas, dias_semana, puesto_id, orden, activo)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                """, (monit_serv_id, nom, hi, hs, d_sem, p_id, ordn))

def inicializar_catalogo_reglas(conn=None):
    """Puebla la tabla reglas_catalogo con las reglas base del sistema."""
    reglas_base = [
        ('MAX_HORAS_SEMANA', 'HARD', 'Límite máximo de horas por semana'),
        ('DESC_POST_NOCHE', 'HARD', 'Horas de descanso obligatorias post guardia nocturna'),
        ('UN_TURNO_POR_DIA', 'HARD', 'Restriccion universal: una persona no puede tener mas de un turno asignado el mismo dia. No tiene parametros configurables.'),
        ('EXCLUIR_TURNOS', 'HARD', 'Prohibición explícita de ciertos turnos para una persona'),
        ('ASIGNACION_FIJA', 'HARD', 'Fuerza a la persona a un turno específico en días específicos'),
        ('MIN_TURNOS', 'HARD', 'Limite minimo de un tipo de turno especifico por bloque semanal. JSON: [{"turno": "Mañana_UTI", "min_por_semana": 4}]'),
        ('MAX_TURNOS', 'HARD', 'Limite maximo de un tipo de turno especifico por bloque semanal. JSON: [{"turno": "Noche", "max_por_semana": 2}]'),
        ('PESO_BRECHA_ANUAL', 'SOFT', 'Peso de penalización por diferencia de horas anuales'),
        ('PESO_BRECHA_MENSUAL', 'SOFT', 'Peso de penalización por diferencia de horas en el mes'),
        ('PESO_BRECHA_HORAS', 'SOFT', 'Peso de penalización por brecha incremental de horas asignadas en base a disponibilidad'),
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
        ('LIMITES_SOFT_RULES', 'SOFT', 'Límite superior de horas mensuales para dimensionar variables del solver (MAX_HORAS_LIMITE_BASE)'),
        ('MAX_HORAS_MES_CALENDARIO', 'HARD', 'Límite máximo estricto de horas a trabajar por mes calendario. JSON: {"max_horas": 144}'),
        ('DESCANSO_ENTRE_TURNOS', 'HARD', 'Horas mínimas de descanso entre el fin de un turno y el comienzo del siguiente. JSON: {"horas": 12}'),
        ('PATRON_CICLICO', 'HARD', 'Patrón cíclico estricto de X días de trabajo seguidos de Y días de franco. JSON: {"trabajo": 10, "franco": 4}'),
        ('PESO_BRECHA_DIARIA_PERSONAL', 'SOFT', 'Peso de penalización por diferencia de personal asignado por día y puesto/turno'),
        ('MIN_FINDES_MES', 'HARD', 'Asegura que el personal tenga al menos N fines de semana trabajados en el mes.'),
        ('EXACTO_FINDES_MES', 'HARD', 'Asegura que el personal tenga exactamente N fines de semana trabajados en el mes.'),
        ('MIN_DIA_ESPECIFICO_MES', 'HARD', 'Asegura que el personal trabaje al menos N veces un dia de la semana especifico en el mes. JSON: {"dia_semana": "Viernes", "min_dias": 1}'),
        ('EXACTO_DIA_ESPECIFICO_MES', 'HARD', 'Asegura que el personal trabaje exactamente N veces un dia de la semana especifico en el mes. JSON: {"dia_semana": "Viernes", "exacto_dias": 1}'),
        ('EXACTO_FINDE_Y_DIA', 'HARD', 'Regla unificada para fines de semana y días específicos (ej. viernes) basada en la cantidad de fines de semana y días hábiles. JSON: {"dia_semana": "Viernes", "findes_por_disponibilidad": {"5": 2, "4": 2, "3": 2, "2": 1, "1": 1, "0": 0}, "dias_por_disponibilidad": {"5": 2, "4": 1, "3": 0, "2": 1, "1": 0, "0": 0}, "modo": "HARD", "peso_soft": 100000}'),
        ('FINDES_COMPLETOS_Y_MEDIOS', 'HARD', 'Asegura la cantidad exacta de fines de semana completos y medios trabajados según la disponibilidad. JSON: {"por_disponibilidad": {"4": {"completos": 2, "medios": 1}}}'),
        ('MEZCLA_SEMANAL_DURA', 'HARD', 'Prohíbe mezclar familias de turno (M, T, TN, N) en una misma semana'),
        ('PESO_EQUIDAD_FERIADOS', 'SOFT', 'Peso de penalización por desigualdad en feriados trabajados anuales'),
        ('PESO_EQUIDAD_FSL', 'SOFT', 'Regla de equidad unificada para fines de semana largos (FSL3 y FSL4) con nivelación histórica'),
        ('PESO_BRECHA_TURNO', 'SOFT', 'Peso de penalización para nivelar noches (turnos Noche) con soporte de nivelación histórica'),
        ('SEMANAS_SEGUIMIENTO_REQUERIDAS', 'HARD', 'Mínimo de semanas de seguimiento de mañana, tarde y total requeridas en el mes. JSON: {"min_manana": 1, "min_tarde": 2, "min_total": 3}'),
        ('NO_REPETIR_TURNO_CONSECUTIVO', 'HARD', 'Prohíbe repetir el mismo tipo de turno semanal en semanas consecutivas'),
        ('ORDEN_ROTACION_SEMANAL', 'HARD', 'Restricción de orden ideal de rotación de turnos semanal (T -> M -> N -> TN)'),
        ('MAX_FRANCOS_SEMANA', 'HARD', 'Límite máximo de francos por semana calendario'),
        ('PUESTOS_SOLO_FIJOS', 'HARD', 'Puestos específicos donde las asignaciones son exclusivas a través de ASIGNACION_FIJA. JSON: {"puestos": ["Especial"]}'),
        ('SOLO_ASIGNACIONES_FIJAS', 'HARD', 'El profesional solo realiza guardias asignadas mediante ASIGNACION_FIJA y no se le asignan turnos libres.'),
        ('FINDE_POST_LICENCIA', 'HARD', 'El primer fin de semana después de volver de una licencia debe trabajarse. JSON: {"configuracion": "completo"}'),
        ('MAX_FRANCOS_CONTINUOS', 'HARD', 'Límite máximo de francos seguidos (consecutivos) permitidos. JSON: {"max_francos": 3, "modo": "HARD", "peso_soft": 10000}'),
        ('MIN_HORAS_SEMANA', 'HARD', 'Piso mínimo de horas trabajadas por semana calendario'),
        ('FRANCOS_FIN_MES', 'SOFT', 'Asegura la cantidad de francos en la última semana del mes si esta es incompleta (tiene 4 o 5 días).'),
        ('MIN_TURNOS_SEMANA', 'HARD', 'Piso mínimo de turnos trabajados por semana calendario'),
        ('MIN_FRANCOS_SEMANA', 'HARD', 'Piso mínimo de francos por semana calendario')
    ]
    if conn is not None:
        for codigo, tipo, desc in reglas_base:
            conn.execute("""
                INSERT OR IGNORE INTO reglas_catalogo (codigo_regla, tipo, descripcion)
                VALUES (?, ?, ?)
            """, (codigo, tipo, desc))
    else:
        with get_connection() as conn_new:
            for codigo, tipo, desc in reglas_base:
                conn_new.execute("""
                    INSERT OR IGNORE INTO reglas_catalogo (codigo_regla, tipo, descripcion)
                    VALUES (?, ?, ?)
                """, (codigo, tipo, desc))



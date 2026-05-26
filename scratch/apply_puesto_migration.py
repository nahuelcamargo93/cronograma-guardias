"""Script de migracion - version ASCII para compatibilidad."""
import sys
sys.path.insert(0, '.')
import sqlite3
import time

DB_PATH = 'cronograma_inteligente.db'

# Intentar conectar con timeout
conn = sqlite3.connect(DB_PATH, timeout=10)
conn.row_factory = sqlite3.Row
conn.execute("PRAGMA journal_mode=WAL")

# 1. Agregar columna es_primario si no existe
try:
    cols = [r[1] for r in conn.execute("PRAGMA table_info(personal_puestos)").fetchall()]
    if 'es_primario' not in cols:
        conn.execute("ALTER TABLE personal_puestos ADD COLUMN es_primario INTEGER DEFAULT 1")
        conn.commit()
        print("[OK] Columna es_primario agregada a personal_puestos (todos = 1 por defecto)")
    else:
        print("[OK] Columna es_primario ya existe en personal_puestos")
except Exception as e:
    print(f"[ERROR] {e}")

# 2. Registrar la regla en el catalogo
try:
    conn.execute("""
        INSERT OR IGNORE INTO reglas_catalogo (codigo_regla, tipo, descripcion)
        VALUES (
            'PENALIZACION_PUESTO_NO_PREFERIDO',
            'SOFT',
            'Penaliza cuando una persona es asignada a un turno de un puesto que NO es su puesto primario. JSON: {"peso": 500}'
        )
    """)
    conn.commit()
    row = conn.execute("SELECT codigo_regla, tipo FROM reglas_catalogo WHERE codigo_regla = 'PENALIZACION_PUESTO_NO_PREFERIDO'").fetchone()
    print(f"[OK] Regla en catalogo: {tuple(row)}")
except Exception as e:
    print(f"[ERROR] registrando regla en catalogo: {e}")

# 3. Activar la regla para el servicio 3 (Área Médica UTI)
try:
    conn.execute("""
        INSERT OR IGNORE INTO servicios_reglas (servicio_id, codigo_regla, parametros_json, activo)
        VALUES (3, 'PENALIZACION_PUESTO_NO_PREFERIDO', '{"peso": 500}', 1)
    """)
    conn.commit()
    row = conn.execute("SELECT * FROM servicios_reglas WHERE servicio_id = 3 AND codigo_regla = 'PENALIZACION_PUESTO_NO_PREFERIDO'").fetchone()
    print(f"[OK] Regla activa en servicio 3: {dict(row)}")
except Exception as e:
    print(f"[ERROR] activando regla en servicio 3: {e}")

# 4. Configurar puestos primarios (marcar Planta como no primario para residentes en servicio 3)
try:
    conn.execute("""
        UPDATE personal_puestos
        SET es_primario = 0
        WHERE personal_nombre IN (
            'Arce Carolina', 'Biscarra Joaquín Martin', 'Matricadi Wendy Ailen',
            'Nuñez Florencia Natalia', 'Pacheco Celeste', 'Palermo Agustín',
            'Villegas Oliva Maria Belén'
        )
        AND puesto_id = (SELECT id FROM puestos WHERE nombre = 'Planta' AND servicio_id = 3)
    """)
    conn.commit()
    print("[OK] Puestos no preferidos (Planta) marcados con es_primario = 0 para los residentes")
except Exception as e:
    print(f"[ERROR] configurando puestos primarios: {e}")

# 5. Verificar columnas actuales y registros
cols = [r[1] for r in conn.execute("PRAGMA table_info(personal_puestos)").fetchall()]
print(f"[OK] Columnas personal_puestos: {cols}")

conn.close()
print("[OK] Migracion completa finalizada.")

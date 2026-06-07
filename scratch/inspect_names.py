import sqlite3
import os
import json

DB_PATH = "cronograma_inteligente.db"

def inspect():
    if not os.path.exists(DB_PATH):
        print(f"Error: {DB_PATH} no existe.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Obtener los servicios 1 y 3
    cursor.execute("SELECT id, nombre FROM servicios WHERE id IN (1, 3)")
    servicios = cursor.fetchall()
    print("=== SERVICIOS ENCONTRADOS ===")
    for s_id, s_nom in servicios:
        print(f"ID: {s_id} - Nombre: {s_nom}")
    print()

    # 2. Obtener personal del servicio 1 y 3
    cursor.execute("SELECT nombre, servicio_id FROM personal WHERE servicio_id IN (1, 3)")
    personal = cursor.fetchall()
    print(f"=== PERSONAL REGISTRADO (Total: {len(personal)}) ===")
    for p_nom, s_id in personal:
        print(f"Servicio: {s_id} | Nombre: {p_nom}")
    print()

    # 3. Buscar todas las tablas que contienen columnas de tipo TEXT que podrían tener nombres de personal
    # Para estar seguros, buscaremos en todo el esquema de la BD.
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall() if not row[0].startswith('sqlite_')]

    print("=== BUSCANDO PRESENCIA DE NOMBRES EN OTRAS TABLAS ===")
    nombres_s1_s3 = [p[0] for p in personal]
    
    # Mapeo de tablas y columnas donde coinciden
    coincidencias = {}
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [col[1] for col in cursor.fetchall()]
        
        for col in columns:
            # Consultar si hay coincidencias exactas con algún nombre del personal de S1 o S3
            placeholders = ",".join(["?"] * len(nombres_s1_s3))
            if not placeholders:
                continue
            query = f"SELECT DISTINCT {col} FROM {table} WHERE {col} IN ({placeholders})"
            try:
                cursor.execute(query, nombres_s1_s3)
                results = [r[0] for r in cursor.fetchall() if r[0] is not None]
                if results:
                    if table not in coincidencias:
                        coincidencias[table] = []
                    coincidencias[table].append((col, len(results), results))
            except sqlite3.OperationalError:
                # Puede fallar si la columna no es de tipo compatible, ignoramos
                pass

    for table, cols in coincidencias.items():
        print(f"Tabla: {table}")
        for col, count, matched in cols:
            print(f"  - Columna '{col}': {count} nombres distintos coinciden. Ejemplos: {matched[:5]}")
    
    # 4. Además, buscar si los nombres aparecen dentro de columnas de tipo JSON (como parametros_json en personal_reglas, servicios_reglas, etc.)
    print("\n=== BUSCANDO NOMBRES DENTRO DE JSON (parametros_json) ===")
    tablas_json = ['personal_reglas', 'servicios_reglas', 'personal_reglas_ajustes', 'servicios_reglas_ajustes']
    for table in tablas_json:
        # Verificar si la tabla existe
        cursor.execute(f"SELECT count(*) FROM sqlite_master WHERE type='table' AND name='{table}'")
        if cursor.fetchone()[0] == 0:
            continue
        
        # Buscar en parametros_json
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [col[1] for col in cursor.fetchall()]
        if 'parametros_json' in columns:
            cursor.execute(f"SELECT id, parametros_json FROM {table} WHERE parametros_json IS NOT NULL")
            rows = cursor.fetchall()
            for r_id, p_json in rows:
                for nombre in nombres_s1_s3:
                    if nombre in p_json:
                        print(f"Coincidencia en tabla '{table}', ID: {r_id}: contiene el nombre '{nombre}' en JSON: {p_json}")

    conn.close()

if __name__ == '__main__':
    inspect()

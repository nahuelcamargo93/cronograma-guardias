import sqlite3
import json
import os

DB_PATH = "cronograma_inteligente.db"

def verify():
    if not os.path.exists(DB_PATH):
        print(f"Error: {DB_PATH} no existe.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    errors = 0

    print("=== INICIANDO AUDITORÍA DE NORMALIZACIÓN ===\n")

    # 1. Verificar que no existan nombres viejos en la tabla 'personal' para servicio 1
    cursor.execute("SELECT nombre FROM personal WHERE servicio_id = 1 AND nombre LIKE 'Lic.%'")
    viejos_s1 = cursor.fetchall()
    if viejos_s1:
        print(f"[ERROR] Se encontraron nombres con formato 'Lic.' en el Servicio 1: {viejos_s1}")
        errors += len(viejos_s1)
    else:
        print("[OK] No se encontraron nombres viejos en personal del Servicio 1.")

    # 2. Verificar que no queden nombres sin comas en el Servicio 3 para personal que debería tenerlos
    cursor.execute("SELECT nombre FROM personal WHERE servicio_id = 3")
    nombres_s3 = [row[0] for row in cursor.fetchall()]
    sin_coma_s3 = [n for n in nombres_s3 if "," not in n]
    # Exceptuamos si hay alguno especial que sea un solo apellido o nombre de fantasía (pero aquí todos son Apellido Nombre)
    if sin_coma_s3:
        print(f"[ERROR] Se encontraron nombres sin coma en el Servicio 3: {sin_coma_s3}")
        errors += len(sin_coma_s3)
    else:
        print("[OK] Todos los nombres del Servicio 3 contienen comas.")

    # 3. Verificar el rol de Pedro Moya
    cursor.execute("SELECT rol FROM personal WHERE nombre = 'Moya, Pedro'")
    row_moya = cursor.fetchone()
    if row_moya:
        rol = row_moya[0]
        if rol == 'Planta':
            print("[OK] Rol de 'Moya, Pedro' corregido con éxito a 'Planta'.")
        else:
            print(f"[ERROR] El rol de 'Moya, Pedro' es '{rol}' (debería ser 'Planta').")
            errors += 1
    else:
        print("[ERROR] No se encontró a 'Moya, Pedro' en la tabla personal.")
        errors += 1

    # 4. Verificar integridad referencial (no registros huérfanos)
    referencias = [
        ("guardias", "nombre"),
        ("personal_reglas_ajustes", "personal_nombre"),
        ("flr_asignados", "nombre"),
        ("personal_puestos", "personal_nombre"),
        ("semanas_categorias", "nombre"),
        ("licencias", "nombre"),
        ("personal_reglas", "personal_nombre"),
    ]

    print("\n--- Verificando Integridad Referencial (Huérfanos) ---")
    for table, col in referencias:
        query = f"""
            SELECT DISTINCT t.{col} 
            FROM {table} t 
            LEFT JOIN personal p ON t.{col} = p.nombre
            WHERE p.nombre IS NULL AND t.{col} IS NOT NULL
        """
        cursor.execute(query)
        orphans = [r[0] for r in cursor.fetchall()]
        if orphans:
            print(f"[ERROR] Tabla '{table}': se encontraron registros huérfanos apuntando a nombres inexistentes: {orphans}")
            errors += len(orphans)
        else:
            print(f"[OK] Tabla '{table}': integridad referencial verificada (0 huérfanos).")

    # 5. Verificar regla ID 62 en servicios_reglas
    cursor.execute("SELECT parametros_json FROM servicios_reglas WHERE id = 62")
    row_regla = cursor.fetchone()
    if row_regla:
        p_json_str = row_regla[0]
        try:
            p_json = json.loads(p_json_str)
            nombres_json = p_json.get("nombres", [])
            print(f"\n[OK] Regla 62 JSON decodificada correctamente: {p_json}")
            for vn in nombres_json:
                if "," not in vn:
                    print(f"[ERROR] El nombre '{vn}' en la regla 62 de servicios_reglas no tiene coma.")
                    errors += 1
        except Exception as e:
            print(f"[ERROR] Regla 62: error decodificando JSON: {e}")
            errors += 1

    print("\n=== AUDITORÍA COMPLETADA ===")
    if errors == 0:
        print("\n>>> [SUCCESS] Todo está normalizado, consistente y referenciado perfectamente.")
    else:
        print(f"\n>>> [FAILED] Se encontraron {errors} errores en la verificación.")

    conn.close()

if __name__ == '__main__':
    verify()

import sqlite3
import json

def scan_db():
    conn = sqlite3.connect("cronograma_inteligente.db")
    conn.row_factory = sqlite3.Row
    
    tables_to_check = [
        ("servicios_reglas", "parametros_json", ["id", "servicio_id", "codigo_regla"]),
        ("personal_reglas", "parametros_json", ["id", "personal_nombre", "codigo_regla"]),
        ("personal_reglas_ajustes", "parametros_json", ["id", "personal_nombre", "codigo_regla"]),
        ("organizaciones_reglas", "parametros_json", ["id", "organizacion_id", "codigo_regla"])
    ]
    
    print("Scanning database for invalid JSON strings...")
    found_invalid = False
    
    for table_name, col_name, keys in tables_to_check:
        try:
            # Check if table exists
            cursor = conn.cursor()
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            if not cursor.fetchone():
                continue
                
            query = f"SELECT {', '.join(keys)}, {col_name} FROM {table_name}"
            rows = conn.execute(query).fetchall()
            for r in rows:
                val = r[col_name]
                if val:
                    try:
                        json.loads(val)
                    except json.JSONDecodeError as e:
                        found_invalid = True
                        key_info = ", ".join(f"{k}: {r[k]}" for k in keys)
                        print(f"\n[INVALID JSON] Table: {table_name} | Row info: ({key_info})")
                        print(f"Value: {val!r}")
                        print(f"Error: {e}")
        except Exception as ex:
            print(f"Error checking table {table_name}: {ex}")
            
    if not found_invalid:
        print("No invalid JSON strings found in the checked tables.")
    conn.close()

if __name__ == '__main__':
    scan_db()

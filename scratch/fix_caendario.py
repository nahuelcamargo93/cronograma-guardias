import sqlite3

try:
    conn = sqlite3.connect("cronograma_inteligente.db", timeout=30.0)
    cursor = conn.cursor()

    # Check how many rows will be affected
    cursor.execute("SELECT COUNT(*) FROM personal_reglas_ajustes WHERE codigo_regla = 'MAX_HORAS_MES_CAENDARIO';")
    count = cursor.fetchone()[0]

    print(f"Encontradas {count} filas con el error ortográfico 'MAX_HORAS_MES_CAENDARIO'.")

    if count > 0:
        cursor.execute("""
            UPDATE personal_reglas_ajustes 
            SET codigo_regla = 'MAX_HORAS_MES_CALENDARIO' 
            WHERE codigo_regla = 'MAX_HORAS_MES_CAENDARIO';
        """)
        conn.commit()
        print("¡Base de datos corregida con éxito!")
    else:
        print("No se encontraron filas para corregir.")

except Exception as e:
    print(f"Error: {e}")
finally:
    if 'conn' in locals():
        conn.close()

import sqlite3

def main():
    db_file = "cronograma_inteligente.db"
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    try:
        # Insertar el ajuste para demanda_config_id = 31
        cursor.execute("""
            INSERT INTO demanda_ajustes (demanda_config_id, fecha_inicio, fecha_fin, cantidad, cantidad_min, cantidad_max, dias_semana, activo)
            VALUES (31, '2026-08-01', '2026-08-02', 8, 8, 12, '5,6', 1)
        """)
        conn.commit()
        print("[OK] Ajuste de demanda insertado con éxito en demanda_ajustes para el puesto 9 (UTI) el 1 y 2 de agosto.")
        
        # Verificar la inserción
        print("\n=== Últimos registros en demanda_ajustes ===")
        rows = cursor.execute("""
            SELECT da.id, da.demanda_config_id, da.fecha_inicio, da.fecha_fin, da.cantidad, da.cantidad_min, da.cantidad_max, da.dias_semana, da.activo
            FROM demanda_ajustes da
            ORDER BY da.id DESC LIMIT 5
        """).fetchall()
        for r in rows:
            print(r)
            
    except Exception as e:
        print(f"Error al ejecutar la inserción: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    main()

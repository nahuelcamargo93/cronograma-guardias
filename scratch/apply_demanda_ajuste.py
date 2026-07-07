import sqlite3

def main():
    db_file = "cronograma_inteligente.db"
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    try:
        # Ejecutar la inserción en demanda_ajustes incluyendo el campo legacy 'cantidad'
        cursor.execute("""
            INSERT INTO demanda_ajustes (demanda_config_id, fecha_inicio, fecha_fin, cantidad, cantidad_min, cantidad_max, dias_semana, activo)
            VALUES (
                (SELECT id FROM demanda_config WHERE puesto_id = 32 AND tipo_dia = 'Finde_Feriado' AND hora_inicio = '00:00' AND hora_fin = '06:00' AND dias_semana = '5,6'),
                '2026-07-06',
                '2026-07-20',
                2,
                2,
                6,
                '5,6',
                1
            )
        """)
        conn.commit()
        print("Ajuste de demanda insertado con éxito en demanda_ajustes.")
        
        # Verificar cómo quedó demanda_ajustes para el puesto 32
        print("\nRegistros en demanda_ajustes para el puesto 32:")
        rows = cursor.execute("""
            SELECT da.id, da.demanda_config_id, da.fecha_inicio, da.fecha_fin, da.cantidad, da.cantidad_min, da.cantidad_max, da.dias_semana, da.activo 
            FROM demanda_ajustes da
            JOIN demanda_config dc ON da.demanda_config_id = dc.id
            WHERE dc.puesto_id = 32
        """).fetchall()
        for r in rows:
            print(r)
            
    except Exception as e:
        print(f"Error al ejecutar la query: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    main()

import sqlite3
import json
import time

print("Intentando abrir la base de datos...")
for i in range(5):
    try:
        conn = sqlite3.connect('cronograma_inteligente.db', timeout=30.0)
        cursor = conn.cursor()
        
        # Datos a insertar
        ajustes = [
            (1, 'MAX_HORAS_MES_CALENDARIO', '2026-06-22', '2026-06-30', 'SUSPENDER', None, 1),
            (1, 'MIN_HORAS_MES_CALENDARIO', '2026-06-22', '2026-06-30', 'SUSPENDER', None, 1),
            (1, 'MAX_HORAS_SEMANA', '2026-06-22', '2026-06-30', 'SOBRESCRIBIR', json.dumps({"limite": 36}), 1)
        ]

        print("--- INSERTANDO AJUSTES EN servicios_reglas_ajustes ---")
        for s_id, cod, fi, ff, acc, params, act in ajustes:
            cursor.execute("""
                DELETE FROM servicios_reglas_ajustes
                WHERE servicio_id = ? AND codigo_regla = ? AND fecha_inicio = ? AND fecha_fin = ?
            """, (s_id, cod, fi, ff))
            
            cursor.execute("""
                INSERT INTO servicios_reglas_ajustes (servicio_id, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (s_id, cod, fi, ff, acc, params, act))
            print(f"Insertado ajuste para {cod}: Acción {acc}, Rango {fi} a {ff}")

        conn.commit()

        print("\n--- AJUSTES ACTUALES EN LA DB ---")
        rows = cursor.execute("SELECT * FROM servicios_reglas_ajustes WHERE servicio_id = 1").fetchall()
        for r in rows:
            print(r)

        conn.close()
        print("Operación completada con éxito.")
        break
    except sqlite3.OperationalError as e:
        if "locked" in str(e):
            print(f"Intento {i+1} fallido por base de datos bloqueada. Reintentando...")
            time.sleep(2)
        else:
            raise e

import sqlite3
import json

db_path = r"c:\Users\asus\Desktop\Ryoko\cronograma_inteligente\cronograma_inteligente.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Insertar el ajuste temporal para bajar las horas mínimas de Melisa Coniglio en Junio
    cursor.execute("""
        INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo, servicio_id)
        VALUES ('Coniglio, Melisa', 'MIN_HORAS_MES_CALENDARIO', '2026-06-22', '2026-06-30', 'SOBRESCRIBIR', ?, 1, 1)
    """, (json.dumps({"min_horas": 120}),))
    
    conn.commit()
    print("Ajuste temporal de MIN_HORAS_MES_CALENDARIO para Melisa Coniglio insertado con éxito en la DB.")
except Exception as e:
    conn.rollback()
    print(f"Error al insertar el ajuste temporal: {e}")
finally:
    conn.close()

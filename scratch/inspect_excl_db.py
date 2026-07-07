import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')

print("=== ALL EXCLUIR_TURNOS IN DB ===")
for tbl in ['personal_reglas', 'roles_reglas', 'servicios_reglas', 'personal_reglas_ajustes']:
    print(f"\n--- Table: {tbl} ---")
    if tbl == 'personal_reglas':
        query = "SELECT personal_nombre, parametros_json, activo FROM personal_reglas WHERE codigo_regla = 'EXCLUIR_TURNOS'"
    elif tbl == 'roles_reglas':
        query = "SELECT rol, parametros_json, activo FROM roles_reglas WHERE codigo_regla = 'EXCLUIR_TURNOS' AND servicio_id = 1"
    elif tbl == 'servicios_reglas':
        query = "SELECT servicio_id, parametros_json, activo FROM servicios_reglas WHERE codigo_regla = 'EXCLUIR_TURNOS'"
    elif tbl == 'personal_reglas_ajustes':
        query = "SELECT personal_nombre, fecha_inicio, fecha_fin, accion, parametros_json, activo FROM personal_reglas_ajustes WHERE codigo_regla = 'EXCLUIR_TURNOS'"
    
    for r in conn.execute(query):
        print(r[0], r[1:] if len(r) > 1 else "")

conn.close()

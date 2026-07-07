import sqlite3
import json

def main():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cur = conn.cursor()
    
    print('=== REGLAS DEL SERVICIO 2 ===')
    cur.execute("SELECT codigo_regla, parametros_json, activo FROM servicios_reglas WHERE servicio_id = 2 AND codigo_regla = 'EXCLUIR_TURNOS'")
    for row in cur.fetchall():
        print(f"Regla: {row[0]}, Activo: {row[2]}, Params: {row[1]}")
        
    print('\n=== REGLAS PERSONALES DE POLETTI NATALIA ===')
    cur.execute("SELECT codigo_regla, parametros_json, activo FROM personal_reglas WHERE personal_nombre = 'POLETTI NATALIA'")
    for row in cur.fetchall():
        print(f"Regla: {row[0]}, Activo: {row[2]}, Params: {row[1]}")
        
    print('\n=== AJUSTES TEMPORALES PARA AGOSTO 2026 ===')
    cur.execute("SELECT personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo FROM personal_reglas_ajustes WHERE fecha_inicio >= '2026-08-01' AND codigo_regla = 'EXCLUIR_TURNOS'")
    for row in cur.fetchall():
        print(f"Nombre: {row[0]}, Rango: {row[2]} a {row[3]}, Accion: {row[4]}, Activo: {row[6]}, Params:\n{row[5]}\n")
        
    conn.close()

if __name__ == '__main__':
    main()

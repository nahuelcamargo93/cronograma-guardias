import sqlite3

def main():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    rows = cursor.execute("""
        SELECT dc.tipo_dia, p.nombre as puesto, dc.hora_inicio, dc.hora_fin, dc.cantidad_min, dc.cantidad_max, dc.dias_semana
        FROM demanda_config dc
        JOIN puestos p ON dc.puesto_id = p.id
        WHERE p.servicio_id = 2 AND dc.activo = 1
    """).fetchall()
    
    print("=== DEMANDAS SERVICIO 2 ===")
    for r in rows:
        print(f"Tipo Dia: {r[0]}, Puesto: {r[1]}, Hora: {r[2]}-{r[3]}, Min: {r[4]}, Max: {r[5]}, Dias: {r[6]}")
        
    print("\n=== TURNOS SERVICIO 2 ===")
    t_rows = cursor.execute("""
        SELECT tc.nombre, tc.hora_inicio, tc.horas, tc.dias_semana, p.nombre
        FROM turnos_config tc
        JOIN puestos p ON tc.puesto_id = p.id
        WHERE tc.servicio_id = 2 AND tc.activo = 1
    """).fetchall()
    for r in t_rows:
        print(f"Turno: {r[0]}, Hora: {r[1]}, Horas: {r[2]}, Dias: {r[3]}, Puesto: {r[4]}")
        
    conn.close()

if __name__ == '__main__':
    main()

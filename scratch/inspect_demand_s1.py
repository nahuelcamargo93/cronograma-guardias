import sqlite3

def inspect_demand():
    conn = sqlite3.connect("cronograma_inteligente.db")
    conn.row_factory = sqlite3.Row
    
    print("=== DEMAND CONFIG (Servicio 1) ===")
    demands = conn.execute("""
        SELECT dc.*, p.nombre as puesto_nombre
        FROM demanda_config dc
        JOIN puestos p ON dc.puesto_id = p.id
        WHERE p.servicio_id = 1
    """).fetchall()
    
    for d in demands:
        print(f"ID: {d['id']} | Puesto: {d['puesto_nombre']} | Dia: {d['tipo_dia']} | Hora: {d['hora_inicio']}-{d['hora_fin']} | Min: {d['cantidad_min']} | Max: {d['cantidad_max']} | Dias: {d['dias_semana']} | Activo: {d['activo']}")
        
    print("\n=== DEMAND ADJUSTMENTS (Servicio 1) ===")
    adjustments = conn.execute("""
        SELECT da.*, dc.tipo_dia, dc.hora_inicio, dc.hora_fin, p.nombre as puesto_nombre
        FROM demanda_ajustes da
        JOIN demanda_config dc ON da.demanda_config_id = dc.id
        JOIN puestos p ON dc.puesto_id = p.id
        WHERE p.servicio_id = 1
    """).fetchall()
    
    for a in adjustments:
        print(f"ID: {a['id']} | Config ID: {a['demanda_config_id']} | Puesto: {a['puesto_nombre']} | Dia: {a['tipo_dia']} | Hora: {a['hora_inicio']}-{a['hora_fin']} | Valido: {a['fecha_inicio']} a {a['fecha_fin']} | Min: {a['cantidad_min']} | Max: {a['cantidad_max']} | Dias: {a['dias_semana']} | Activo: {a['activo']}")
        
    conn.close()

if __name__ == '__main__':
    inspect_demand()

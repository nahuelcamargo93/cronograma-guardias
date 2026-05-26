import sqlite3

def run():
    conn = sqlite3.connect("cronograma_inteligente.db")
    conn.row_factory = sqlite3.Row
    
    print("=== PUESTOS ===")
    rows = conn.execute("SELECT id, nombre, servicio_id FROM puestos WHERE servicio_id = 2").fetchall()
    puesto_ids = []
    for r in rows:
        print(f"  Puesto ID: {r['id']} | Nombre: {r['nombre']} | Servicio ID: {r['servicio_id']}")
        puesto_ids.append(r['id'])
        
    print("\n=== DEMANDA CONFIG ===")
    if puesto_ids:
        placeholders = ','.join('?' for _ in puesto_ids)
        d_rows = conn.execute(f"""
            SELECT dc.id, dc.puesto_id, dc.tipo_dia, dc.hora_inicio, dc.hora_fin, dc.cantidad_min, dc.cantidad_max
            FROM demanda_config dc
            WHERE dc.puesto_id IN ({placeholders})
        """, tuple(puesto_ids)).fetchall()
        for r in d_rows:
            print(f"  ID: {r['id']} | Puesto ID: {r['puesto_id']} | Tipo Dia: {r['tipo_dia']} | Hora Ini: {r['hora_inicio']} | Hora Fin: {r['hora_fin']} | Min: {r['cantidad_min']} | Max: {r['cantidad_max']}")

    print("\n=== TURNOS CONFIG ===")
    t_rows = conn.execute("SELECT id, nombre, horas, hora_inicio, puesto_id, servicio_id FROM turnos_config WHERE servicio_id = 2").fetchall()
    for r in t_rows:
        print(f"  ID: {r['id']} | Nombre: {r['nombre']} | Horas: {r['horas']} | Hora Ini: {r['hora_inicio']} | Puesto ID: {r['puesto_id']}")
        
    conn.close()

if __name__ == '__main__':
    run()


if __name__ == '__main__':
    run()


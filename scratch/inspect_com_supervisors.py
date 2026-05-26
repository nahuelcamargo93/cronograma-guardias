import sqlite3
import json

def inspect():
    conn = sqlite3.connect("cronograma_inteligente.db")
    conn.row_factory = sqlite3.Row
    
    print("=== SUPERVISORES EN COM (Servicio 4) ===")
    supervisores = conn.execute("""
        SELECT nombre, rol, categoria, activo
        FROM personal
        WHERE servicio_id = 4 AND (rol LIKE '%Supervisor%' OR categoria = 'A')
    """).fetchall()
    
    for s in supervisores:
        print(f"Nombre: {s['nombre']} | Rol: {s['rol']} | Categoria: {s['categoria']}")
        
    print("\n=== REGLAS ACTIVAS PARA ESTOS SUPERVISORES ===")
    nombres_sups = [s['nombre'] for s in supervisores]
    for nombre in nombres_sups:
        rules = conn.execute("""
            SELECT pr.codigo_regla, pr.parametros_json, pr.activo
            FROM personal_reglas pr
            WHERE pr.personal_nombre = ?
        """, (nombre,)).fetchall()
        print(f"\nEmpleado: {nombre}")
        for r in rules:
            print(f"  Regla: {r['codigo_regla']} | Params: {r['parametros_json']} | Activo: {r['activo']}")
            
        # Check adjustments too
        adjustments = conn.execute("""
            SELECT pra.codigo_regla, pra.fecha_inicio, pra.fecha_fin, pra.accion, pra.parametros_json, pra.activo
            FROM personal_reglas_ajustes pra
            WHERE pra.personal_nombre = ?
        """, (nombre,)).fetchall()
        if adjustments:
            print(f"  Ajustes (personal_reglas_ajustes):")
            for a in adjustments:
                print(f"    Regla: {a['codigo_regla']} | Accion: {a['accion']} | Params: {a['parametros_json']} | Rango: {a['fecha_inicio']} a {a['fecha_fin']} | Activo: {a['activo']}")
                
    print("\n=== DEMANDA CONFIG DE SUPERVISORES ===")
    # Find puesto_id for 'Supervisor' or similar
    puestos = conn.execute("SELECT id, nombre FROM puestos WHERE servicio_id = 4").fetchall()
    print("Puestos in COM:")
    for p in puestos:
        print(f"  ID: {p['id']} | Nombre: {p['nombre']}")
        
    puesto_ids = [p['id'] for p in puestos if 'Supervisor' in p['nombre']]
    if puesto_ids:
        placeholders = ",".join("?" for _ in puesto_ids)
        demands = conn.execute(f"""
            SELECT dc.*, p.nombre as puesto_nombre
            FROM demanda_config dc
            JOIN puestos p ON dc.puesto_id = p.id
            WHERE dc.puesto_id IN ({placeholders}) AND dc.tipo_dia = 'Finde_Feriado'
        """, puesto_ids).fetchall()
        for d in demands:
            print(f"  Puesto: {d['puesto_nombre']} | Dia: {d['tipo_dia']} | Hora: {d['hora_inicio']}-{d['hora_fin']} | Min: {d['cantidad_min']} | Max: {d['cantidad_max']} | Dias: {d['dias_semana']}")
            
    print("\n=== LICENCIAS DE SUPERVISORES ===")
    for nombre in nombres_sups:
        lics = conn.execute("SELECT * FROM licencias WHERE nombre = ?", (nombre,)).fetchall()
        for l in lics:
            print(f"  Nombre: {nombre} | Tipo: {l['tipo']} | Rango: {l['fecha_inicio']} a {l['fecha_fin']}")
            
    conn.close()

if __name__ == '__main__':
    inspect()

import sqlite3
import json

def inspect():
    conn = sqlite3.connect("cronograma_inteligente.db")
    conn.row_factory = sqlite3.Row
    
    print("=== PUESTOS (Servicio 1) ===")
    puestos = conn.execute("SELECT * FROM puestos WHERE servicio_id = 1").fetchall()
    for p in puestos:
        print(dict(p))
        
    print("\n=== TURNOS CONFIG (Servicio 1) ===")
    turnos = conn.execute("SELECT * FROM turnos_config WHERE servicio_id = 1").fetchall()
    for t in turnos:
        print(dict(t))
        
    print("\n=== PERSONAL (Servicio 1) ===")
    personal = conn.execute("SELECT * FROM personal WHERE servicio_id = 1").fetchall()
    for p in personal:
        print(f"Nombre: {p['nombre']} | Rol: {p['rol']} | Categoria: {p['categoria']} | Activo: {p['activo']}")
        
    print("\n=== PERSONAL PUESTOS MAPPINGS ===")
    mappings = conn.execute("""
        SELECT pp.personal_nombre, p.nombre as puesto_nombre, p.id as puesto_id
        FROM personal_puestos pp
        JOIN puestos p ON pp.puesto_id = p.id
        WHERE p.servicio_id = 1
    """).fetchall()
    for m in mappings:
        print(dict(m))
        
    print("\n=== PERSONAL REGLAS ===")
    personal_rules = conn.execute("""
        SELECT pr.personal_nombre, rc.codigo_regla, pr.parametros_json
        FROM personal_reglas pr
        JOIN reglas_catalogo rc ON pr.codigo_regla = rc.codigo_regla
        JOIN personal p ON pr.personal_nombre = p.nombre
        WHERE p.servicio_id = 1
    """).fetchall()
    for pr in personal_rules:
        print(f"Nombre: {pr['personal_nombre']} | Regla: {pr['codigo_regla']} | Params: {pr['parametros_json']}")
        
    conn.close()

if __name__ == '__main__':
    inspect()

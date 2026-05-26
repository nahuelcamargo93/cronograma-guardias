import sqlite3

def main():
    conn = sqlite3.connect('cronograma_inteligente.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("=== PERSONAL SERVICIO 3 ===")
    rows = cursor.execute("SELECT nombre, rol, categoria, activo, servicio_id FROM personal WHERE servicio_id = 3").fetchall()
    for r in rows:
        puestos = cursor.execute("""
            SELECT p.nombre, pp.es_primario 
            FROM personal_puestos pp 
            JOIN puestos p ON pp.puesto_id = p.id 
            WHERE pp.personal_nombre = ?
        """, (r['nombre'],)).fetchall()
        puestos_str = ", ".join([f"{p[0]} (primario={p[1]})" for p in puestos])
        print(f"Nombre: {r['nombre']} | Rol: {r['rol']} | Categoria: {r['categoria']} | Puestos: [{puestos_str}]")
        
    print("\n=== PUESTOS SERVICIO 3 ===")
    rows = cursor.execute("SELECT id, nombre, servicio_id FROM puestos WHERE servicio_id = 3").fetchall()
    for r in rows:
        print(f"ID: {r['id']} | Nombre: {r['nombre']}")
        
    print("\n=== CONFIGURACION REGLAS SERVICIO 3 ===")
    rows = cursor.execute("SELECT codigo_regla, parametros_json FROM servicios_reglas WHERE servicio_id = 3 AND activo = 1").fetchall()
    for r in rows:
        print(f"Regla: {r['codigo_regla']} | Parametros: {r['parametros_json']}")
        
    conn.close()

if __name__ == '__main__':
    main()

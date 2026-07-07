import sqlite3

conn = sqlite3.connect("cronograma_inteligente.db")
cursor = conn.cursor()

print("--- EMPLEADOS Y PUESTOS DEL SERVICIO 1 ---")
res = cursor.execute("""
    SELECT p.nombre, p.rol, p.categoria, 
           (SELECT group_concat(pst.nombre) 
            FROM personal_puestos pp 
            JOIN puestos pst ON pp.puesto_id = pst.id 
            WHERE pp.personal_nombre = p.nombre) as puestos
    FROM personal p 
    WHERE p.servicio_id = 1 AND COALESCE(p.activo, 1) = 1
""").fetchall()

for r in res:
    print(f"Nombre: {r[0]} | Rol: {r[1]} | Categoria: {r[2]} | Puestos: {r[3]}")

conn.close()

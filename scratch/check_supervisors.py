import sys; sys.path.insert(0,'.')
from database.connection import get_connection
conn = get_connection()

# Who is in categories C and D for service 4, and what role?
rows = conn.execute("""
    SELECT nombre, categoria, rol FROM personal 
    WHERE servicio_id = 4 AND COALESCE(activo, 1) = 1
    ORDER BY categoria, rol, nombre
""").fetchall()

print('=== PERSONAL SERVICIO 4 (categoria, rol) ===')
for nombre, cat, rol in rows:
    print(f"  {nombre}: cat={cat}, rol={rol}")

print()
print('=== SUPERVISORES EN CATEGORIAS C y D ===')
for nombre, cat, rol in rows:
    if cat in ('C', 'D') and 'Supervisor' in (rol or ''):
        print(f"  {nombre}: cat={cat}, rol={rol}")

conn.close()

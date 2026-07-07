import sqlite3
conn = sqlite3.connect('cronograma_inteligente.db')
print("=== TOLEDO, ANDREA FRANCOS FORZADOS ===")
for r in conn.execute("SELECT personal_nombre, fecha_inicio, fecha_fin, activo FROM personal_francos_forzados WHERE personal_nombre = 'Toledo, Andrea'").fetchall():
    print(r)

print("\n=== GARCIA, LUCIANO FRANCOS FORZADOS ===")
for r in conn.execute("SELECT personal_nombre, fecha_inicio, fecha_fin, activo FROM personal_francos_forzados WHERE personal_nombre = 'Garcia, Luciano'").fetchall():
    print(r)

import sqlite3
conn = sqlite3.connect('cronograma_inteligente.db')
print("=== TOLEDO, ANDREA REGLAS AJUSTES ===")
for r in conn.execute("SELECT personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, activo FROM personal_reglas_ajustes WHERE personal_nombre = 'Toledo, Andrea'").fetchall():
    print(r)

print("\n=== GARCIA, LUCIANO REGLAS AJUSTES ===")
for r in conn.execute("SELECT personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, activo FROM personal_reglas_ajustes WHERE personal_nombre = 'Garcia, Luciano'").fetchall():
    print(r)

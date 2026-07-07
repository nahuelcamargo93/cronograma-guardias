import sqlite3
conn = sqlite3.connect('cronograma_inteligente.db')

# Reglas de Juarez
print("=== JUAREZ, EDUARDO ===")
for r in conn.execute("SELECT codigo_regla, parametros_json FROM personal_reglas WHERE personal_nombre = 'Juarez, Eduardo' AND activo = 1").fetchall():
    print(r)

# Verificar quiénes tienen rol 'Rotativo' actualmente
print("\n=== PERSONAL CON ROL 'Rotativo' ===")
for r in conn.execute("SELECT nombre, rol FROM personal WHERE servicio_id = 1 AND rol = 'Rotativo' AND COALESCE(activo, 1) = 1").fetchall():
    print(r)

# Verificar quiénes tienen rol 'Nocturno'
print("\n=== PERSONAL CON ROL 'Nocturno' ===")
for r in conn.execute("SELECT nombre, rol FROM personal WHERE servicio_id = 1 AND rol = 'Nocturno' AND COALESCE(activo, 1) = 1").fetchall():
    print(r)

# Reglas individuales de los rotativos (para saber qué tienen cargado)
print("\n=== REGLAS INDIVIDUALES DE ROTATIVOS ===")
rotativos = [r[0] for r in conn.execute("SELECT nombre FROM personal WHERE servicio_id = 1 AND rol = 'Rotativo' AND COALESCE(activo, 1) = 1").fetchall()]
for nombre in rotativos:
    reglas = conn.execute("SELECT codigo_regla, parametros_json FROM personal_reglas WHERE personal_nombre = ? AND activo = 1", (nombre,)).fetchall()
    if reglas:
        print(f"\n  {nombre}:")
        for r in reglas:
            print(f"    {r}")
    else:
        print(f"  {nombre}: (sin reglas individuales)")

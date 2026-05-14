import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')

# Obtener IDs de las reglas obsoletas
ids = [r[0] for r in conn.execute(
    "SELECT id FROM reglas_catalogo WHERE codigo_regla IN ('MAX_NOCHES', 'NO_NOCHES')"
).fetchall()]

if ids:
    placeholders = ','.join('?' * len(ids))
    d1 = conn.execute(f"DELETE FROM personal_reglas WHERE regla_id IN ({placeholders})", ids).rowcount
    d2 = conn.execute(f"DELETE FROM servicios_reglas WHERE regla_id IN ({placeholders})", ids).rowcount
    d3 = conn.execute(f"DELETE FROM organizaciones_reglas WHERE regla_id IN ({placeholders})", ids).rowcount
    d4 = conn.execute(f"DELETE FROM reglas_catalogo WHERE id IN ({placeholders})", ids).rowcount
    conn.commit()
    print(f"Limpieza completada:")
    print(f"  personal_reglas eliminados:      {d1}")
    print(f"  servicios_reglas eliminados:     {d2}")
    print(f"  organizaciones_reglas eliminados:{d3}")
    print(f"  catalogo eliminados:             {d4}")
else:
    print("No se encontraron MAX_NOCHES ni NO_NOCHES en el catálogo.")

conn.close()

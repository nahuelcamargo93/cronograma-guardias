import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')

conn.execute("""
    INSERT OR IGNORE INTO reglas_catalogo (codigo_regla, tipo, descripcion)
    VALUES (
        'UN_TURNO_POR_DIA',
        'HARD',
        'Restriccion universal: una persona no puede tener mas de un turno asignado el mismo dia. No tiene parametros configurables.'
    )
""")
conn.commit()

row = conn.execute("SELECT codigo_regla, tipo, descripcion FROM reglas_catalogo WHERE codigo_regla = 'UN_TURNO_POR_DIA'").fetchone()
print("Registrado:", row)
conn.close()

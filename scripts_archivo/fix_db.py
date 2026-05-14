import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')

# 1. Corregir fecha fin de Toledo LPP: 2026-06-02 -> 2026-06-01
result = conn.execute("""
    UPDATE licencias SET fecha_fin = '2026-06-01'
    WHERE nombre = 'Lic. Toledo' AND tipo = 'LPP' AND fecha_fin = '2026-06-02'
""")
print(f"Toledo corregido: {result.rowcount} fila(s) actualizadas")

# 2. Eliminar Test User de todas las tablas relacionadas
result = conn.execute("DELETE FROM personal WHERE nombre = 'Test User'")
print(f"Test User eliminado: {result.rowcount} fila(s) de personal")

conn.commit()

# Verificar
row = conn.execute("SELECT nombre, tipo, fecha_inicio, fecha_fin FROM licencias WHERE nombre = 'Lic. Toledo' AND tipo = 'LPP'").fetchone()
print(f"\nToledo LPP: {row}")

print(f"Personal restante: {conn.execute('SELECT COUNT(*) FROM personal').fetchone()[0]} personas")
conn.close()

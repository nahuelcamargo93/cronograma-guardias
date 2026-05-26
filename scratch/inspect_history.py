import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

names = ["BASCUR ALEJANDRA", "CASTRO LUCIANO", "GUIAZU KARINA", "VERA JULIETA", "ECHENIQUE ROCIO", "MIRANDA LUCIANA"]
for name in names:
    print(f"=== {name} ===")
    cursor.execute("""
        SELECT fecha, turno, horas 
        FROM guardias 
        WHERE nombre = ? AND fecha >= '2026-06-20' AND fecha < '2026-07-01'
    """, (name,))
    print("History from 2026-06-20 to 2026-07-01:", cursor.fetchall())

conn.close()

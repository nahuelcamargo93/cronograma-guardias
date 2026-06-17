import sqlite3
from datetime import date, timedelta

db_path = "cronograma_inteligente.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get latest cronograma id
cursor.execute("SELECT max(id) FROM cronogramas")
crono_id = cursor.fetchone()[0]

print("=== ORTIZ LAURA MONTHLY ASSIGNMENTS ===")
cursor.execute("""
    SELECT fecha, turno 
    FROM guardias 
    WHERE nombre = 'ORTIZ LAURA' AND cronograma_id = ?
    ORDER BY fecha
""", (crono_id,))
for row in cursor.fetchall():
    print(row)
    
conn.close()

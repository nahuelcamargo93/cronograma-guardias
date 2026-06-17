import sqlite3

db_path = 'cronograma_inteligente.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get the latest cronograma ID from infracciones_debug
crono_id_row = cursor.execute("SELECT MAX(cronograma_id) FROM infracciones_debug").fetchone()
if not crono_id_row or not crono_id_row[0]:
    print("No infractions found in database.")
    conn.close()
    exit()

crono_id = crono_id_row[0]
print(f"--- INFRACCIONES DETECTADAS PARA CRONOGRAMA ID {crono_id} ---")

# Group by codigo_regla
summary = cursor.execute("""
    SELECT codigo_regla, COUNT(*) 
    FROM infracciones_debug 
    WHERE cronograma_id = ? 
    GROUP BY codigo_regla
    ORDER BY COUNT(*) DESC
""", (crono_id,)).fetchall()

print("\nResumen por regla:")
for rule, count in summary:
    print(f"- {rule}: {count} infracciones")

print("\nDetalle de infracciones (muestreo):")
for rule, count in summary:
    print(f"\n--- {rule} ---")
    examples = cursor.execute("""
        SELECT detalle 
        FROM infracciones_debug 
        WHERE cronograma_id = ? AND codigo_regla = ?
        LIMIT 10
    """, (crono_id, rule)).fetchall()
    for ex in examples:
        print(f"  * {ex[0]}")

conn.close()

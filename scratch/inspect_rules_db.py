import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

# Get the rule catalog ID
cursor.execute("SELECT id, codigo_regla FROM reglas_catalogo WHERE codigo_regla = 'PESO_MIX_HORARIO'")
rule = cursor.fetchone()
print("Rule Catalog entry:", rule)

if rule:
    rule_id = rule[0]
    cursor.execute("""
        SELECT sr.id, sr.servicio_id, sr.parametros_json 
        FROM servicios_reglas sr
        WHERE sr.regla_id = ?
    """, (rule_id,))
    rows = cursor.fetchall()
    print("\nservicios_reglas entries:")
    for r in rows:
        print(f"ID: {r[0]}, Servicio ID: {r[1]}, JSON: {r[2]}")
        
conn.close()

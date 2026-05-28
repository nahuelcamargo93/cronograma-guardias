import sqlite3, json

con = sqlite3.connect('cronograma_inteligente.db')
cur = con.cursor()

print("=== CHANGING EXACTO_FINDE_Y_DIA TO SOFT ===")
cur.execute("SELECT parametros_json FROM servicios_reglas WHERE servicio_id=3 AND codigo_regla='EXACTO_FINDE_Y_DIA'")
row = cur.fetchone()
if row:
    params = json.loads(row[0])
    params['modo'] = 'SOFT'
    new_json = json.dumps(params)
    cur.execute(
        "UPDATE servicios_reglas SET parametros_json=? WHERE servicio_id=3 AND codigo_regla='EXACTO_FINDE_Y_DIA'",
        (new_json,)
    )
    print(f"Updated: {new_json}")
else:
    print("Rule EXACTO_FINDE_Y_DIA not found for service 3")

con.commit()
con.close()

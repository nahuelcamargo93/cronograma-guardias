import sqlite3
conn = sqlite3.connect('cronograma_inteligente.db')
print("=== personal_puestos ===")
for r in conn.execute("SELECT pp.personal_nombre, p.nombre, pp.es_primario FROM personal_puestos pp JOIN puestos p ON pp.puesto_id = p.id WHERE pp.personal_nombre IN ('Camargo, Nahuel', 'Coniglio, Melisa', 'Giacoppo, Veronica')"):
    print(r)
conn.close()

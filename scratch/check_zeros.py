import sqlite3

conn = sqlite3.connect("cronograma_inteligente.db")
names = ["Franco, Leandro", "Garcia, Luciano", "Moyano, Fernando", "Toledo, Andrea"]

for name in names:
    print(f"\n=== {name} ===")
    p = conn.execute("SELECT * FROM personal WHERE nombre = ?", (name,)).fetchone()
    print("Personal details:", p)
    
    puestos = conn.execute(
        "SELECT p.nombre FROM personal_puestos pp JOIN puestos p ON pp.puesto_id = p.id WHERE pp.personal_nombre = ?",
        (name,),
    ).fetchall()
    print("Puestos:", [pt[0] for pt in puestos])
    
    lics = conn.execute(
        "SELECT * FROM licencias WHERE nombre = ? AND fecha_inicio <= '2026-07-31' AND fecha_fin >= '2026-06-22'",
        (name,),
    ).fetchall()
    print("Licencias:", lics)
    
    rules = conn.execute("SELECT * FROM personal_reglas WHERE personal_nombre = ?", (name,)).fetchall()
    print("Reglas:", rules)

conn.close()

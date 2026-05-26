import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import sqlite3
import exportar_pdf

conn = sqlite3.connect('cronograma_inteligente.db')
db_name = conn.execute("SELECT DISTINCT nombre FROM guardias WHERE nombre LIKE '%Florencia%'").fetchone()[0]
print("DB Name:", repr(db_name))

for key in exportar_pdf.MAPEO_NOMBRES.keys():
    if "Florencia" in key:
        print(f"Key in MAPEO_NOMBRES: {repr(key)}")
        print(f"Equal? {db_name == key}")
        print(f"simplificar_nombre(db_name): {repr(exportar_pdf.simplificar_nombre(db_name))}")
conn.close()

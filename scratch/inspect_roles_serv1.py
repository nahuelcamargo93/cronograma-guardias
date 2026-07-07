import sys, os
sys.path.append(os.getcwd())
import database.queries as q
import pandas as pd

df = pd.DataFrame(q.obtener_personal_db(1))
for _, r in df.iterrows():
    print(f"Nombre: {r['Nombre']}, Rol: {r['Rol']}")

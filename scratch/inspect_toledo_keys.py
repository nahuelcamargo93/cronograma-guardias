import sys, os
sys.path.append(os.getcwd())

from database.data_loader import obtener_empleados
from main import ContextoModelo
import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
# Obtener una instancia del contexto para inspeccionar
import pandas as pd
import database.queries as q
df = pd.DataFrame(q.obtener_personal_db(1))
df = q.cargar_datos_personales_bd(df)
historial = q.cargar_historial(df, "2026-08-01")
reglas_db = q.cargar_reglas_personal(1)
reglas_rol_db = q.cargar_reglas_rol(1)

# load turnos
from database.data_loader import obtener_turnos, obtener_demandas
turnos_dict = obtener_turnos(1)
demandas = obtener_demandas(1, "2026-08-01", 31)

# Simular construcción de variables en main.py
class MockCtx:
    def __init__(self):
        self.empleados = obtener_empleados(1, "2026-08-01", 31)
        self.dias = 31
        self.offset_dia = 6 # 2026-08-01 is Saturday (5 or 6 depending on 0-based)
        # Actually 2026-08-01: Saturday is 5 (Monday=0). Let's check:
        # date(2026, 8, 1).weekday() is 5.
        self.offset_dia = 5
        self.feriados = set()
        self.demanda_turnos = {"Semana": {"Mañana_UTI": 1, "Mañana_UCO": 1, "Tarde_UTI": 1, "Tarde_UCO": 1, "Noche": 1}, "Finde_Feriado": {"Dia_UTI": 1, "Dia_UCO": 1, "Noche": 1}}
        
        self.turnos = {}
        for emp in self.empleados:
            for d in range(self.dias):
                dia_semana = (d + self.offset_dia) % 7
                td = "Finde_Feriado" if (dia_semana >= 5) else "Semana"
                for t in self.demanda_turnos[td].keys():
                    self.turnos[(emp.nombre, d, t)] = f"VAR_{emp.nombre}_d{d}_{t}"

ctx = MockCtx()
emp_toledo = next(e for e in ctx.empleados if e.nombre == 'Toledo, Andrea')
print("Toledo turnos keys for d=10:")
for k in ctx.turnos.keys():
    if k[0] == 'Toledo, Andrea' and k[1] == 10:
        print(k)

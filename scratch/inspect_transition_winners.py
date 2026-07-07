import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
import pandas as pd
from datetime import date, timedelta
from restricciones.hard._utils import determinar_familia_ganadora

conn = sqlite3.connect('cronograma_inteligente.db')

# Cargar empleados del servicio 2
servicio_id = 2
fecha_inicio_str = "2026-08-01"
fecha_inicio_dt = date.fromisoformat(fecha_inicio_str)
primer_lunes_dt = fecha_inicio_dt - timedelta(days=fecha_inicio_dt.weekday()) # 27 de julio

# Cargar personal activo
personal = pd.read_sql_query("""
    SELECT nombre, rol FROM personal 
    WHERE servicio_id = 2 AND COALESCE(activo, 1) = 1
""", conn)

# Cargar licencias
licencias = pd.read_sql_query("""
    SELECT nombre, tipo, fecha_inicio, fecha_fin 
    FROM licencias 
    WHERE fecha_inicio <= '2026-08-02' AND fecha_fin >= '2026-08-01'
""", conn)
lic_nombres = set(licencias['nombre'])

# Cargar guardias previas de julio
guardias_julio = pd.read_sql_query("""
    SELECT g.nombre, g.fecha, g.turno
    FROM guardias g
    JOIN cronogramas c ON g.cronograma_id = c.id
    WHERE c.id = 583
""", conn)

# Organizar guardias por enfermero
guardias_by_emp = {}
for _, r in guardias_julio.iterrows():
    guardias_by_emp.setdefault(r['nombre'], []).append({
        'fecha': r['fecha'],
        'turno': r['turno']
    })

print(f"Total personal activo en Servicio 2: {len(personal)}")
print(f"Personal de licencia el 1 y 2 de agosto: {len(lic_nombres)}")

rows = []
for _, p in personal.iterrows():
    nombre = p['nombre']
    rol = p['rol']
    
    # Licencia el 1 o 2 de agosto
    de_licencia = nombre in lic_nombres
    
    # Ganador histórico en la semana del 27 de julio al 2 de agosto
    hist_prev = guardias_by_emp.get(nombre, [])
    ganador = determinar_familia_ganadora(hist_prev, primer_lunes_dt)
    
    rows.append({
        'Nombre': nombre,
        'Rol': rol,
        'Licencia': 'SI' if de_licencia else 'NO',
        'Ganador_Julio': ganador if ganador else 'Ninguno'
    })

df_res = pd.DataFrame(rows)
print("\n=== RESUMEN POR EMPLEADO (SEMANA DE TRANSICIÓN) ===")
print(df_res.to_string())

print("\n=== DISTRIBUCION DE GANADORES PARA PERSONAL DISPONIBLE (SIN LICENCIA) ===")
disp_df = df_res[df_res['Licencia'] == 'NO']
print(disp_df['Ganador_Julio'].value_counts())

conn.close()

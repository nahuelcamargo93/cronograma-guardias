import os
import sqlite3
import pandas as pd
from datetime import date, timedelta
import sys

# Asegurar path de imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database import queries as db_queries
from database import schema as db_schema
from database.data_loader import obtener_empleados, obtener_turnos

def analizar_horas_transicion():
    db_schema.inicializar_db()
    
    fecha_inicio = "2026-08-01"
    fecha_fin = "2026-08-31"
    
    fecha_inicio_dt = date.fromisoformat(fecha_inicio)
    
    # Semana 31 de 2026 va desde el lunes 27 de Julio hasta el domingo 2 de Agosto
    lunes_sem31 = date(2026, 7, 27)
    
    # Cargar empleados activos
    empleados = obtener_empleados(2, fecha_inicio, 31)
    
    # Cargar historial de guardias previas (Julio)
    historial = db_queries.cargar_guardias_previas(fecha_inicio, dias_atras=28, servicio_id=2)
    
    print("=== ANÁLISIS DE HORAS TRABAJADAS EN JULIO (SEMANA 31: 27-JUL A 31-JUL) ===")
    
    disponibles_sabado_domingo = 0
    listado_empleados = []
    
    for emp in empleados:
        nombre = emp.nombre
        if "POLETTI" in nombre:
            # Natalia Poletti no trabaja fin de semana
            continue
            
        hist_emp = historial.get(nombre, [])
        
        # Filtrar guardias del lunes 27 de Julio al viernes 31 de Julio
        guardias_julio_sem31 = [
            g for g in hist_emp
            if "2026-07-27" <= g['fecha'] <= "2026-07-31"
        ]
        
        horas_trabajadas_julio = sum(g['horas'] for g in guardias_julio_sem31)
        horas_disponibles = 36 - horas_trabajadas_julio
        
        puede_trabajar = horas_disponibles >= 6
        if puede_trabajar:
            disponibles_sabado_domingo += 1
            
        listado_empleados.append({
            "Nombre": nombre,
            "Horas Julio (Semana 31)": horas_trabajadas_julio,
            "Horas Disponibles Agosto (Semana 31)": horas_disponibles,
            "Puede trabajar Finde (>=6h)": "SÍ" if puede_trabajar else "NO"
        })
        
    df = pd.DataFrame(listado_empleados)
    print(df.to_string(index=False))
    
    print("\n=== RESUMEN ===")
    print(f"Total empleados disponibles en Servicio 2 (excluyendo a Poletti): {len(empleados) - 1}")
    print(f"Total empleados que TIENEN horas disponibles para trabajar el fin de semana del 1-2 Agosto (>= 6hs): {disponibles_sabado_domingo}")
    print("Demanda mínima requerida:")
    print("  - Sábado 1 de Agosto: 7 (M) + 9 (T) + 7 (TN) + 7 (N) = 30 personas diferentes")
    print("  - Domingo 2 de Agosto: 7 (M) + 9 (T) + 7 (TN) + 7 (N) = 30 personas diferentes")
    print(f"¿Es posible cubrir el Sábado (mín 30 personas)? {'SÍ' if disponibles_sabado_domingo >= 30 else 'NO'}")

if __name__ == "__main__":
    analizar_horas_transicion()

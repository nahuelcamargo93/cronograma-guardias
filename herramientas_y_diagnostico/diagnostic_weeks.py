import main, data
from ortools.sat.python import cp_model
import pandas as pd

def check_week(week_num):
    print(f"\n--- PROBANDO SEMANA {week_num} ---")
    fecha_inicio_semana = pd.to_datetime("2026-05-25") + pd.Timedelta(days=week_num * 7)
    fecha_inicio_str = fecha_inicio_semana.strftime("%Y-%m-%d")
    
    # Run only for 7 days
    try:
        # We need to temporarily modify main.py to only solve for 7 days and start on fecha_inicio_str
        # Or just call solve_semana if it existed.
        # Let's do a simpler thing: mock the parameters
        
        from db import cargar_datos
        from rule_engine import RuleEngine
        from main import construir_modelo, resolver_modelo
        
        _re = RuleEngine()
        df_personal, turnos_config, ajustes_demanda, licencias, reglas_servicio, reglas_personal, ajustes_reglas_personal, feriados = cargar_datos()
        
        modelo, turnos = construir_modelo(
            df_personal, turnos_config, ajustes_demanda, licencias, 
            reglas_servicio, reglas_personal, ajustes_reglas_personal,
            feriados, fecha_inicio_str, num_semanas=1
        )
        
        status = resolver_modelo(modelo, turnos, df_personal, 7, feriados, fecha_inicio_str, fecha_inicio_semana.weekday(), turnos_config)
        
        if status is not None:
            print(f"Semana {week_num} es FACTIBLE.")
        else:
            print(f"Semana {week_num} es INVIABLE.")
            
    except Exception as e:
        print(f"Error en Semana {week_num}: {e}")

if __name__ == "__main__":
    for i in range(5):
        check_week(i)

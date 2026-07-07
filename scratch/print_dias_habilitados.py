import sys, os
sys.path.append(os.getcwd())
import database.queries as q
config, _, _, _ = q.cargar_configuracion_turnos(1)
for tipo in ["Semana", "Finde_Feriado"]:
    print(f"=== {tipo} ===")
    for t, cfg in config.get(tipo, {}).items():
        print(f"  Turn: {t}, Dias_Habilitados: {cfg.get('Dias_Habilitados')}")

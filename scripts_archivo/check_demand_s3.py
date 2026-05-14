import db as database
from data import FECHA_INICIO, FECHA_FIN, SERVICIO_ID

def check_demand():
    print(f"Checking demand for Service {SERVICIO_ID} from {FECHA_INICIO} to {FECHA_FIN}")
    config, metadata, req, ajustes = database.cargar_configuracion_turnos(SERVICIO_ID, FECHA_INICIO, FECHA_FIN)
    
    print("\n--- DEMANDA CONFIG (req) ---")
    for tipo, lista in req.items():
        print(f"Tipo: {tipo}")
        for r in lista:
            print(f"  - Puesto: {r.get('puesto')} (ID: {r.get('puesto_id')}) | {r.get('hora_inicio')}-{r.get('hora_fin')} | Min: {r.get('cantidad_min')} Max: {r.get('cantidad_max')}")

if __name__ == "__main__":
    check_demand()

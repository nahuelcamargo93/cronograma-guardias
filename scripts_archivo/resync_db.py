import db
import pandas as pd
from data import DEMANDA_TURNOS, AJUSTES_VACANTES, FECHA_INICIO

def resync():
    db.inicializar_db()
    # Esto creará la columna y migrará la demanda con los nuevos días permitidos
    db.migrar_demanda_a_db(DEMANDA_TURNOS, AJUSTES_VACANTES, servicio_id=1, fecha_inicio_cronograma=FECHA_INICIO)
    print("✅ Base de datos actualizada con la columna dias_semana y configurada correctamente.")

if __name__ == "__main__":
    resync()

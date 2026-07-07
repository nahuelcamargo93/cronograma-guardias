import sys
sys.path.append('.')
from datetime import date, timedelta
import pandas as pd
from database import queries as db_queries
from database.data_loader import obtener_empleados, obtener_turnos
import main
from restricciones.hard._utils import determinar_familia_ganadora

servicio_id = 2
fecha_inicio = "2026-08-01"

db_queries.init_licencias(servicio_id)
config_turnos, _, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
    servicio_id=servicio_id, fecha_inicio=fecha_inicio, fecha_fin="2026-08-31"
)
reglas_servicio_db = db_queries.cargar_reglas_servicio(servicio_id)
ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, "2026-08-31")
ajustes_servicio = db_queries.cargar_ajustes_reglas_servicio(fecha_inicio, "2026-08-31", servicio_id)
ajustes_reglas['__servicio__'] = ajustes_servicio

empleados = obtener_empleados(servicio_id, fecha_inicio, 31)
turnos_dict = obtener_turnos(servicio_id)
historial_semana_previa = db_queries.cargar_guardias_previas(fecha_inicio, dias_atras=28, servicio_id=servicio_id)

fecha_inicio_dt = date.fromisoformat(fecha_inicio)
feriados_indices = []

# Build model (patched so it doesn't solve)
main.cargar_y_ejecutar_todas = lambda m, c: None
modelo, turnos, flr_tracker, ctx = main.construir_modelo(
    empleados, config_turnos, turnos_dict, demanda_req, ajustes_db,
    31, feriados_indices, fecha_inicio_dt.weekday(), 6,
    reglas_servicio=reglas_servicio_db,
    ajustes_reglas_personal=ajustes_reglas,
    historial_semana_previa=historial_semana_previa,
    servicio_id=servicio_id,
    fecha_inicio=fecha_inicio,
    fecha_fin="2026-08-31",
    modo_debug=False,
    force_assumptions=False
)

from restricciones.hard._utils import crear_y_vincular_variables_semanales
crear_y_vincular_variables_semanales(modelo, ctx)

# Let's inspect for the first employee
emp = ctx.empleados[0]
nombre = emp.nombre
hist_prev = ctx.historial_semana_previa.get(nombre, [])
primer_lunes = date.fromisoformat("2026-07-27")

dias_por_semana = {}
for d in range(31):
    fd = fecha_inicio_dt + timedelta(days=d)
    lunes = fd - timedelta(days=fd.weekday())
    dias_por_semana.setdefault(lunes.isoformat(), []).append(d)
semanas_keys = sorted(dias_por_semana.keys())

for fam in ['N', 'TN']:
    print(f"\nEmpleado: {nombre} | Familia: {fam}")
    d_min = 3
    w = d_min + 1
    
    secuencia_hist = []
    for sem_idx in range(w - 1, 0, -1):
        lunes_prev_dt = primer_lunes - timedelta(days=sem_idx * 7)
        ganador_prev = determinar_familia_ganadora(hist_prev, lunes_prev_dt)
        hist_flag = 1 if ganador_prev == fam else 0
        secuencia_hist.append(f"Historial {lunes_prev_dt.isoformat()}: {hist_flag}")
        
    secuencia_vars = []
    for sem_key in semanas_keys:
        v_dict = ctx.vars_turno_sem.get((nombre, sem_key))
        if v_dict and fam in v_dict:
            secuencia_vars.append(f"Variable {sem_key}: {v_dict[fam].Name()}")
            
    print("Secuencia completa:")
    for idx, item in enumerate(secuencia_hist + secuencia_vars):
        print(f"  [{idx}] {item}")

conn = sqlite3.connect('cronograma_inteligente.db')
conn.close()

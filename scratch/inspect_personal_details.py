import sys
import os
import datetime
from datetime import date, timedelta

sys.path.append(os.path.abspath('.'))
from database import queries as db_queries
from database.data_loader import obtener_empleados
import rule_engine as _re

servicio_id = 3
fecha_inicio = "2026-06-01"
fecha_fin = "2026-06-30"
fecha_inicio_dt = date.fromisoformat(fecha_inicio)
dias_del_bloque = (date.fromisoformat(fecha_fin) - fecha_inicio_dt).days + 1

empleados = obtener_empleados(servicio_id, fecha_inicio, dias_del_bloque)
reglas_servicio = db_queries.cargar_reglas_servicio(servicio_id)
ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)

target_names = ["Aguilera Graciela", "Diaz Villafañe Morales Abigail", "Motta, Mayra Belen", "Navarro Suarez Gabriela Belén", "Pregot Analia Mariana", "Zeballos Valeria Alejandra"]

# Find targets in employees list (watch out for spelling/encoding)
targets = []
for name in target_names:
    norm_name = name.lower().replace("ñ", "").replace("í", "").replace("é", "")
    for emp in empleados:
        # Match substring
        if name.split()[0].lower() in emp.nombre.lower() or emp.nombre.lower() in name.lower():
            targets.append(emp)
            break

print("Target Employees Constraints Summary:")
for emp in targets:
    print(f"\n========================================\nEmployee: {emp.nombre}")
    print(f"Puestos habilitados: {emp.puestos_habilitados}")
    print(f"Licencias ({len(emp.dias_licencia)}): {sorted(list(emp.dias_licencia))}")
    print("Rules (from DB / model):")
    for r_code, r_val in emp.reglas.items():
        print(f"  - {r_code}: {r_val}")
    
    # Check if they can work on Fridays
    # June Fridays are: June 5 (day 4), June 12 (day 11), June 19 (day 18), June 26 (day 25)
    fridays = [4, 11, 18, 25]
    print("Friday availability (checks licenses and exclusions):")
    for f_day in fridays:
        fecha_d = (fecha_inicio_dt + timedelta(days=f_day)).isoformat()
        is_licensed = f_day in emp.dias_licencia
        
        # Check excluir turnos
        p_excluir = _re.resolver_parametros_regla('EXCLUIR_TURNOS', emp.nombre, fecha_d, reglas_servicio, emp.reglas, ajustes_reglas)
        has_excl = _re.regla_existe(p_excluir) and not _re.regla_suspendida(p_excluir)
        
        # Check franco forzado
        p_franco = _re.resolver_parametros_regla('FRANCO_FORZADO', emp.nombre, fecha_d, reglas_servicio, emp.reglas, ajustes_reglas)
        has_franco = _re.regla_existe(p_franco) and not _re.regla_suspendida(p_franco)
        
        print(f"  Day {f_day} ({fecha_d}): Licensed={is_licensed} | ExcluirTurnos={p_excluir if has_excl else False} | FrancoForzado={has_franco}")

conn = db_queries.sqlite3.connect("cronograma_inteligente.db")
cur = conn.cursor()
print("\nAssignments in Cronograma 215 for these targets:")
for emp in targets:
    cur.execute("SELECT fecha, turno FROM guardias WHERE cronograma_id = 215 AND nombre = ? ORDER BY fecha", (emp.nombre,))
    rows = cur.fetchall()
    print(f"  {emp.nombre}: {len(rows)} shifts: {rows}")
conn.close()

import sys
import os
import datetime
from datetime import date, timedelta

sys.path.append(os.path.abspath('.'))
from database import queries as db_queries
from database.data_loader import obtener_empleados
import rule_engine as _re

db_queries.init_licencias()
reglas_servicio = db_queries.cargar_reglas_servicio(3)
ajustes_reglas = db_queries.cargar_ajustes_reglas_personal("2026-06-01", "2026-06-30")

# Get active employees for service 3
empleados = obtener_empleados(3, "2026-06-01", 30)

# Filter residentes
residentes = [e for e in empleados if e.rol == "Residente"]

print(f"Total active residentes loaded: {len(residentes)}")
for r in residentes:
    print(f"  - {r.nombre}")

# Long weekend: June 13 (day 12), June 14 (day 13), June 15 (day 14)
long_weekend = [12, 13, 14]
fecha_inicio_dt = date.fromisoformat("2026-06-01")

print("\n--- Availability during June 13-15 ---")
for r in residentes:
    print(f"\nResidente: {r.nombre}")
    print(f"  Puestos Habilitados: {r.puestos_habilitados}")
    for d in long_weekend:
        fecha_str = (fecha_inicio_dt + timedelta(days=d)).isoformat()
        is_licensed = d in r.dias_licencia
        
        # Check Excluir turnos
        p_excluir = _re.resolver_parametros_regla('EXCLUIR_TURNOS', r.nombre, fecha_str, reglas_servicio, r.reglas, ajustes_reglas)
        has_excl = _re.regla_existe(p_excluir) and not _re.regla_suspendida(p_excluir)
        
        # Check Franco Forzado
        p_franco = _re.resolver_parametros_regla('FRANCO_FORZADO', r.nombre, fecha_str, reglas_servicio, r.reglas, ajustes_reglas)
        has_franco = _re.regla_existe(p_franco) and not _re.regla_suspendida(p_franco)
        
        # Check Cumpleaños
        p_cumple = _re.resolver_parametros_regla('CUMPLEANOS_LIBRE', r.nombre, fecha_str, reglas_servicio, r.reglas, ajustes_reglas)
        has_cumple = _re.regla_existe(p_cumple) and not _re.regla_suspendida(p_cumple)
        is_birthday = r.fecha_cumpleanos is not None and isinstance(r.fecha_cumpleanos, str) and r.fecha_cumpleanos[5:] == fecha_str[5:]
        
        # Check Asignacion Fija
        p_asig = _re.resolver_parametros_regla('ASIGNACION_FIJA', r.nombre, fecha_str, reglas_servicio, r.reglas, ajustes_reglas)
        has_asig = _re.regla_existe(p_asig) and not _re.regla_suspendida(p_asig)
        
        print(f"    Day {d} ({fecha_str}): Licensed={is_licensed} | ExcluirTurnos={has_excl} | FrancoForzado={has_franco} (params: {p_franco}) | Birthday={is_birthday} (has_rule: {has_cumple}) | AsignacionFija={p_asig if has_asig else False}")

conn = db_queries.sqlite3.connect("cronograma_inteligente.db")
cur = conn.cursor()
print("\n--- Any personal_reglas_ajustes for Residentes in June? ---")
for r in residentes:
    cur.execute("""
        SELECT id, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo
        FROM personal_reglas_ajustes
        WHERE personal_nombre = ? AND fecha_inicio <= '2026-06-30' AND fecha_fin >= '2026-06-01'
    """, (r.nombre,))
    rows = cur.fetchall()
    if rows:
        print(f"\n{r.nombre}:")
        for row in rows:
            print(f"  {row}")
conn.close()

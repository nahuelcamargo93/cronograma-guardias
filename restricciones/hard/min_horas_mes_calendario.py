"""restricciones/hard/min_horas_mes_calendario.py — Piso mínimo de horas por mes calendario.

Regla DOUBLE: soporta modo HARD (restricción dura) y SOFT (penalización proporcional al déficit).
Configuración en BD (parametros_json):
  {"min_horas": 185, "modo": "SOFT", "peso_soft": 100000}
Si modo no está definido o es "HARD", se comporta como restricción dura vía add_hard.
"""
import calendar
from datetime import date, timedelta
from restricciones.cargador import add_hard
from restricciones.hard._utils import is_finde
import rule_engine as _re


def apply(modelo, ctx) -> None:
    fecha_inicio_dt = date.fromisoformat(ctx.fecha_inicio)
    for emp in ctx.empleados:
        meses = {}
        for d in range(ctx.dias):
            meses.setdefault((fecha_inicio_dt + timedelta(days=d)).strftime("%Y-%m"), []).append(d)

        for m_key, dias_m in meses.items():
            ref = (fecha_inicio_dt + timedelta(days=dias_m[0])).isoformat()
            p_min = _re.resolver_parametros_regla(
                'MIN_HORAS_MES_CALENDARIO', emp.nombre, ref,
                ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
            )
            p_max = _re.resolver_parametros_regla(
                'MAX_HORAS_MES_CALENDARIO', emp.nombre, ref,
                ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
            )
            if not _re.regla_existe(p_min) or _re.regla_suspendida(p_min):
                continue
            min_h = p_min.get('min_horas', 144) if isinstance(p_min, dict) else 144
            modo = p_min.get('modo', 'HARD') if isinstance(p_min, dict) else 'HARD'
            peso_soft = p_min.get('peso_soft', 100_000) if isinstance(p_min, dict) else 100_000

            if not _re.regla_suspendida(p_max):
                max_h_ref = p_max.get('max_horas', 192) if isinstance(p_max, dict) else 192
                if min_h > max_h_ref:
                    min_h = max_h_ref

            vars_h = []
            for d in dias_m:
                td = "Finde_Feriado" if is_finde(d, ctx.offset_dia, ctx.feriados) else "Semana"
                for t in ctx.demanda_turnos.get(td, {}).keys():
                    if (emp.nombre, d, t) in ctx.turnos:
                        vars_h.append(ctx.turnos[(emp.nombre, d, t)] * ctx.turnos_dict[t].horas)

            dias_lic = [d for d in dias_m if d in emp.dias_licencia]
            p_cred = _re.resolver_parametros_regla(
                'CREDITO_HORARIO_LICENCIA', emp.nombre, ref,
                ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
            )
            
            y, m = map(int, m_key.split("-"))
            dias_del_mes = calendar.monthrange(y, m)[1]

            if _re.regla_existe(p_cred) and not _re.regla_suspendida(p_cred):
                if 'horas_mensuales_base' in p_cred:
                    horas_lic = int((p_cred.get('horas_mensuales_base') / dias_del_mes) * len(dias_lic) + 0.5)
                else:
                    horas_lic = int((p_cred.get('horas_por_semana', 36) / 7.0) * len(dias_lic) + 0.5)
            else:
                horas_lic = 0

            piso = int((float(min_h) / dias_del_mes) * len(dias_m) + 0.5)
            if not vars_h:
                continue

            if modo.upper() == "SOFT":
                # Variable entera de déficit: deficit >= piso - (sum_h + horas_lic)
                nombre_limpio = emp.nombre.replace(" ", "_").replace(",", "")
                deficit = modelo.NewIntVar(0, piso, f"deficit_min_h_{nombre_limpio}_{m_key}")
                modelo.Add(deficit >= piso - sum(vars_h) - horas_lic)
                ctx.penalizaciones_soft.append(deficit * peso_soft)
            else:
                add_hard(modelo, ctx,
                         modelo.Add(sum(vars_h) + horas_lic >= piso),
                         f"{emp.nombre}_{m_key}")

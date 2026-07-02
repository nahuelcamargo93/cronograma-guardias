"""restricciones/hard/max_horas_mes_calendario.py — Tope máximo de horas por mes calendario."""
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
            params = _re.resolver_parametros_regla(
                'MAX_HORAS_MES_CALENDARIO', emp.nombre, ref,
                ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
            )
            if _re.regla_suspendida(params):
                continue
            max_h = params.get('max_horas', 144) if isinstance(params, dict) else 144
            modo = params.get('modo', 'HARD') if isinstance(params, dict) else 'HARD'
            peso_soft = params.get('peso_soft', 100_000) if isinstance(params, dict) else 100_000

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
                horas_lic = int((float(max_h) / dias_del_mes) * len(dias_lic) + 0.5)

            tope = int((float(max_h) / dias_del_mes) * len(dias_m) + 0.5)
            horas_lic = min(horas_lic, tope)
            if vars_h:
                if modo.upper() == "SOFT":
                    nombre_limpio = emp.nombre.replace(" ", "_").replace(",", "")
                    exceso = modelo.NewIntVar(0, 744, f"exceso_max_h_{nombre_limpio}_{m_key}")
                    modelo.Add(exceso >= sum(vars_h) + horas_lic - tope)
                    ctx.penalizaciones_soft.append(exceso * peso_soft)
                else:
                    add_hard(modelo, ctx,
                             modelo.Add(sum(vars_h) + horas_lic <= tope),
                             f"{emp.nombre}_{m_key}")


"""restricciones/hard/_utils.py — Utilidades matemáticas compartidas entre micro-reglas."""
from datetime import date, timedelta
from typing import Dict, List, Any


def get_semanas_calendario(dias: int, fecha_inicio_dt: date) -> Dict[tuple, list]:
    semanas = {}
    for d in range(dias):
        fecha_d = fecha_inicio_dt + timedelta(days=d)
        iso_year, iso_week, _ = fecha_d.isocalendar()
        semanas.setdefault((iso_year, iso_week), []).append((d, fecha_d))
    return semanas


def is_finde(d: int, offset_dia: int, feriados) -> bool:
    return ((d + offset_dia) % 7) >= 5 or d in feriados


def prohibir_turnos_dia(modelo, ctx, nombre_emp: str, dia_idx: int) -> None:
    for td in ["Semana", "Finde_Feriado"]:
        for t in ctx.demanda_turnos.get(td, {}).keys():
            if (nombre_emp, dia_idx, t) in ctx.turnos:
                modelo.Add(ctx.turnos[(nombre_emp, dia_idx, t)] == 0)


def mapear_turno_a_familias(turno: str) -> List[str]:
    t = turno.upper()
    if t in ('MT', 'MT_UTI', 'MT_UCO', 'MAÑANA_TARDE'): return ['M', 'T']
    if t == 'M': return ['M']
    if t == 'T': return ['T']
    if t == 'TN': return ['TN']
    if t in ('N', 'NOCHE'): return ['N']
    if 'MT' in t or 'MAÑANA' in t or 'MAANA' in t:
        return ['M', 'T'] if 'TARDE' in t else ['M']
    if 'TNN' in t: return ['TN', 'N']
    if 'TARDE' in t: return ['T']
    if 'UCO' in t or 'UTI' in t:
        if t.startswith('M'): return ['M']
        if t.startswith('T'): return ['T']
    familias = []
    if 'M' in t: familias.append('M')
    if 'T' in t:
        if 'TN' not in t or t.count('T') > 1: familias.append('T')
    if 'TN' in t: familias.append('TN')
    if 'N' in t:
        if 'TN' not in t or t.count('N') > 1: familias.append('N')
    return familias if familias else ['M']


def determinar_familia_ganadora(historial_semana: list, lunes_semana_dt: date):
    conteos = {'M': 0, 'T': 0, 'TN': 0, 'N': 0}
    ultimo = {'M': date.min, 'T': date.min, 'TN': date.min, 'N': date.min}
    tiene = False
    for h in historial_semana:
        h_fecha_str = h.get('fecha')
        if not h_fecha_str: continue
        h_fecha = date.fromisoformat(h_fecha_str)
        if lunes_semana_dt <= h_fecha < lunes_semana_dt + timedelta(days=7):
            for f in mapear_turno_a_familias(h.get('turno', '')):
                if f in conteos:
                    conteos[f] += 1
                    tiene = True
                    if h_fecha > ultimo[f]: ultimo[f] = h_fecha
    if not tiene: return None
    max_c = max(conteos.values())
    cands = [f for f, c in conteos.items() if c == max_c]
    if len(cands) == 1: return cands[0]
    ganador = cands[0]
    for c in cands[1:]:
        if ultimo[c] > ultimo[ganador]: ganador = c
    return ganador


def crear_y_vincular_variables_semanales(modelo, ctx) -> None:
    """Crea las vars de categoría semanal (M/T/TN/N) y las almacena en ctx.vars_turno_sem."""
    fecha_inicio_dt = date.fromisoformat(ctx.fecha_inicio)
    dias_por_semana = {}
    for d in range(ctx.dias):
        fecha_d = fecha_inicio_dt + timedelta(days=d)
        lunes = fecha_d - timedelta(days=fecha_d.weekday())
        dias_por_semana.setdefault(lunes.isoformat(), []).append(d)

    for emp in ctx.empleados:
        nombre = emp.nombre
        hist_prev = ctx.historial_semana_previa.get(nombre, []) if ctx.historial_semana_previa else []
        for sem_key, dias_sem in dias_por_semana.items():
            sid = sem_key.replace("-", "_")
            lunes_dt = date.fromisoformat(sem_key)
            is_M  = modelo.NewBoolVar(f'is_M_{nombre}_{sid}')
            is_T  = modelo.NewBoolVar(f'is_T_{nombre}_{sid}')
            is_TN = modelo.NewBoolVar(f'is_TN_{nombre}_{sid}')
            is_N  = modelo.NewBoolVar(f'is_N_{nombre}_{sid}')
            ctx.vars_turno_sem[(nombre, sem_key)] = {'M': is_M, 'T': is_T, 'TN': is_TN, 'N': is_N}

            for d in dias_sem:
                for key, var in [('M', is_M), ('T', is_T), ('TN', is_TN), ('N', is_N)]:
                    if (nombre, d, key) in ctx.turnos:
                        modelo.AddImplication(ctx.turnos[(nombre, d, key)], var)
                if (nombre, d, 'MT') in ctx.turnos:
                    modelo.Add(is_M + is_T >= 1).OnlyEnforceIf(ctx.turnos[(nombre, d, 'MT')])
                if (nombre, d, 'TNN') in ctx.turnos:
                    modelo.Add(is_TN + is_N >= 1).OnlyEnforceIf(ctx.turnos[(nombre, d, 'TNN')])

            ganador = determinar_familia_ganadora(hist_prev, lunes_dt)
            hist_flags = {'M': 0, 'T': 0, 'TN': 0, 'N': 0}
            if ganador:
                hist_flags[ganador] = 1
                var_map = {'M': is_M, 'T': is_T, 'TN': is_TN, 'N': is_N}
                modelo.Add(var_map[ganador] == 1)
            vars_M  = [ctx.turnos[(nombre, d, 'M')]  for d in dias_sem if (nombre, d, 'M')  in ctx.turnos]
            vars_T  = [ctx.turnos[(nombre, d, 'T')]  for d in dias_sem if (nombre, d, 'T')  in ctx.turnos]
            vars_TN = [ctx.turnos[(nombre, d, 'TN')] for d in dias_sem if (nombre, d, 'TN') in ctx.turnos]
            vars_N  = [ctx.turnos[(nombre, d, 'N')]  for d in dias_sem if (nombre, d, 'N')  in ctx.turnos]
            vars_MT  = [ctx.turnos[(nombre, d, 'MT')]  for d in dias_sem if (nombre, d, 'MT')  in ctx.turnos]
            vars_TNN = [ctx.turnos[(nombre, d, 'TNN')] for d in dias_sem if (nombre, d, 'TNN') in ctx.turnos]
            modelo.Add(is_M  <= sum(vars_M)  + sum(vars_MT)  + hist_flags['M'])
            modelo.Add(is_T  <= sum(vars_T)  + sum(vars_MT)  + hist_flags['T'])
            modelo.Add(is_TN <= sum(vars_TN) + sum(vars_TNN) + hist_flags['TN'])
            modelo.Add(is_N  <= sum(vars_N)  + sum(vars_TNN) + hist_flags['N'])

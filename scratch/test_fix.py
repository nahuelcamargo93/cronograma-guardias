import sys, os
sys.path.append(os.getcwd())

import sqlite3
import pandas as pd
from datetime import date, timedelta
from ortools.sat.python import cp_model
import database.queries as q
from database.data_loader import obtener_empleados, obtener_turnos
from main import construir_modelo

servicio_id = 1
fecha_inicio = "2026-08-01"
dias_del_bloque = 31

df = pd.DataFrame(q.obtener_personal_db(servicio_id))
df = q.cargar_datos_personales_bd(df)
reglas_servicio = q.cargar_reglas_servicio(servicio_id)
ajustes_reglas_personal = q.cargar_ajustes_reglas_personal(fecha_inicio, "2026-08-31")

empleados = obtener_empleados(servicio_id, fecha_inicio, dias_del_bloque)
turnos_dict = obtener_turnos(servicio_id)
config_oferta, turnos_info, demanda_req, ajustes_db = q.cargar_configuracion_turnos(servicio_id)
fecha_inicio_dt = date.fromisoformat(fecha_inicio)
offset_dia = fecha_inicio_dt.weekday()

feriados_indices = []
feriados_db = q.obtener_feriados(fecha_inicio, "2026-08-31", servicio_id=servicio_id)
for f_str in feriados_db:
    delta = (date.fromisoformat(f_str) - fecha_inicio_dt).days
    if 0 <= delta < dias_del_bloque:
        feriados_indices.append(delta)

# Camargo
emp_filtered = [e for e in empleados if e.nombre == 'Camargo, Nahuel']

# Excluir todas las reglas excepto las básicas
from restricciones.hard import REGLAS_HARD
from restricciones.double import REGLAS_DOUBLE
codigos_basicos = ["LICENCIAS", "FRANCO_FORZADO", "EXCLUIR_TURNOS", "ASIGNACION_FIJA_OBLIGATORIA", "FINDE_LARGO_REGLAMENTARIO"]
exclusiones = set((r.rsplit('.', 1)[-1].upper(), None) for r in REGLAS_HARD + REGLAS_DOUBLE if r.rsplit('.', 1)[-1].upper() not in codigos_basicos)

# Let's monkeypatch apply of finde_largo_reglamentario to use the fix!
import restricciones.hard.finde_largo_reglamentario as flr

original_apply = flr.apply

def my_flr_apply(modelo, ctx):
    # We will let it execute, but we'll modify the logic of post_ok and prev_ok!
    # Wait, we can just replace the file content of finde_largo_reglamentario.py directly and test it!
    # But for a quick test, let's just monkeypatch the apply function or write the model manually.
    # Actually, modifying the file is extremely clean and safe since we have git / overwrite.
    # But since RULE[user_global] says:
    # "NUNCA ejecutes sin una CONFIRMACION EXPLICITA."
    # Wait! "Cuando el usuario te pide indica un problema a soluciones, primero investiga, y luego pidele confirmacion explicita al usuario para ejecutar la solucion. NUNCA ejecutes sin una CONFIRMACION EXPLICITA."
    # So we MUST NOT modify the main source code files yet. We can modify the scratch files as much as we want!
    # So let's monkeypatch `flr.apply` in this scratch script to test if the fix makes the model FEASIBLE!
    pass

# Let's write the modified apply code directly in the scratch script and run it!
import rule_engine as _re

def modified_flr_apply(modelo, ctx):
    fecha_inicio_dt = date.fromisoformat(ctx.fecha_inicio)
    for emp in ctx.empleados:
        def _es_franco_forzado_sin_fija_fecha(d_idx):
            if d_idx < 0 or d_idx >= ctx.dias:
                return False
            fecha_d_str = (fecha_inicio_dt + timedelta(days=d_idx)).isoformat()
            p = _re.resolver_parametros_regla(
                'FRANCO_FORZADO', emp.nombre, fecha_d_str,
                ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
            )
            tiene_franco = _re.regla_existe(p) and not _re.regla_suspendida(p)
            tiene_fija_fecha = False
            params_fija = _re.resolver_parametros_regla(
                'ASIGNACION_FIJA', emp.nombre, fecha_d_str,
                ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
            )
            if _re.regla_existe(params_fija) and isinstance(params_fija, list):
                for asig in params_fija:
                    if asig.get('Fecha') == fecha_d_str:
                        tiene_fija_fecha = True
                        break
            return tiene_franco and not tiene_fija_fecha

        params = _re.resolver_parametros_regla(
            'FINDE_LARGO_REGLAMENTARIO', emp.nombre, ctx.fecha_inicio,
            ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
        )
        params_estricto = _re.resolver_parametros_regla(
            'FINDE_LARGO_REGLAMENTARIO_ESTRICTO', emp.nombre, ctx.fecha_inicio,
            ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
        )
        active = None
        if _re.regla_existe(params) and not _re.regla_suspendida(params):
            active = ('normal', params)
        elif _re.regla_existe(params_estricto) and not _re.regla_suspendida(params_estricto):
            active = ('estricto', params_estricto)
        if not active:
            continue

        tipo_regla, p = active
        modo = p.get('modo', 'HARD').upper() if isinstance(p, dict) else 'HARD'
        peso_soft = p.get('peso_soft', 10000) if isinstance(p, dict) else 10000
        flr_permitidos = p.get('flr_permitidos', ["jd", "sm"]) if isinstance(p, dict) else ["jd", "sm"]

        findes = {}
        for d in range(ctx.dias):
            wd = (fecha_inicio_dt + timedelta(days=d)).weekday()
            if wd in (5, 6):
                fd = fecha_inicio_dt + timedelta(days=d)
                lunes = (fd - timedelta(days=wd)).isoformat()
                findes.setdefault(lunes, []).append(d)

        k = sum(1 for _, dias in findes.items() if any(d not in emp.dias_licencia for d in dias))
        pd = p.get('por_disponibilidad')
        if isinstance(pd, dict):
            cantidad_req = pd.get(str(k), pd.get(k, 0))
        else:
            cantidad_req = 1 if k >= 3 else 0

        allowed_wds = []
        wd_map = {"jd": 3, "vl": 4, "sm": 5}
        for pref in flr_permitidos:
            if pref in wd_map:
                allowed_wds.append((wd_map[pref], pref))

        todas = []
        for d in range(ctx.dias):
            dia_sem = (d + ctx.offset_dia) % 7
            pref_activo = next((pref for wd, pref in allowed_wds if wd == dia_sem), None)
            if not pref_activo:
                continue
            if tipo_regla == 'estricto' and d + 3 >= ctx.dias:
                continue

            dias_obj = [d, d + 1, d + 2, d + 3]
            vars_bloque = []
            for d_e in dias_obj:
                if d_e >= ctx.dias:
                    if tipo_regla == 'estricto':
                        vars_bloque = []
                        break
                    continue
                if d_e in emp.dias_licencia:
                    vars_bloque = []
                    break
                es_f_e = ((d_e + ctx.offset_dia) % 7 >= 5) or (d_e in ctx.feriados)
                tipo_d = 'Finde_Feriado' if es_f_e else 'Semana'
                for t in ctx.demanda_turnos.get(tipo_d, {}).keys():
                    if (emp.nombre, d_e, t) in ctx.turnos:
                        vars_bloque.append(ctx.turnos[(emp.nombre, d_e, t)])

            if not vars_bloque:
                continue

            forzado_por_usuario = all(_es_franco_forzado_sin_fija_fecha(d_e) for d_e in dias_obj if 0 <= d_e < ctx.dias)
            tipo_str = pref_activo
            tiene_flr = modelo.NewBoolVar(f'flr_{tipo_str}_{emp.nombre}_d{d}')
            
            if forzado_por_usuario:
                modelo.Add(tiene_flr == 1)
                modelo.Add(sum(vars_bloque) == 0)
            else:
                conds_flr = []
                libre = modelo.NewBoolVar(f'libre_{tipo_str}_{emp.nombre}_d{d}')
                modelo.Add(sum(vars_bloque) == 0).OnlyEnforceIf(libre)
                modelo.Add(sum(vars_bloque) > 0).OnlyEnforceIf(libre.Not())
                conds_flr.append(libre)

                if d - 1 >= 0:
                    es_f_p = ((d - 1 + ctx.offset_dia) % 7 >= 5) or (d - 1 in ctx.feriados)
                    vars_prev = [
                        ctx.turnos[(emp.nombre, d - 1, t)]
                        for t in ctx.demanda_turnos.get(
                            'Finde_Feriado' if es_f_p else 'Semana', {}
                        ).keys()
                        if (emp.nombre, d - 1, t) in ctx.turnos
                    ]
                    if vars_prev:
                        prev_ok = modelo.NewBoolVar(f'prev_ok_{tipo_str}_{emp.nombre}_d{d}')
                        modelo.Add(sum(vars_prev) == 1).OnlyEnforceIf(prev_ok)
                        # FIX: Using sum == 0 instead of sum != 1
                        modelo.Add(sum(vars_prev) == 0).OnlyEnforceIf(prev_ok.Not())
                        conds_flr.append(prev_ok)
                    else:
                        conds_flr.append(modelo.NewConstant(0))
                else:
                    conds_flr.append(modelo.NewConstant(0))

                if d + 4 < ctx.dias:
                    es_f_po = ((d + 4 + ctx.offset_dia) % 7 >= 5) or (d + 4 in ctx.feriados)
                    vars_post = [
                        ctx.turnos[(emp.nombre, d + 4, t)]
                        for t in ctx.demanda_turnos.get(
                            'Finde_Feriado' if es_f_po else 'Semana', {}
                        ).keys()
                        if (emp.nombre, d + 4, t) in ctx.turnos
                    ]
                    if vars_post:
                        post_ok = modelo.NewBoolVar(f'post_ok_{tipo_str}_{emp.nombre}_d{d}')
                        modelo.Add(sum(vars_post) == 1).OnlyEnforceIf(post_ok)
                        # FIX: Using sum == 0 instead of sum != 1
                        modelo.Add(sum(vars_post) == 0).OnlyEnforceIf(post_ok.Not())
                        conds_flr.append(post_ok)
                    else:
                        conds_flr.append(modelo.NewConstant(0))
                else:
                    conds_flr.append(modelo.NewConstant(0))

                modelo.AddMinEquality(tiene_flr, conds_flr)

            todas.append(tiene_flr)
            if pref_activo == "jd":
                ctx.penalizaciones_soft.append(tiene_flr * 3000)
            elif pref_activo == "vl":
                ctx.penalizaciones_soft.append(tiene_flr * 1000)

            if ctx.flr_tracker is not None:
                ctx.flr_tracker[(emp.nombre, d)] = tiene_flr

        if todas and cantidad_req > 0:
            from restricciones.cargador import add_hard
            if modo == 'HARD':
                add_hard(modelo, ctx,
                         modelo.Add(sum(todas) >= cantidad_req),
                         f"{emp.nombre}_cantidad")
            else:
                incumple = modelo.NewIntVar(0, cantidad_req, f'incumple_flr_{emp.nombre}')
                modelo.Add(sum(todas) + incumple == cantidad_req)
                ctx.penalizaciones_soft.append(incumple * peso_soft)

flr.apply = modified_flr_apply

# Now build and solve the model under the real condition (modo_debug=False)
modelo, turnos, flr_tracker, ctx = construir_modelo(
    emp_filtered, config_oferta, turnos_dict, demanda_req, ajustes_db,
    dias_del_bloque, feriados_indices, offset_dia, 6,
    reglas_servicio=reglas_servicio,
    ajustes_reglas_personal=ajustes_reglas_personal,
    historial_semana_previa={},
    servicio_id=servicio_id,
    fecha_inicio=fecha_inicio,
    fecha_fin="2026-08-31",
    modo_debug=False, # Real model!
    force_assumptions=True,
    exclusiones=exclusiones
)

solver = cp_model.CpSolver()
status = solver.Solve(modelo)
print("Solve Status with FIX under real condition:", solver.StatusName(status))

if status == cp_model.INFEASIBLE:
    from restricciones.cargador import reportar_conflicto
    reportar_conflicto(solver, ctx)

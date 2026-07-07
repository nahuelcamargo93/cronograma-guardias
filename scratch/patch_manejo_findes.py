import os

filepath = "restricciones/double/manejo_findes.py"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Normalizar retornos de carro
content_norm = content.replace("\r\n", "\n")

target = """    def crear_var_flr(emp, lunes, d_inicio, prefijo):
        dias_flr = [d_inicio, d_inicio + 1, d_inicio + 2, d_inicio + 3]
        for d_e in dias_flr:
            if d_e < 0 or d_e >= ctx.dias:
                return None
            if d_e in emp.dias_licencia:
                return None

        # Verificar si todos los días de este bloque libre de 4 días tienen franco forzado activo
        # (por ende, el bloque libre fue configurado explícitamente por el usuario)
        def _tiene_franco_forzado(d_idx):
            fecha_d_str = (fecha_inicio_dt + timedelta(days=d_idx)).isoformat()
            p = _re.resolver_parametros_regla(
                'FRANCO_FORZADO', emp.nombre, fecha_d_str,
                ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
            )
            return _re.regla_existe(p) and not _re.regla_suspendida(p)

        forzado_por_usuario = all(_tiene_franco_forzado(d_e) for d_e in dias_flr)
        
        var_bloque = modelo.NewBoolVar(f'flr_{prefijo}_{emp.nombre}_{lunes}')
        flr_conds = []
        
        vars_bloque_flr = []
        for d_e in dias_flr:
            es_f = is_finde(d_e, ctx.offset_dia, ctx.feriados)
            for t in ctx.demanda_turnos.get("Finde_Feriado" if es_f else "Semana", {}).keys():
                if (emp.nombre, d_e, t) in ctx.turnos:
                    vars_bloque_flr.append(ctx.turnos[(emp.nombre, d_e, t)])
                    
        libre_flr = modelo.NewBoolVar(f'libre_{prefijo}_{emp.nombre}_{lunes}')
        if vars_bloque_flr:
            modelo.Add(sum(vars_bloque_flr) == 0).OnlyEnforceIf(libre_flr)
            modelo.Add(sum(vars_bloque_flr) > 0).OnlyEnforceIf(libre_flr.Not())
        else:
            modelo.Add(libre_flr == 1)
        flr_conds.append(libre_flr)
        
        d_prev = d_inicio - 1
        if d_prev >= 0:
            es_f_p = is_finde(d_prev, ctx.offset_dia, ctx.feriados)
            vars_prev = [
                ctx.turnos[(emp.nombre, d_prev, t)]
                for t in ctx.demanda_turnos.get("Finde_Feriado" if es_f_p else "Semana", {}).keys()
                if (emp.nombre, d_prev, t) in ctx.turnos
            ]
            if vars_prev:
                prev_ok = modelo.NewBoolVar(f'prev_{prefijo}_{emp.nombre}_{lunes}')
                modelo.AddBoolOr(vars_prev).OnlyEnforceIf(prev_ok)
                modelo.AddBoolAnd([v.Not() for v in vars_prev]).OnlyEnforceIf(prev_ok.Not())
                flr_conds.append(prev_ok)
            else:
                flr_conds.append(modelo.NewConstant(0))
        else:
            flr_conds.append(modelo.NewConstant(0))
            
        d_post = d_inicio + 4
        if d_post < ctx.dias:
            es_f_po = is_finde(d_post, ctx.offset_dia, ctx.feriados)
            vars_post = [
                ctx.turnos[(emp.nombre, d_post, t)]
                for t in ctx.demanda_turnos.get("Finde_Feriado" if es_f_po else "Semana", {}).keys()
                if (emp.nombre, d_post, t) in ctx.turnos
            ]
            if vars_post:
                post_ok = modelo.NewBoolVar(f'post_{prefijo}_{emp.nombre}_{lunes}')
                modelo.AddBoolOr(vars_post).OnlyEnforceIf(post_ok)
                modelo.AddBoolAnd([v.Not() for v in vars_post]).OnlyEnforceIf(post_ok.Not())
                flr_conds.append(post_ok)
            else:
                flr_conds.append(modelo.NewConstant(0))
        else:
            flr_conds.append(modelo.NewConstant(0))
            
        modelo.AddBoolAnd(flr_conds).OnlyEnforceIf(var_bloque)
        modelo.AddBoolOr([v.Not() if hasattr(v, 'Not') else v == 0 for v in flr_conds]).OnlyEnforceIf(var_bloque.Not())
        
        if forzado_por_usuario:
            modelo.Add(var_bloque == 1)
            
        return var_bloque"""

replacement = """    def crear_var_flr(emp, lunes, d_inicio, prefijo):
        dias_flr = [d_inicio, d_inicio + 1, d_inicio + 2, d_inicio + 3]
        for d_e in dias_flr:
            if d_e >= ctx.dias:
                return None
            if d_e >= 0:
                if d_e in emp.dias_licencia:
                    return None
            else:
                # d_e < 0 (mes anterior): si trabajó ese día, no es un bloque libre válido
                fecha_d_str = (fecha_inicio_dt + timedelta(days=d_e)).isoformat()
                hist_emp = ctx.historial_semana_previa.get(emp.nombre, []) if ctx.historial_semana_previa else []
                trabajado_d = any(h['fecha'] == fecha_d_str and h.get('horas', 0) > 0 for h in hist_emp)
                if trabajado_d:
                    return None

        # Verificar si todos los días de este bloque libre de 4 días tienen franco forzado activo
        # (por ende, el bloque libre fue configurado explícitamente por el usuario)
        def _tiene_franco_forzado(d_idx):
            if d_idx < 0 or d_idx >= ctx.dias:
                return False
            fecha_d_str = (fecha_inicio_dt + timedelta(days=d_idx)).isoformat()
            p = _re.resolver_parametros_regla(
                'FRANCO_FORZADO', emp.nombre, fecha_d_str,
                ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
            )
            return _re.regla_existe(p) and not _re.regla_suspendida(p)

        forzado_por_usuario = all(_tiene_franco_forzado(d_e) for d_e in dias_flr if d_e >= 0)
        
        var_bloque = modelo.NewBoolVar(f'flr_{prefijo}_{emp.nombre}_{lunes}')
        flr_conds = []
        
        vars_bloque_flr = []
        for d_e in dias_flr:
            if d_e < 0 or d_e >= ctx.dias:
                continue
            es_f = is_finde(d_e, ctx.offset_dia, ctx.feriados)
            for t in ctx.demanda_turnos.get("Finde_Feriado" if es_f else "Semana", {}).keys():
                if (emp.nombre, d_e, t) in ctx.turnos:
                    vars_bloque_flr.append(ctx.turnos[(emp.nombre, d_e, t)])
                    
        libre_flr = modelo.NewBoolVar(f'libre_{prefijo}_{emp.nombre}_{lunes}')
        if vars_bloque_flr:
            modelo.Add(sum(vars_bloque_flr) == 0).OnlyEnforceIf(libre_flr)
            modelo.Add(sum(vars_bloque_flr) > 0).OnlyEnforceIf(libre_flr.Not())
        else:
            modelo.Add(libre_flr == 1)
        flr_conds.append(libre_flr)
        
        d_prev = d_inicio - 1
        if d_prev >= 0:
            es_f_p = is_finde(d_prev, ctx.offset_dia, ctx.feriados)
            vars_prev = [
                ctx.turnos[(emp.nombre, d_prev, t)]
                for t in ctx.demanda_turnos.get("Finde_Feriado" if es_f_p else "Semana", {}).keys()
                if (emp.nombre, d_prev, t) in ctx.turnos
            ]
            if vars_prev:
                prev_ok = modelo.NewBoolVar(f'prev_{prefijo}_{emp.nombre}_{lunes}')
                modelo.AddBoolOr(vars_prev).OnlyEnforceIf(prev_ok)
                modelo.AddBoolAnd([v.Not() for v in vars_prev]).OnlyEnforceIf(prev_ok.Not())
                flr_conds.append(prev_ok)
            else:
                flr_conds.append(modelo.NewConstant(0))
        else:
            # d_prev < 0 (pertenece al mes anterior)
            fecha_prev_str = (fecha_inicio_dt + timedelta(days=d_prev)).isoformat()
            hist_emp = ctx.historial_semana_previa.get(emp.nombre, []) if ctx.historial_semana_previa else []
            trabajo_previo = any(h['fecha'] == fecha_prev_str and h.get('horas', 0) > 0 for h in hist_emp)
            if trabajo_previo:
                flr_conds.append(modelo.NewConstant(1))
            else:
                if ctx.historial_semana_previa:
                    flr_conds.append(modelo.NewConstant(0))
                else:
                    flr_conds.append(modelo.NewConstant(1))
            
        d_post = d_inicio + 4
        if d_post < ctx.dias:
            es_f_po = is_finde(d_post, ctx.offset_dia, ctx.feriados)
            vars_post = [
                ctx.turnos[(emp.nombre, d_post, t)]
                for t in ctx.demanda_turnos.get("Finde_Feriado" if es_f_po else "Semana", {}).keys()
                if (emp.nombre, d_post, t) in ctx.turnos
            ]
            if vars_post:
                post_ok = modelo.NewBoolVar(f'post_{prefijo}_{emp.nombre}_{lunes}')
                modelo.AddBoolOr(vars_post).OnlyEnforceIf(post_ok)
                modelo.AddBoolAnd([v.Not() for v in vars_post]).OnlyEnforceIf(post_ok.Not())
                flr_conds.append(post_ok)
            else:
                flr_conds.append(modelo.NewConstant(0))
        else:
            flr_conds.append(modelo.NewConstant(1))
            
        modelo.AddBoolAnd(flr_conds).OnlyEnforceIf(var_bloque)
        modelo.AddBoolOr([v.Not() if hasattr(v, 'Not') else v == 0 for v in flr_conds]).OnlyEnforceIf(var_bloque.Not())
        
        if forzado_por_usuario:
            modelo.Add(var_bloque == 1)
            
        return var_bloque"""

if target in content_norm:
    content_norm = content_norm.replace(target, replacement)
    with open(filepath, "w", encoding="utf-8", newline="\n") as f:
        f.write(content_norm)
    print("Patch applied successfully!")
else:
    print("Target content not found in file!")

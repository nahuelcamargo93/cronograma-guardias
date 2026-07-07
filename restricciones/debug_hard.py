"""
restricciones/debug_hard.py — Diagnóstico matemático iterativo (Modo Debug Hard).

Aísla conflictos matemáticos de inviabilidad mediante un flujo de decisiones
lógicas de encendido progresivo (búsqueda incremental de colisiones)
tanto para reglas globales como para profesionales.
"""

def ejecutar_diagnostico_hard(empleados, codigos_reglas, resolver_con_parametros_cb, ajustes_reglas=None) -> dict:
    """Ejecuta el diagnóstico de inviabilidad matemática.

    Partiendo de un escenario simplificado, activa secuencialmente las reglas globales
    y las restricciones del personal (licencias, reglas, ajustes) para detectar de forma
    precisa qué elementos o combinaciones de elementos causan la imposibilidad matemática.
    """
    print("\n" + "="*75, flush=True)
    print("  [DEBUG HARD] INICIANDO DIAGNÓSTICO DE INVIABILIDAD MATEMÁTICA", flush=True)
    print("  Ejecutando algoritmo de encendido progresivo...", flush=True)
    print("="*75 + "\n", flush=True)

    todos_nombres = {e.nombre for e in empleados}
    ajustes_reglas = ajustes_reglas or {}
    
    # Estructura del reporte
    reporte_conflictos = {
        "reglas_globales_cuello_botella": [],    # Reglas globales que causan conflicto individualmente
        "colisiones_globales_dobles": [],        # Parejas de reglas globales que colisionan entre sí
        "empleados_cuello_botella": [],          # Empleados que causan conflicto individualmente (y la causa)
        "colisiones_empleado_empleado": [],      # Parejas de empleados cuyas restricciones colisionan
        "colisiones_regla_empleado": [],         # Parejas (Regla Global, Empleado) que colisionan
        "sistemico_capacidad": False,            # Si es inviable incluso sin ninguna restricción
        "etapa_a_personal": [],                  # Para compatibilidad
        "etapa_b_hard_globales": [],             # Para compatibilidad
    }

    # Helper para formatear los detalles de un ajuste
    def obtener_descripcion_ajuste(emp_nombre, idx):
        if emp_nombre not in ajustes_reglas or idx >= len(ajustes_reglas[emp_nombre]):
            return f"Ajuste #{idx}"
        aj = ajustes_reglas[emp_nombre][idx]
        cod = aj.get('codigo_regla', 'AJUSTE')
        fi = aj.get('fecha_inicio', '?')
        ff = aj.get('fecha_fin', '?')
        acc = aj.get('accion', 'SOBRESCRIBIR')
        return f"{cod} ({fi} a {ff})"

    # -------------------------------------------------------------------------
    # PASO 0: Diagnóstico Sistémico de Capacidad
    # -------------------------------------------------------------------------
    print("  [Paso 0] Evaluando viabilidad física básica (sin reglas globales ni restricciones de personal)...", flush=True)
    viable_capacidad = resolver_con_parametros_cb(
        excluir_reglas=codigos_reglas,
        sin_licencias_de=todos_nombres,
        sin_reglas_de=todos_nombres,
        sin_ajustes_de=todos_nombres
    )
    if not viable_capacidad:
        print("    --> [DIAGNÓSTICO CRÍTICO] El modelo sigue siendo INVIABLE incluso sin reglas globales,", flush=True)
        print("        licencias, ni restricciones de personal. Hay un déficit de capacidad fundamental.", flush=True)
        reporte_conflictos["sistemico_capacidad"] = True
        print("\n" + "="*75 + "\n", flush=True)
        return reporte_conflictos

    # -------------------------------------------------------------------------
    # PASO 1: Diagnóstico con Datos de Personal Puros (Sin Reglas Globales)
    # -------------------------------------------------------------------------
    print("\n  [Paso 1] Evaluando viabilidad con datos de personal reales (sin reglas globales)...", flush=True)
    viable_personal_puro = resolver_con_parametros_cb(
        excluir_reglas=codigos_reglas, # Sin reglas globales
        sin_licencias_de=set(),        # Todas las licencias de todos activas
        sin_reglas_de=set(),           # Todas las reglas individuales de todos activas
        sin_ajustes_de=set()           # Todos los ajustes de todos activos
    )
    
    if not viable_personal_puro:
        print("    --> [Inviabilidad de Personal] El modelo es inviable con los datos del personal (sin reglas globales).", flush=True)
        print("        Analizando colisiones en restricciones de profesionales (licencias/reglas/ajustes)...", flush=True)
        
        # Filtrar empleados con alguna restricción
        empleados_con_restricciones = []
        for e in empleados:
            tiene_lic = len(e.dias_licencia) > 0
            tiene_reg = len(e.reglas) > 0
            tiene_ajust = len(ajustes_reglas.get(e.nombre, [])) > 0
            if tiene_lic or tiene_reg or tiene_ajust or e.rol != "Rotativo":
                empleados_con_restricciones.append(e)
                
        if not empleados_con_restricciones:
            empleados_con_restricciones = list(empleados)
            
        nombres_con_restricciones = {e.nombre for e in empleados_con_restricciones}
        empleados_encendidos = []
        
        for emp in empleados_con_restricciones:
            intentar_encender = empleados_encendidos + [emp.nombre]
            nombres_a_apagar = nombres_con_restricciones - set(intentar_encender)
            
            viable = resolver_con_parametros_cb(
                excluir_reglas=codigos_reglas,
                sin_licencias_de=nombres_a_apagar,
                sin_reglas_de=nombres_a_apagar,
                sin_ajustes_de=nombres_a_apagar
            )
            
            if viable:
                empleados_encendidos.append(emp.nombre)
            else:
                print(f"    --> [Conflicto] Activar restricciones de '{emp.nombre}' produce inviabilidad.", flush=True)
                
                # Probar si es inviable él solo (con todos los demás apagados)
                viable_solo = resolver_con_parametros_cb(
                    excluir_reglas=codigos_reglas,
                    sin_licencias_de=todos_nombres - {emp.nombre},
                    sin_reglas_de=todos_nombres - {emp.nombre},
                    sin_ajustes_de=todos_nombres - {emp.nombre}
                )
                
                if not viable_solo:
                    print(f"      * El profesional '{emp.nombre}' es inviable por sí solo.", flush=True)
                    
                    # Micro-diagnóstico de las restricciones de emp
                    # 1. Probar sin licencias
                    v_sin_lic = resolver_con_parametros_cb(
                        excluir_reglas=codigos_reglas,
                        sin_licencias_de=todos_nombres, # Solo se apagan las suyas (y las de los demas ya estan apagadas)
                        sin_reglas_de=todos_nombres - {emp.nombre},
                        sin_ajustes_de=todos_nombres - {emp.nombre}
                    )
                    if v_sin_lic:
                        print(f"        -> Aislamiento: Desactivar sus LICENCIAS resuelve el conflicto.", flush=True)
                        reporte_conflictos["empleados_cuello_botella"].append((emp.nombre, "LICENCIAS"))
                        reporte_conflictos["etapa_a_personal"].append((emp.nombre, "LICENCIAS"))
                    
                    # 2. Probar sin reglas individuales
                    v_sin_reg = resolver_con_parametros_cb(
                        excluir_reglas=codigos_reglas,
                        sin_licencias_de=todos_nombres - {emp.nombre},
                        sin_reglas_de=todos_nombres,
                        sin_ajustes_de=todos_nombres - {emp.nombre}
                    )
                    if v_sin_reg:
                        print(f"        -> Aislamiento: Desactivar sus REGLAS individuales resuelve el conflicto.", flush=True)
                        reporte_conflictos["empleados_cuello_botella"].append((emp.nombre, "REGLAS_INDIVIDUALES"))
                        reporte_conflictos["etapa_a_personal"].append((emp.nombre, "REGLAS_INDIVIDUALES"))
                        
                    # 3. Micro-diagnóstico de ajustes individuales de emp
                    lista_ajustes = ajustes_reglas.get(emp.nombre, [])
                    if lista_ajustes:
                        print(f"        -> Evaluando {len(lista_ajustes)} ajustes individuales...", flush=True)
                        for idx in range(len(lista_ajustes)):
                            # Desactivamos solo el ajuste idx
                            v_sin_ajuste_idx = resolver_con_parametros_cb(
                                excluir_reglas=codigos_reglas,
                                sin_licencias_de=todos_nombres - {emp.nombre},
                                sin_reglas_de=todos_nombres - {emp.nombre},
                                sin_ajustes_de=todos_nombres - {emp.nombre},
                                sin_ajustes_especificos={emp.nombre: {idx}}
                            )
                            if v_sin_ajuste_idx:
                                desc = obtener_descripcion_ajuste(emp.nombre, idx)
                                print(f"        -> [AJUSTE CULPABLE] Desactivar el ajuste {desc} resuelve el conflicto.", flush=True)
                                reporte_conflictos["empleados_cuello_botella"].append((emp.nombre, f"AJUSTE: {desc}"))
                                reporte_conflictos["etapa_a_personal"].append((emp.nombre, f"AJUSTE_{idx}"))
                else:
                    # Choca en combinación con otros. Buscamos con quién colisiona de los ya encendidos.
                    colisiono_emp = False
                    for anterior_nombre in empleados_encendidos:
                        # Para testear si colisiona con anterior_nombre, los encendemos a ambos y apagamos al resto
                        apagar_para_test = todos_nombres - {emp.nombre, anterior_nombre}
                        v_test = resolver_con_parametros_cb(
                            excluir_reglas=codigos_reglas,
                            sin_licencias_de=apagar_para_test,
                            sin_reglas_de=apagar_para_test,
                            sin_ajustes_de=apagar_para_test
                        )
                        if not v_test:
                            print(f"      * Colisión de personal detectada: '{emp.nombre}' <=> '{anterior_nombre}'", flush=True)
                            reporte_conflictos["colisiones_empleado_empleado"].append((emp.nombre, anterior_nombre))
                            reporte_conflictos["etapa_a_personal"].append((emp.nombre, f"COLISION_CON_{anterior_nombre}"))
                            colisiono_emp = True
                    
                    if not colisiono_emp:
                        print(f"      * Las restricciones de '{emp.nombre}' colisionan con el conjunto acumulado anterior.", flush=True)
                        reporte_conflictos["empleados_cuello_botella"].append((emp.nombre, "COLISION_MULTIPLE_PERSONAL"))
                        reporte_conflictos["etapa_a_personal"].append((emp.nombre, "COLISION_MULTIPLE_PERSONAL"))
        
        # Reportar y terminar ya que el personal por sí solo es inviable
        print("\n" + "="*75, flush=True)
        print("  [DEBUG HARD] RESUMEN DE CONFLICTOS DETECTADOS (PASO 1)", flush=True)
        print("="*75, flush=True)
        for emp, causa in reporte_conflictos["empleados_cuello_botella"]:
            print(f"    -> Profesional: {emp} | Causa: {causa}", flush=True)
        for emp_a, emp_b in reporte_conflictos["colisiones_empleado_empleado"]:
            print(f"    -> Colisión: Profesional '{emp_a}' <=> Profesional '{emp_b}'", flush=True)
        print("\n" + "="*75 + "\n", flush=True)
        return reporte_conflictos

    # -------------------------------------------------------------------------
    # PASO 2: Diagnóstico de Reglas Globales (Con Plantilla de Personal Activa)
    # -------------------------------------------------------------------------
    print("\n  [Paso 2] Analizando colisiones en reglas globales con plantilla activa...", flush=True)
    
    reglas_ordenadas = sorted(codigos_reglas)
    reglas_viables_acumuladas = []
    reglas_conflictivas = []
    
    # 2.1 Encendido progresivo y descarte
    for reg_cod in reglas_ordenadas:
        intentar_encender = reglas_viables_acumuladas + [reg_cod]
        reglas_a_excluir = set(reglas_ordenadas) - set(intentar_encender)
        
        viable = resolver_con_parametros_cb(
            excluir_reglas=reglas_a_excluir,
            sin_licencias_de=set(),
            sin_reglas_de=set(),
            sin_ajustes_de=set()
        )
        
        if viable:
            reglas_viables_acumuladas.append(reg_cod)
        else:
            print(f"    --> [Regla Conflictiva] Activar la regla global '{reg_cod}' produce inviabilidad.", flush=True)
            reglas_conflictivas.append(reg_cod)
            # Se deja apagada la regla conflictiva y se continúa
            
    # 2.2 Diagnóstico individual de cada regla conflictiva R
    for reg_cod in reglas_conflictivas:
        print(f"\n    [Diagnóstico Regla] Analizando causa raíz de '{reg_cod}'...", flush=True)
        
        # Evaluar encendiendo ÚNICAMENTE la regla R
        reglas_a_excluir_solo_R = set(reglas_ordenadas) - {reg_cod}
        viable_solo_R = resolver_con_parametros_cb(
            excluir_reglas=reglas_a_excluir_solo_R,
            sin_licencias_de=set(),
            sin_reglas_de=set(),
            sin_ajustes_de=set()
        )
        
        if not viable_solo_R:
            # Caso 2.2.1: Inviable sola. Choca directamente con las restricciones del personal real.
            print(f"      * La regla '{reg_cod}' es inviable por sí sola con los datos de personal.", flush=True)
            
            # Buscamos qué profesional causa el choque con R.
            # Apagamos todas las restricciones de personal.
            # Vamos encendiendo a los profesionales de a uno.
            empleados_con_restricciones = []
            for e in empleados:
                tiene_lic = len(e.dias_licencia) > 0
                tiene_reg = len(e.reglas) > 0
                tiene_ajust = len(ajustes_reglas.get(e.nombre, [])) > 0
                if tiene_lic or tiene_reg or tiene_ajust or e.rol != "Rotativo":
                    empleados_con_restricciones.append(e)
            if not empleados_con_restricciones:
                empleados_con_restricciones = list(empleados)
                
            nombres_con_restricciones = {e.nombre for e in empleados_con_restricciones}
            empleados_encendidos_R = []
            
            for emp in empleados_con_restricciones:
                intentar_encender = empleados_encendidos_R + [emp.nombre]
                nombres_a_apagar = nombres_con_restricciones - set(intentar_encender)
                
                viable_test_emp = resolver_con_parametros_cb(
                    excluir_reglas=reglas_a_excluir_solo_R,
                    sin_licencias_de=nombres_a_apagar,
                    sin_reglas_de=nombres_a_apagar,
                    sin_ajustes_de=nombres_a_apagar
                )
                
                if viable_test_emp:
                    empleados_encendidos_R.append(emp.nombre)
                else:
                    # El empleado emp hace inviable a R.
                    print(f"      --> [Colisión Regla-Personal] La regla '{reg_cod}' colisiona con las restricciones de '{emp.nombre}'", flush=True)
                    reporte_conflictos["colisiones_regla_empleado"].append((reg_cod, emp.nombre))
                    
                    # Micro-diagnóstico dentro de emp para R:
                    # 1. Probar sin licencias
                    v_sin_lic = resolver_con_parametros_cb(
                        excluir_reglas=reglas_a_excluir_solo_R,
                        sin_licencias_de=nombres_a_apagar | {emp.nombre},
                        sin_reglas_de=nombres_a_apagar,
                        sin_ajustes_de=nombres_a_apagar
                    )
                    if v_sin_lic:
                        print(f"        -> Aislamiento: Desactivar LICENCIAS de '{emp.nombre}' resuelve el choque con '{reg_cod}'", flush=True)
                        reporte_conflictos["empleados_cuello_botella"].append((emp.nombre, f"LICENCIAS en conflicto con {reg_cod}"))
                    
                    # 2. Probar sin reglas individuales
                    v_sin_reg = resolver_con_parametros_cb(
                        excluir_reglas=reglas_a_excluir_solo_R,
                        sin_licencias_de=nombres_a_apagar,
                        sin_reglas_de=nombres_a_apagar | {emp.nombre},
                        sin_ajustes_de=nombres_a_apagar
                    )
                    if v_sin_reg:
                        print(f"        -> Aislamiento: Desactivar REGLAS individuales de '{emp.nombre}' resuelve el choque con '{reg_cod}'", flush=True)
                        reporte_conflictos["empleados_cuello_botella"].append((emp.nombre, f"REGLAS_INDIVIDUALES en conflicto con {reg_cod}"))
                    
                    # 3. Probar sin ajustes individuales (Micro-diagnóstico)
                    lista_aj = ajustes_reglas.get(emp.nombre, [])
                    if lista_aj:
                        for idx in range(len(lista_aj)):
                            v_sin_aj_idx = resolver_con_parametros_cb(
                                excluir_reglas=reglas_a_excluir_solo_R,
                                sin_licencias_de=nombres_a_apagar,
                                sin_reglas_de=nombres_a_apagar,
                                sin_ajustes_de=nombres_a_apagar,
                                sin_ajustes_especificos={emp.nombre: {idx}}
                            )
                            if v_sin_aj_idx:
                                desc = obtener_descripcion_ajuste(emp.nombre, idx)
                                print(f"        -> [AJUSTE CULPABLE] Desactivar el ajuste {desc} resuelve el choque con '{reg_cod}'", flush=True)
                                reporte_conflictos["empleados_cuello_botella"].append((emp.nombre, f"AJUSTE: {desc} en conflicto con {reg_cod}"))
                                
                    # Dejamos apagado a emp para continuar evaluando otros empleados que puedan colisionar con R
        else:
            # Caso 2.2.2: Viable sola. Colisiona en combinación con otras reglas.
            print(f"      * La regla '{reg_cod}' es viable por sí sola. Buscando colisión multifactorial...", flush=True)
            
            # Vamos encendiendo una a una las reglas viables acumuladas hasta que quiebre
            reglas_acumuladas_test = [reg_cod]
            for viable_reg in reglas_viables_acumuladas:
                intentar_encender_test = reglas_acumuladas_test + [viable_reg]
                reglas_a_excluir_test = set(reglas_ordenadas) - set(intentar_encender_test)
                
                v_test_comb = resolver_con_parametros_cb(
                    excluir_reglas=reglas_a_excluir_test,
                    sin_licencias_de=set(),
                    sin_reglas_de=set(),
                    sin_ajustes_de=set()
                )
                
                if not v_test_comb:
                    print(f"      --> [Colisión entre Reglas] Colisión mutua detectada: '{reg_cod}' <=> '{viable_reg}'", flush=True)
                    reporte_conflictos["colisiones_globales_dobles"].append((reg_cod, viable_reg))
                    reporte_conflictos["etapa_b_hard_globales"].append((reg_cod, f"COLISION_CON_{viable_reg}"))
                    
                    # Verificamos si la colisión es sistémica o catalizada por el personal
                    v_sin_personal = resolver_con_parametros_cb(
                        excluir_reglas=reglas_a_excluir_test,
                        sin_licencias_de=todos_nombres,
                        sin_reglas_de=todos_nombres,
                        sin_ajustes_de=todos_nombres
                    )
                    
                    if v_sin_personal:
                        print(f"      --> [Aislamiento] La colisión no es sistémica, es catalizada por restricciones del personal. Buscando profesionales en colisión...", flush=True)
                        
                        empleados_con_restricciones = []
                        for e in empleados:
                            tiene_lic = len(e.dias_licencia) > 0
                            tiene_reg = len(e.reglas) > 0
                            tiene_ajust = len(ajustes_reglas.get(e.nombre, [])) > 0
                            if tiene_lic or tiene_reg or tiene_ajust or e.rol != "Rotativo":
                                empleados_con_restricciones.append(e)
                        if not empleados_con_restricciones:
                            empleados_con_restricciones = list(empleados)
                            
                        nombres_con_restricciones = {e.nombre for e in empleados_con_restricciones}
                        empleados_encendidos_comb = []
                        
                        for emp in empleados_con_restricciones:
                            intentar_encender_c = empleados_encendidos_comb + [emp.nombre]
                            nombres_a_apagar_c = nombres_con_restricciones - set(intentar_encender_c)
                            
                            v_test_emp = resolver_con_parametros_cb(
                                excluir_reglas=reglas_a_excluir_test,
                                sin_licencias_de=nombres_a_apagar_c,
                                sin_reglas_de=nombres_a_apagar_c,
                                sin_ajustes_de=nombres_a_apagar_c
                            )
                            
                            if v_test_emp:
                                empleados_encendidos_comb.append(emp.nombre)
                            else:
                                print(f"        -> Colisión catalizada por restricciones de '{emp.nombre}'", flush=True)
                                reporte_conflictos["colisiones_regla_empleado"].append((f"{reg_cod}+{viable_reg}", emp.nombre))
                                
                                # Micro-diagnóstico dentro de emp para la combinación:
                                # 1. Probar sin licencias
                                v_sin_lic_c = resolver_con_parametros_cb(
                                    excluir_reglas=reglas_a_excluir_test,
                                    sin_licencias_de=nombres_a_apagar_c | {emp.nombre},
                                    sin_reglas_de=nombres_a_apagar_c,
                                    sin_ajustes_de=nombres_a_apagar_c
                                )
                                if v_sin_lic_c:
                                    print(f"          -> Aislamiento: Desactivar LICENCIAS de '{emp.nombre}' resuelve el choque.", flush=True)
                                    reporte_conflictos["empleados_cuello_botella"].append((emp.nombre, f"LICENCIAS en conflicto con {reg_cod}+{viable_reg}"))
                                
                                # 2. Probar sin reglas individuales
                                v_sin_reg_c = resolver_con_parametros_cb(
                                    excluir_reglas=reglas_a_excluir_test,
                                    sin_licencias_de=nombres_a_apagar_c,
                                    sin_reglas_de=nombres_a_apagar_c | {emp.nombre},
                                    sin_ajustes_de=nombres_a_apagar_c
                                )
                                if v_sin_reg_c:
                                    print(f"          -> Aislamiento: Desactivar REGLAS individuales de '{emp.nombre}' resuelve el choque.", flush=True)
                                    reporte_conflictos["empleados_cuello_botella"].append((emp.nombre, f"REGLAS_INDIVIDUALES en conflicto con {reg_cod}+{viable_reg}"))
                                
                                # 3. Probar sin ajustes individuales (Micro-diagnóstico)
                                lista_aj = ajustes_reglas.get(emp.nombre, [])
                                if lista_aj:
                                    for idx in range(len(lista_aj)):
                                        v_sin_aj_idx_c = resolver_con_parametros_cb(
                                            excluir_reglas=reglas_a_excluir_test,
                                            sin_licencias_de=nombres_a_apagar_c,
                                            sin_reglas_de=nombres_a_apagar_c,
                                            sin_ajustes_de=nombres_a_apagar_c,
                                            sin_ajustes_especificos={emp.nombre: {idx}}
                                        )
                                        if v_sin_aj_idx_c:
                                            desc = obtener_descripcion_ajuste(emp.nombre, idx)
                                            print(f"          -> [AJUSTE CULPABLE] Desactivar el ajuste {desc} resuelve el choque.", flush=True)
                                            reporte_conflictos["empleados_cuello_botella"].append((emp.nombre, f"AJUSTE: {desc} en conflicto con {reg_cod}+{viable_reg}"))
                    break
                else:
                    reglas_acumuladas_test.append(viable_reg)

    # -------------------------------------------------------------------------
    # REPORTE FINAL CONSOLIDADO EN CONSOLA
    # -------------------------------------------------------------------------
    print("\n" + "="*75, flush=True)
    print("  [DEBUG HARD] RESUMEN DE CONFLICTOS DETECTADOS", flush=True)
    print("="*75, flush=True)

    encontrado = False

    if reporte_conflictos["sistemico_capacidad"]:
        print("  [DIAGNÓSTICO SISTÉMICO] La demanda de cobertura supera la disponibilidad física básica del plantel.", flush=True)
        print("  Revisar la demanda mínima requerida o habilitar más personal.", flush=True)
        encontrado = True

    if reporte_conflictos["reglas_globales_cuello_botella"]:
        print("  [REGLAS GLOBALES CULPABLES] Reglas que al activarse bloquean la viabilidad por completo:", flush=True)
        for reg in reporte_conflictos["reglas_globales_cuello_botella"]:
            print(f"    -> Regla Global: {reg}", flush=True)
        encontrado = True

    if reporte_conflictos["colisiones_globales_dobles"]:
        print("  [COLISIONES ENTRE REGLAS] Parejas de reglas globales que colisionan entre sí (incompatibilidad mutua):", flush=True)
        for reg_a, reg_b in reporte_conflictos["colisiones_globales_dobles"]:
            print(f"    -> Regla '{reg_a}' <=> Regla '{reg_b}'", flush=True)
        encontrado = True

    if reporte_conflictos["empleados_cuello_botella"]:
        print("  [PROFESIONALES CONFLICTIVOS] Restricciones individuales que impiden la viabilidad:", flush=True)
        for emp, causa in reporte_conflictos["empleados_cuello_botella"]:
            print(f"    -> Profesional: {emp} | Causa identificada: {causa}", flush=True)
        encontrado = True

    if reporte_conflictos["colisiones_empleado_empleado"]:
        print("  [COLISIONES ENTRE PROFESIONALES] Restricciones de profesionales que colisionan mutuamente (ej: licencias simultáneas):", flush=True)
        for emp_a, emp_b in reporte_conflictos["colisiones_empleado_empleado"]:
            print(f"    -> Profesional '{emp_a}' <=> Profesional '{emp_b}'", flush=True)
        encontrado = True

    if reporte_conflictos["colisiones_regla_empleado"]:
        print("  [COLISIONES REGLA-PROFESIONAL] Restricciones de un profesional que chocan con una regla global:", flush=True)
        for reg, emp in reporte_conflictos["colisiones_regla_empleado"]:
            print(f"    -> Regla '{reg}' colisiona con las restricciones de '{emp}'", flush=True)
        encontrado = True

    if not encontrado:
        print("  No se identificó un único culpable de forma aislada.", flush=True)
        print("  El conflicto puede involucrar interacciones complejas de múltiples componentes.", flush=True)
        print("  Se recomienda usar el modo de relajación Debug Soft (--debug-soft) para ver infracciones ponderadas.", flush=True)

    print("\n" + "="*75 + "\n", flush=True)
    return reporte_conflictos

"""
restricciones/debug_hard.py — Diagnóstico matemático iterativo (Modo Debug Hard).

Aísla conflictos matemáticos de inviabilidad mediante un flujo de decisiones
lógicas de encendido progresivo (búsqueda incremental de colisiones)
tanto para reglas globales como para profesionales.
"""

def ejecutar_diagnostico_hard(empleados, codigos_reglas, resolver_con_parametros_cb) -> dict:
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
    
    # Estructura del reporte
    reporte_conflictos = {
        "reglas_globales_cuello_botella": [],    # Reglas globales que causan conflicto individualmente
        "colisiones_globales_dobles": [],        # Parejas de reglas globales que colisionan entre sí
        "empleados_cuello_botella": [],          # Empleados que causan conflicto individualmente
        "colisiones_empleado_empleado": [],      # Parejas de empleados cuyas restricciones colisionan
        "colisiones_regla_empleado": [],         # Parejas (Regla Global, Empleado) que colisionan
        "sistemico_capacidad": False,            # Si es inviable incluso sin ninguna restricción
        # Llaves legacy para mantener compatibilidad
        "etapa_a_personal": [],
        "etapa_b_hard_globales": [],
    }

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
    # PASO 1: Diagnóstico de Reglas Globales (Encendido Progresivo)
    # -------------------------------------------------------------------------
    print("\n  [Paso 1] Analizando colisiones en reglas globales...", flush=True)
    
    reglas_ordenadas = sorted(codigos_reglas)
    reglas_encendidas = []
    
    # Evaluamos con todas las restricciones de personal apagadas para aislar lógica global
    for reg_cod in reglas_ordenadas:
        intentar_encender = reglas_encendidas + [reg_cod]
        reglas_a_excluir = set(reglas_ordenadas) - set(intentar_encender)
        
        viable = resolver_con_parametros_cb(
            excluir_reglas=reglas_a_excluir,
            sin_licencias_de=todos_nombres,
            sin_reglas_de=todos_nombres,
            sin_ajustes_de=todos_nombres
        )
        
        if viable:
            reglas_encendidas.append(reg_cod)
        else:
            print(f"    --> [Conflicto] Activar la regla global '{reg_cod}' produce inviabilidad.", flush=True)
            
            # Buscamos con cuál de las ya encendidas colisiona (apagando una por una de las anteriores)
            colisiono = False
            for anterior in reglas_encendidas:
                excluir_para_test = (set(reglas_ordenadas) - set(intentar_encender)) | {anterior}
                v_test = resolver_con_parametros_cb(
                    excluir_reglas=excluir_para_test,
                    sin_licencias_de=todos_nombres,
                    sin_reglas_de=todos_nombres,
                    sin_ajustes_de=todos_nombres
                )
                if v_test:
                    print(f"      * Colisión mutua detectada: '{reg_cod}' <=> '{anterior}'", flush=True)
                    reporte_conflictos["colisiones_globales_dobles"].append((reg_cod, anterior))
                    reporte_conflictos["etapa_b_hard_globales"].append((reg_cod, f"COLISION_CON_{anterior}"))
                    colisiono = True
            
            if not colisiono:
                print(f"      * La regla '{reg_cod}' colisiona con el conjunto de reglas anteriores: {reglas_encendidas}", flush=True)
                reporte_conflictos["reglas_globales_cuello_botella"].append(reg_cod)
                reporte_conflictos["etapa_b_hard_globales"].append((reg_cod, "CUELLO_BOTELLA_GLOBAL"))

    # -------------------------------------------------------------------------
    # PASO 2: Diagnóstico de Restricciones de Personal (Encendido Progresivo)
    # -------------------------------------------------------------------------
    print("\n  [Paso 2] Analizando colisiones en restricciones de profesionales (licencias/reglas/ajustes)...", flush=True)
    
    # Optimización: Solo evaluamos profesionales que tienen alguna restricción activa en el mes.
    # Los que no tienen licencias, reglas individuales ni ajustes actúan siempre libres y no colisionan de forma aislada.
    import sys
    # Accedemos a los ajustes de reglas de personal a través del callback si es necesario, o lo leemos directamente
    # desde la configuración del contexto en el orquestador.
    # Evaluamos qué empleados tienen licencias o reglas especiales:
    empleados_con_restricciones = []
    for e in empleados:
        tiene_licencias = len(e.dias_licencia) > 0
        tiene_reglas = len(e.reglas) > 0
        # Revisamos si tiene algún ajuste en el mes
        # Como no tenemos acceso directo al objeto ctx, podemos asumir que tiene restricciones si tiene licencias o reglas.
        # Adicionalmente, incluimos a todos por si las dudas, pero si podemos filtrar mejor es ideal.
        # Para ser totalmente seguros pero eficientes, consideramos a cualquiera con licencias, reglas, o que no sea un rotativo estándar sin licencias.
        if tiene_licencias or tiene_reglas or e.rol != "Rotativo":
            empleados_con_restricciones.append(e)
            
    if not empleados_con_restricciones:
        empleados_con_restricciones = list(empleados)
        
    nombres_con_restricciones = {e.nombre for e in empleados_con_restricciones}
    empleados_encendidos = []
    
    # Manteniendo las reglas globales encendidas (a menos que se hayan excluido),
    # encendemos uno a uno los profesionales con restricciones para ver quién quiebra el modelo.
    for emp in empleados_con_restricciones:
        intentar_encender = empleados_encendidos + [emp.nombre]
        nombres_a_apagar = nombres_con_restricciones - set(intentar_encender)
        
        viable = resolver_con_parametros_cb(
            sin_licencias_de=nombres_a_apagar,
            sin_reglas_de=nombres_a_apagar,
            sin_ajustes_de=nombres_a_apagar
        )
        
        if viable:
            empleados_encendidos.append(emp.nombre)
        else:
            print(f"    --> [Conflicto] Encender las restricciones de '{emp.nombre}' produce inviabilidad.", flush=True)
            
            # Buscamos si colisiona con algún profesional ya encendido (apagando uno por uno los anteriores)
            colisiono_emp = False
            for anterior_nombre in empleados_encendidos:
                apagar_para_test = nombres_a_apagar | {anterior_nombre}
                v_test = resolver_con_parametros_cb(
                    sin_licencias_de=apagar_para_test,
                    sin_reglas_de=apagar_para_test,
                    sin_ajustes_de=apagar_para_test
                )
                if v_test:
                    print(f"      * Colisión de personal detectada: '{emp.nombre}' <=> '{anterior_nombre}'", flush=True)
                    reporte_conflictos["colisiones_empleado_empleado"].append((emp.nombre, anterior_nombre))
                    reporte_conflictos["etapa_a_personal"].append((emp.nombre, f"COLISION_CON_{anterior_nombre}"))
                    colisiono_emp = True
            
            if not colisiono_emp:
                # Si no colisiona con otro empleado, colisiona con las reglas globales o la demanda
                print(f"      * Las restricciones de '{emp.nombre}' colisionan directamente con las reglas globales o demanda base.", flush=True)
                
                # Buscamos con cuál regla global específica colisiona
                for reg_cod in sorted(codigos_reglas):
                    v_reg_test = resolver_con_parametros_cb(
                        excluir_reglas={reg_cod},
                        sin_licencias_de=nombres_a_apagar,
                        sin_reglas_de=nombres_a_apagar,
                        sin_ajustes_de=nombres_a_apagar
                    )
                    if v_reg_test:
                        print(f"        -> [Colisión Regla-Personal] Colisiona con la regla global: '{reg_cod}'", flush=True)
                        reporte_conflictos["colisiones_regla_empleado"].append((reg_cod, emp.nombre))
                        
                # Aislamiento dentro del profesional (Licencias, Reglas o Ajustes)
                # 1. Probar desactivando sus LICENCIAS
                v_sin_licencia = resolver_con_parametros_cb(
                    sin_licencias_de=nombres_a_apagar | {emp.nombre},
                    sin_reglas_de=nombres_a_apagar,
                    sin_ajustes_de=nombres_a_apagar
                )
                if v_sin_licencia:
                    print(f"        -> Aislamiento: Desactivar sus LICENCIAS resuelve el conflicto.", flush=True)
                    reporte_conflictos["empleados_cuello_botella"].append((emp.nombre, "LICENCIAS"))
                    reporte_conflictos["etapa_a_personal"].append((emp.nombre, "LICENCIAS"))
                
                # 2. Probar desactivando sus AJUSTES
                v_sin_ajuste = resolver_con_parametros_cb(
                    sin_licencias_de=nombres_a_apagar,
                    sin_reglas_de=nombres_a_apagar,
                    sin_ajustes_de=nombres_a_apagar | {emp.nombre}
                )
                if v_sin_ajuste:
                    print(f"        -> Aislamiento: Desactivar sus AJUSTES de regla resuelve el conflicto.", flush=True)
                    reporte_conflictos["empleados_cuello_botella"].append((emp.nombre, "AJUSTES_PERSONAL"))
                    reporte_conflictos["etapa_a_personal"].append((emp.nombre, "AJUSTES_PERSONAL"))
                
                # 3. Probar desactivando sus REGLAS individuales
                if emp.reglas:
                    for reg_ind in sorted(emp.reglas.keys()):
                        v_sin_reg_ind = resolver_con_parametros_cb(
                            sin_licencias_de=nombres_a_apagar,
                            sin_reglas_de=nombres_a_apagar,
                            sin_ajustes_de=nombres_a_apagar,
                            exclusiones_adicionales={(reg_ind, emp.nombre)}
                        )
                        if v_sin_reg_ind:
                            print(f"        -> Aislamiento: Desactivar su regla individual '{reg_ind}' resuelve el conflicto.", flush=True)
                            reporte_conflictos["empleados_cuello_botella"].append((emp.nombre, f"REGLA_{reg_ind}"))
                            reporte_conflictos["etapa_a_personal"].append((emp.nombre, f"REGLA_{reg_ind}"))

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
        print("  [PROFESIONALES CONFLICTIVOS] Profesionales cuyas restricciones individuales impiden la viabilidad:", flush=True)
        for emp, causa in reporte_conflictos["empleados_cuello_botella"]:
            print(f"    -> Profesional: {emp} | Causa identificada: {causa}", flush=True)
        encontrado = True

    if reporte_conflictos["colisiones_empleado_empleado"]:
        print("  [COLISIONES ENTRE PROFESIONALES] Profesionales cuyas restricciones colisionan mutuamente (ej: licencias simultáneas):", flush=True)
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

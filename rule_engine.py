"""
rule_engine.py — Motor centralizado de resolución de reglas.

Implementa la jerarquía de prioridad:
  1. personal_reglas_ajustes (ajuste temporal por persona y período)  ← mayor prioridad
  2. personal_reglas           (regla fija por persona)
  3. servicios_reglas          (regla del sector/servicio)
  4. organizaciones_reglas     (regla de la institución)              ← menor prioridad

Las reglas de servicio y organización ya vienen pre-fusionadas en el dict
`reglas_servicio` que devuelve db.cargar_reglas_servicio() (el servicio
sobrescribe a la organización). Por eso esta jerarquía queda en la práctica:

  ajuste_personal_temporal > personal > servicio_o_rganizacion
"""


def resolver_parametros_regla(
    codigo_regla,
    nombre,
    fecha_str,
    reglas_servicio,
    reglas_personal,
    ajustes_personal,
):
    """
    Resuelve los parámetros activos para una regla, para una persona en una fecha.

    Args:
        codigo_regla    (str):  Ej. 'MAX_HORAS_SEMANA', 'EXCLUIR_TURNOS', etc.
        nombre          (str):  Nombre del profesional.
        fecha_str       (str):  Fecha de referencia ISO 8601 (ej. '2026-06-02').
        reglas_servicio (dict): Resultado de db.cargar_reglas_servicio().
        reglas_personal (dict): Resultado de db.cargar_reglas_personal().
        ajustes_personal(dict): Resultado de db.cargar_ajustes_reglas_personal().

    Returns:
        dict  — parámetros activos (puede ser {} si la regla existe sin params).
        None  — la regla está SUSPENDIDA para esta persona en esta fecha.
        Raises KeyError si la regla no existe en ningún nivel de la jerarquía
               (para que el llamador decida si es un error o simplemente no aplica).
    """
    # ─── 0. DETECTAR SOLO_ASIGNACIONES_FIJAS ──────────────────────────────────
    # Si el profesional solo hace asignaciones fijas, desactivamos automáticamente
    # cualquier otra regla para evitar colisiones matemáticas (ellos deciden).
    if codigo_regla not in ('SOLO_ASIGNACIONES_FIJAS', 'ASIGNACION_FIJA'):
        saf_activo = False
        # A. Comprobar ajuste temporal
        if ajustes_personal and nombre in ajustes_personal:
            for aj in ajustes_personal[nombre]:
                if aj['codigo_regla'] == 'SOLO_ASIGNACIONES_FIJAS' and aj['fecha_inicio'] <= fecha_str <= aj['fecha_fin']:
                    if aj['accion'] == 'SOBRESCRIBIR':
                        saf_activo = True
                    elif aj['accion'] == 'SUSPENDER':
                        saf_activo = False
                    break
            else:
                # B. Si no hay ajuste, ver si tiene la regla fija cargada
                if reglas_personal and 'SOLO_ASIGNACIONES_FIJAS' in reglas_personal:
                    saf_activo = True
        else:
            # B. Si no hay ajustes de ningún tipo, ver la regla fija
            if reglas_personal and 'SOLO_ASIGNACIONES_FIJAS' in reglas_personal:
                saf_activo = True
                
        if saf_activo:
            return None # Regla suspendida automáticamente

    # ─── 1. AJUSTE TEMPORAL PERSONAL ──────────────────────────────────────────
    # Tiene prioridad absoluta. Si hay un ajuste activo para esta persona y fecha,
    # se aplica sin importar lo que digan las reglas base.
    if ajustes_personal and nombre in ajustes_personal:
        coincidentes = []
        for aj in ajustes_personal[nombre]:
            if aj['codigo_regla'] == codigo_regla and aj['fecha_inicio'] <= fecha_str <= aj['fecha_fin']:
                if aj['accion'] == 'SUSPENDER':
                    return None          # regla completamente desactivada para este período
                if aj['accion'] == 'SOBRESCRIBIR':
                    coincidentes.append(aj['params'])
        if coincidentes:
            if codigo_regla in (
                'EXCLUIR_TURNOS', 'MAX_TURNOS', 'MIN_TURNOS', 'ASIGNACION_FIJA',
                'PENALIZACION_TURNO', 'TURNOS_PREFERENCIALES'
            ):
                combinado = []
                for p in coincidentes:
                    if isinstance(p, list):
                        combinado.extend(p)
                    elif isinstance(p, dict):
                        combinado.append(p)
                return combinado
            else:
                combinado = {}
                for p in coincidentes:
                    if isinstance(p, dict):
                        combinado.update(p)
                return combinado

    # ─── 2. REGLA PERSONAL ────────────────────────────────────────────────────
    # Configuración individual que no tiene límite de tiempo.
    if codigo_regla in reglas_personal:
        valor = reglas_personal[codigo_regla]
        # Si es una lista y la regla espera un dict simple, tomamos el primer elemento
        if isinstance(valor, list) and codigo_regla not in (
            'EXCLUIR_TURNOS', 'MAX_TURNOS', 'MIN_TURNOS', 'ASIGNACION_FIJA',
            'PENALIZACION_TURNO', 'TURNOS_PREFERENCIALES'
        ):
            return valor[0] if len(valor) > 0 else {}
        return valor

    # ─── 3. AJUSTE TEMPORAL SERVICIO ──────────────────────────────────────────
    # Si hay un ajuste activo para el servicio en este período, sobrescribe o suspende.
    if ajustes_personal and '__servicio__' in ajustes_personal:
        ajustes_servicio = ajustes_personal['__servicio__']
        if isinstance(ajustes_servicio, dict) and codigo_regla in ajustes_servicio:
            coincidentes = []
            for aj in ajustes_servicio[codigo_regla]:
                if aj['fecha_inicio'] <= fecha_str <= aj['fecha_fin']:
                    if aj['accion'] == 'SUSPENDER':
                        return None
                    if aj['accion'] == 'SOBRESCRIBIR':
                        coincidentes.append(aj['params'])
            if coincidentes:
                if codigo_regla in (
                    'EXCLUIR_TURNOS', 'MAX_TURNOS', 'MIN_TURNOS', 'ASIGNACION_FIJA',
                    'PENALIZACION_TURNO', 'TURNOS_PREFERENCIALES'
                ):
                    combinado = []
                    for p in coincidentes:
                        if isinstance(p, list):
                            combinado.extend(p)
                        elif isinstance(p, dict):
                            combinado.append(p)
                    return combinado
                else:
                    combinado = {}
                    for p in coincidentes:
                        if isinstance(p, dict):
                            combinado.update(p)
                    return combinado

    # ─── 4. REGLA DE SERVICIO / ORGANIZACIÓN ─────────────────────────────────
    # cargar_reglas_servicio() ya fusiona organización y servicio,
    # con el servicio teniendo mayor prioridad.
    if codigo_regla in reglas_servicio:
        return reglas_servicio[codigo_regla]

    # ─── 5. NO EXISTE EN NINGÚN NIVEL ────────────────────────────────────────
    # Devolvemos un centinela especial para distinguir "suspendida" (None)
    # de "no configurada" (Ellipsis).
    return ...   # Ellipsis: la regla no está definida en ningún nivel


def regla_existe(params):
    """True si resolver_parametros_regla devolvió algo válido (no None ni Ellipsis)."""
    return params is not None and params is not ...


def regla_suspendida(params):
    """True si la regla está suspendida (ya sea por ajuste temporal o por parámetro en el JSON) o no existe."""
    if params is None or params is ...:
        return True
    if isinstance(params, dict) and params.get('suspendida') is True:
        return True
    return False



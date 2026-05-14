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
    # ─── 1. AJUSTE TEMPORAL ───────────────────────────────────────────────────
    # Tiene prioridad absoluta. Si hay un ajuste activo para esta persona y fecha,
    # se aplica sin importar lo que digan las reglas base.
    for aj in ajustes_personal.get(nombre, []):
        if aj['codigo_regla'] == codigo_regla and aj['fecha_inicio'] <= fecha_str <= aj['fecha_fin']:
            if aj['accion'] == 'SUSPENDER':
                return None          # regla completamente desactivada para este período
            if aj['accion'] == 'SOBRESCRIBIR':
                return aj['params'] or {}   # nuevos parámetros para este período

    # ─── 2. REGLA PERSONAL ────────────────────────────────────────────────────
    # Configuración individual que no tiene límite de tiempo.
    # (cargar_reglas_personal devuelve listas; tomamos la primera si aplica)
    if codigo_regla in reglas_personal:
        valor = reglas_personal[codigo_regla]
        # Si la regla personal es una lista de dicts (ej. EXCLUIR_TURNOS), la devolvemos tal cual.
        # Si es un dict simple, también.
        return valor

    # ─── 3. REGLA DE SERVICIO / ORGANIZACIÓN ─────────────────────────────────
    # cargar_reglas_servicio() ya fusiona organización y servicio,
    # con el servicio teniendo mayor prioridad.
    if codigo_regla in reglas_servicio:
        return reglas_servicio[codigo_regla]

    # ─── 4. NO EXISTE EN NINGÚN NIVEL ────────────────────────────────────────
    # Devolvemos un centinela especial para distinguir "suspendida" (None)
    # de "no configurada" (Ellipsis).
    return ...   # Ellipsis: la regla no está definida en ningún nivel


def regla_existe(params):
    """True si resolver_parametros_regla devolvió algo válido (no None ni Ellipsis)."""
    return params is not None and params is not ...


def regla_suspendida(params):
    """True si la regla está suspendida (ya sea por ajuste temporal o por parámetro en el JSON)."""
    if params is None:
        return True
    if isinstance(params, dict) and params.get('suspendida') is True:
        return True
    return False


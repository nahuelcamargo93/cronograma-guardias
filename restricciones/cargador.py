"""
restricciones/cargador.py — Infraestructura de doble red de seguridad.

Tarea 2.2: provee las dos mecánicas del debugger sin que las micro-reglas
repitan código:

  1. ASSUMPTIONS (INFEASIBLE detection):
     Cada regla recibe un BoolVar. Todas sus restricciones se envuelven
     con .OnlyEnforceIf(assumption). Si el solver da INFEASIBLE, se llama
     a reportar_conflicto() para imprimir exactamente qué reglas colapsaron.

  2. MODO_DEBUG (penalización extrema):
     Si ctx.modo_debug=True, add_hard() NO agrega restricciones duras.
     En su lugar, crea un BoolVar de violación y lo penaliza con PESO_DEBUG
     en la función objetivo. El modelo NUNCA dará INFEASIBLE; generará
     un cronograma que muestra visualmente qué regla se sacrificó.

  3. OBJETIVO SOFT UNIFICADO:
     construir_objetivo_soft() ensambla la función objetivo completa a
     partir de ctx.penalizaciones_soft y ctx.bonuses_soft. El orquestador
     la llama UNA VEZ al final, después de ejecutar todas las micro-reglas.

Uso en cada micro-regla hard:
    from restricciones.cargador import add_hard

    def apply(modelo, ctx):
        for emp in ctx.empleados:
            vars_dia = [...]
            add_hard(modelo, ctx,
                     modelo.Add(sum(vars_dia) <= 1),
                     etiqueta=emp.nombre)

Uso en cada micro-regla soft:
    def apply(modelo, ctx):
        # Acumula en ctx.penalizaciones_soft o ctx.bonuses_soft
        ctx.penalizaciones_soft.append(var * peso)
"""

PESO_DEBUG = 10_000_000   # Peso extremo para penalizar violaciones en modo debug


# ---------------------------------------------------------------------------
# API principal
# ---------------------------------------------------------------------------

def preparar_assumption(modelo, ctx, codigo_regla: str, sufijo: str = "") -> object:
    """Crea y registra el BoolVar de assumption para la regla activa."""
    etiqueta = f"{codigo_regla}__{sufijo}" if sufijo else codigo_regla
    nombre_assume = f"REG_{etiqueta}"
    b = modelo.NewBoolVar(nombre_assume)
    ctx.assumptions.append((nombre_assume, b))
    ctx.current_assumption = b
    return b


def add_hard(modelo, ctx, constraint, etiqueta: str = "") -> None:
    """Agrega una restricción dura con soporte automático de debugger."""
    if ctx.codigo_regla:
        if not hasattr(ctx, 'reglas_duras_aplicadas'):
            ctx.reglas_duras_aplicadas = set()
        ctx.reglas_duras_aplicadas.add(ctx.codigo_regla)

    # Comprobar si la regla completa está excluida
    if (ctx.codigo_regla, None) in getattr(ctx, 'exclusiones', set()):
        etiqueta_limpia = etiqueta.replace(" ", "_").replace("-", "_") if etiqueta else ""
        b_excl = modelo.NewBoolVar(f"excl_{ctx.codigo_regla}_{etiqueta_limpia}" if etiqueta_limpia else f"excl_{ctx.codigo_regla}")
        constraint.OnlyEnforceIf(b_excl)
        modelo.Add(b_excl == 0)
        return

    # Comprobar si la regla está excluida para un empleado específico
    if etiqueta:
        for excl_cod, excl_emp in getattr(ctx, 'exclusiones', set()):
            if excl_cod == ctx.codigo_regla and excl_emp is not None:
                emp_formato = excl_emp.replace(" ", "_").replace("-", "_")
                etiqueta_formato = etiqueta.replace(" ", "_").replace("-", "_")
                if emp_formato in etiqueta_formato:
                    b_excl = modelo.NewBoolVar(f"excl_{ctx.codigo_regla}_{etiqueta_formato}")
                    constraint.OnlyEnforceIf(b_excl)
                    modelo.Add(b_excl == 0)
                    return

    # Desactivar restricciones que involucren únicamente variables de días bloqueados
    desactivar_por_bloqueo = False
    try:
        if hasattr(ctx, 'dias_bloqueados') and ctx.dias_bloqueados:
            c_idx = constraint.Index()
            proto = modelo.Proto().constraints[c_idx]
            inds = []
            if proto.enforcement_literal:
                for lit in proto.enforcement_literal:
                    inds.append(lit if lit >= 0 else -lit - 1)
            if proto.has_linear():
                inds.extend(proto.linear.vars)
            elif proto.has_bool_or():
                for lit in proto.bool_or.literals:
                    inds.append(lit if lit >= 0 else -lit - 1)
            elif proto.has_bool_and():
                for lit in proto.bool_and.literals:
                    inds.append(lit if lit >= 0 else -lit - 1)
            elif proto.has_at_most_one():
                for lit in proto.at_most_one.literals:
                    inds.append(lit if lit >= 0 else -lit - 1)
            elif proto.has_exactly_one():
                for lit in proto.exactly_one.literals:
                    inds.append(lit if lit >= 0 else -lit - 1)
            
            inds = list(set(inds))
            
            if inds:
                import re
                todas_bloqueadas = True
                for idx in inds:
                    var_name = modelo.Proto().variables[idx].name
                    match = re.search(r'_(?:dia|d)(\d+)(?:_|$)', var_name)
                    if match:
                        dia_idx = int(match.group(1))
                        if dia_idx not in ctx.dias_bloqueados:
                            todas_bloqueadas = False
                            break
                    else:
                        todas_bloqueadas = False
                        break
                if todas_bloqueadas:
                    desactivar_por_bloqueo = True
            elif etiqueta:
                import re
                match = re.search(r'_d(\d+)', etiqueta)
                if match:
                    dia_idx = int(match.group(1))
                    if dia_idx in ctx.dias_bloqueados:
                        desactivar_por_bloqueo = True
    except Exception:
        pass

    if desactivar_por_bloqueo:
        if ctx.modo_debug:
            label = f"viol__{ctx.codigo_regla}__{etiqueta}" if etiqueta else f"viol__{ctx.codigo_regla}"
            v = modelo.NewBoolVar(label)
            constraint.OnlyEnforceIf(v.Not())
            modelo.Add(v == 0)
        else:
            if ctx.codigo_regla:
                etiqueta_limpia = etiqueta.replace(" ", "_").replace("-", "_") if etiqueta else ""
                nombre_assume = f"REG_{ctx.codigo_regla}__{etiqueta_limpia}" if etiqueta_limpia else f"REG_{ctx.codigo_regla}"
                
                b = None
                for name, var in ctx.assumptions:
                    if name == nombre_assume:
                        b = var
                        break
                if b is None:
                    b = modelo.NewBoolVar(nombre_assume)
                constraint.OnlyEnforceIf(b)
                modelo.Add(b == 0)
        return

    if ctx.modo_debug:
        label = f"viol__{ctx.codigo_regla}__{etiqueta}" if etiqueta else f"viol__{ctx.codigo_regla}"
        v = modelo.NewBoolVar(label)
        constraint.OnlyEnforceIf(v.Not())   # La restricción actúa solo cuando NO hay violación
        ctx.penalizaciones.append((PESO_DEBUG, v))
    else:
        if ctx.codigo_regla:
            etiqueta_limpia = etiqueta.replace(" ", "_").replace("-", "_") if etiqueta else ""
            nombre_assume = f"REG_{ctx.codigo_regla}__{etiqueta_limpia}" if etiqueta_limpia else f"REG_{ctx.codigo_regla}"
            
            b = None
            for name, var in ctx.assumptions:
                if name == nombre_assume:
                    b = var
                    break
            if b is None:
                b = modelo.NewBoolVar(nombre_assume)
                ctx.assumptions.append((nombre_assume, b))
                
            constraint.OnlyEnforceIf(b)
        elif ctx.current_assumption is not None:
            constraint.OnlyEnforceIf(ctx.current_assumption)
        # Si no hay assumption activa, la restricción ya fue agregada normalmente por modelo.Add()


# ---------------------------------------------------------------------------
# Integración con el solver (llamadas desde el orquestador, no desde reglas)
# ---------------------------------------------------------------------------

def activar_assumptions(modelo, ctx, de_verdad=False) -> None:
    """Registra todas las assumptions en el modelo antes de resolver.

    El solver asumirá que todos los flags son True (comportamiento normal).
    Si de_verdad=False, se fijan las variables a True directamente (modelo.Add(b == 1))
    para permitir paralelismo (8 workers).
    Si de_verdad=True, se registran como assumptions (modelo.AddAssumptions) para diagnosticar conflictos.
    """
    if ctx.assumptions and not ctx.modo_debug:
        if de_verdad:
            modelo.AddAssumptions([b for _, b in ctx.assumptions])
        else:
            for _, b in ctx.assumptions:
                modelo.Add(b == 1)


def aplicar_objetivo_debug(modelo, ctx) -> None:
    """Agrega las penalizaciones acumuladas a la función objetivo.

    Solo tiene efecto cuando ctx.modo_debug=True y existen penalizaciones.
    Llamar después de que todas las reglas hayan ejecutado su apply().
    """
    if ctx.modo_debug and ctx.penalizaciones:
        terminos = [peso * var for peso, var in ctx.penalizaciones]
        # Minimizar suma ponderada de violaciones (se suma a cualquier objetivo previo)
        try:
            modelo.Minimize(sum(terminos))
        except Exception:
            # Si ya hay un objetivo definido, OR-Tools acepta redefinirlo
            modelo.Minimize(sum(terminos))


def reportar_conflicto(solver, ctx) -> list[str]:
    """Imprime y retorna los nombres de reglas que causaron INFEASIBLE.

    Usar solo después de que solver.Solve() retorne INFEASIBLE.
    Requiere que activar_assumptions() haya sido llamado antes de resolver.

    Returns:
        Lista de etiquetas de reglas conflictivas.
    """
    indices = set(solver.SufficientAssumptionsForInfeasibility())
    conflictos = []
    
    # Agrupar colisiones por regla y recolectar personas/detalles afectados
    reglas_conflictivas = {} # {codigo_regla: { 'detalles': [], 'personas': set() }}
    
    for etiqueta, b in ctx.assumptions:
        if b.Index() in indices:
            conflictos.append(etiqueta)
            
            # Decodificar etiqueta
            if etiqueta.startswith("REG_"):
                etiqueta_sin_prefix = etiqueta[4:]
            else:
                etiqueta_sin_prefix = etiqueta
                
            if "__" in etiqueta_sin_prefix:
                codigo_regla, detalle = etiqueta_sin_prefix.split("__", 1)
                
                # Intentar extraer el nombre del empleado (suele estar al principio del detalle)
                # Formatos comunes: "Vivas,_Eric_d22Noche...", "Camargo,_Nahuel_d0..."
                persona = None
                import re
                match = re.split(r'_(?:d\d+|hist_|excl_)', detalle)
                if match and match[0]:
                    persona = match[0].replace("_", " ")
                
                reglas_conflictivas.setdefault(codigo_regla, {'detalles': [], 'personas': set()})
                if persona:
                    reglas_conflictivas[codigo_regla]['personas'].add(persona)
                reglas_conflictivas[codigo_regla]['detalles'].append(detalle)
            else:
                codigo_regla = etiqueta_sin_prefix
                reglas_conflictivas.setdefault(codigo_regla, {'detalles': [], 'personas': set()})

    print("\n" + "="*60)
    print("  [WARNING] CONFLICTO MATEMÁTICO DETECTADO")
    print("   Reglas que hacen el cronograma inviable:")
    for codigo_regla, info in reglas_conflictivas.items():
        if info['personas']:
            personas_str = ", ".join(sorted(info['personas']))
            print(f"   -> {codigo_regla} (Colisiones en: {personas_str})")
        elif info['detalles']:
            print(f"   -> {codigo_regla} ({len(info['detalles'])} colisiones detalladas)")
        else:
            print(f"   -> {codigo_regla}")
    print("="*60 + "\n")
    return conflictos



# ---------------------------------------------------------------------------
# Función objetivo unificada para reglas soft
# ---------------------------------------------------------------------------

def construir_objetivo_soft(modelo, ctx) -> None:
    """Construye la función objetivo a partir de los acumuladores del contexto.

    Las micro-reglas soft acumulan sus contribuciones en:
        ctx.penalizaciones_soft  — términos a minimizar
        ctx.bonuses_soft         — términos a maximizar (se restan)

    El orquestador llama a esta función UNA VEZ después de ejecutar todas
    las reglas. Combina con penalizaciones de debug si corresponde.

    Args:
        modelo : CpModel de OR-Tools
        ctx    : ContextoModelo con los acumuladores rellenos
    """
    terminos = list(ctx.penalizaciones_soft)

    # Bonuses se restan (maximizar bonus = minimizar -bonus)
    terminos += [-b for b in ctx.bonuses_soft]

    # En MODO_DEBUG también se agregan las penalizaciones hard convertidas a soft
    if ctx.modo_debug and ctx.penalizaciones:
        terminos += [peso * var for peso, var in ctx.penalizaciones]

    if terminos:
        modelo.Minimize(sum(terminos))


# ---------------------------------------------------------------------------
# Tarea 2.5 — Cargador dinámico de restricciones
# ---------------------------------------------------------------------------

import importlib


def ejecutar_reglas(modelo, ctx, modulos: list[str]) -> None:
    """Carga y ejecuta dinámicamente una lista de módulos de micro-reglas.

    Para cada módulo en `modulos`:
      1. Importa el módulo (ruta Python de puntos, ej. 'restricciones.hard.licencias').
      2. Prepara un assumption BoolVar para el sistema de debugger.
      3. Llama a modulo.apply(modelo, ctx).
      4. Limpia ctx.current_assumption para la siguiente regla.

    Args:
        modelo  : CpModel de OR-Tools
        ctx     : ContextoModelo — se muta en cada regla
        modulos : lista de strings con rutas Python de los módulos a ejecutar
    """
    for ruta_modulo in modulos:
        # Derivar un código de regla limpio del nombre del módulo
        codigo = ruta_modulo.rsplit('.', 1)[-1].upper()
        if (codigo, None) in getattr(ctx, 'exclusiones', set()):
            continue  # Completamente excluido, no ejecutar

        modulo = importlib.import_module(ruta_modulo)
        ctx.codigo_regla = codigo
        preparar_assumption(modelo, ctx, codigo)
        modulo.apply(modelo, ctx)
        ctx.current_assumption = None


def cargar_y_ejecutar_todas(modelo, ctx) -> None:
    """Orquestador principal: ejecuta hard → double → soft → objetivo.

    Reemplaza las llamadas a `aplicar_reglas_duras()` y
    `aplicar_reglas_blandas()` del flujo legacy. Las reglas se toman
    de los registros REGLAS_HARD, REGLAS_DOUBLE y REGLAS_SOFT.

    Flujo:
        1. Ejecuta todas las reglas hard (restricciones duras).
        2. Ejecuta todas las reglas double (modo HARD/SOFT según DB).
        3. Ejecuta todas las reglas soft (acumulan en ctx).
        4. Arma la función objetivo con construir_objetivo_soft().
        5. Registra assumptions en el modelo para detección de INFEASIBLE.

    Args:
        modelo : CpModel de OR-Tools
        ctx    : ContextoModelo completamente inicializado
    """
    from restricciones.hard import REGLAS_HARD
    from restricciones.double import REGLAS_DOUBLE
    from restricciones.soft import REGLAS_SOFT
    from restricciones.hard._utils import crear_y_vincular_variables_semanales

    # Inicializar y vincular variables de categoría semanal
    crear_y_vincular_variables_semanales(modelo, ctx)

    ejecutar_reglas(modelo, ctx, REGLAS_HARD)
    ejecutar_reglas(modelo, ctx, REGLAS_DOUBLE)

    desactivar_soft = getattr(ctx, 'desactivar_soft', False)
    if not desactivar_soft:
        ejecutar_reglas(modelo, ctx, REGLAS_SOFT)
        construir_objetivo_soft(modelo, ctx)

    activar_assumptions(modelo, ctx, de_verdad=getattr(ctx, 'force_assumptions', False))

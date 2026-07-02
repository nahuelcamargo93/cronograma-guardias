"""
restricciones/contexto.py — Contenedor de datos para micro-reglas.

El cargador dinámico instancia un ContextoModelo y lo pasa a cada
función apply(modelo, ctx). Las reglas nunca tocan la DB directamente
ni conocen strings de negocio; todo llega aquí ya traducido a IDs.
"""
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ContextoModelo:
    """Snapshot matemático del problema para una ejecución concreta.

    Campos de identidad
    -------------------
    servicio_id   : int   — servicio que se está optimizando
    fecha_inicio  : str   — ISO "YYYY-MM-DD"
    fecha_fin     : str   — ISO "YYYY-MM-DD"

    Dimensiones del problema
    ------------------------
    dias          : int   — total de días del bloque
    num_semanas   : int   — semanas completas del bloque
    offset_dia    : int   — día de semana del primer día (0=Lun)
    feriados      : set[int] — índices de días feriados dentro del bloque

    Objetos del motor
    -----------------
    turnos        : dict  — {(emp_idx, dia, turno_idx): BoolVar}
    empleados     : list  — lista de objetos Empleado (modelo actual)
    traductor     : Traductor — mapeo bidireccional string <-> ID

    Configuración de la regla activa
    ---------------------------------
    codigo_regla  : str   — ej. "UN_TURNO_POR_DIA"
    params        : dict  — parámetros JSON de la regla para este servicio/persona

    Modo debugger
    -------------
    modo_debug    : bool  — si True, las reglas hard/double se convierten en soft
    penalizaciones: list  — acumula (peso, var) para la función objetivo en debug
    assumptions   : list  — acumula BoolVars para SufficientAssumptionsForInfeasibility
    """
    # Identidad
    servicio_id:  int
    fecha_inicio: str
    fecha_fin:    str

    # Dimensiones
    dias:         int
    num_semanas:  int
    offset_dia:   int
    feriados:     set = field(default_factory=set)

    # Objetos del motor
    turnos:       dict = field(default_factory=dict)
    empleados:    list = field(default_factory=list)
    traductor:    Any  = None  # Traductor — Any para evitar import circular

    # Regla activa
    codigo_regla: str  = ""
    params:       dict = field(default_factory=dict)

    # Debugger
    modo_debug:      bool = False
    modo_debug_hard: bool = False
    penalizaciones:  list = field(default_factory=list)
    assumptions:     list = field(default_factory=list)
    exclusiones:     set = field(default_factory=set)
    dias_bloqueados: set = field(default_factory=set)

    # Historial y ajustes (opcionales, necesarios para reglas de equidad)
    historial_semana_previa: dict = field(default_factory=dict)
    ajustes_reglas_personal: dict = field(default_factory=dict)
    reglas_servicio:         dict = field(default_factory=dict)
    demanda_req:             dict = field(default_factory=dict)
    ajustes_demanda:         list = field(default_factory=list)
    demanda_turnos:          dict = field(default_factory=dict)
    turnos_dict:             dict = field(default_factory=dict)
    flr_tracker:             dict = field(default_factory=dict)
    vars_turno_sem:          dict = field(default_factory=dict)

    # Acumuladores para el orquestador soft
    penalizaciones_soft: list = field(default_factory=list)  # [(peso * var)]
    bonuses_soft:        list = field(default_factory=list)  # [(valor * var)]

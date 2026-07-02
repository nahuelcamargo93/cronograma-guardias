from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Set

@dataclass
class Turno:
    nombre: str
    horas: int
    hora_inicio: str = "08:00"
    puesto_nombre: Optional[str] = None
    es_noche: bool = False
    es_dia: bool = False
    
    def __post_init__(self):
        # Clasificación heurística basada en el nombre (como estaba en data.py, pero ahora es propiedad)
        self.es_noche = self.nombre.startswith("Noche") or "Noche" in self.nombre
        self.es_dia = self.nombre.startswith("Dia") or "Dia_" in self.nombre


@dataclass
class Empleado:
    nombre: str
    rol: str
    categoria: Optional[str] = None
    servicio_id: Optional[int] = None
    fecha_cumpleanos: Optional[str] = None
    es_madre: bool = False
    es_padre: bool = False
    regimen_trabajo: Optional[str] = None
    
    # Historial acumulado desde la DB
    horas_anuales_previas: int = 0
    findes_semanas_previos: int = 0
    findes_habiles_previos: int = 0
    findes_largos_3_previos: int = 0
    findes_largos_4_previos: int = 0
    feriados_previos: int = 0
    horas_fijas_semanales: int = 0
    seguimientos_previos: int = 0
    noches_previas: int = 0
    
    # Días (índices 0..DIAS_DEL_BLOQUE) en los que está de licencia (LPP/LAR)
    dias_licencia: Set[int] = field(default_factory=set)
    # Mapeo de día (índice) a tipo de licencia (ej. 'LPP', 'LAR', etc.)
    tipos_licencia: Dict[int, str] = field(default_factory=dict)

    # Puestos que la persona puede cubrir
    puestos_habilitados: Set[str] = field(default_factory=set)
    
    # Puestos que la persona cubre preferentemente (es_primario=1 en personal_puestos)
    puestos_primarios: Set[str] = field(default_factory=set)

    # Reglas específicas de la BD para este empleado
    reglas: Dict[str, Any] = field(default_factory=dict)
    
    horas_mensuales_reglamentarias: Optional[int] = None
    fecha_inicio_historial: Optional[str] = None


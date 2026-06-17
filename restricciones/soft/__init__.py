"""
restricciones/soft/__init__.py
Registro de todas las micro-reglas soft para el cargador dinámico.
Cada entrada es un módulo con función apply(modelo, ctx).
"""

REGLAS_SOFT = [
    "restricciones.soft.penalizacion_turno",
    "restricciones.soft.penalizacion_puesto_no_preferido",
    "restricciones.soft.bonus_combo_finde",
    "restricciones.soft.bonus_seg_total",
    "restricciones.soft.peso_brecha_seg",
    "restricciones.soft.turnos_preferenciales",
    "restricciones.soft.equidad_horas_mensuales",
    "restricciones.soft.equidad_finds_mensual",
    "restricciones.soft.equidad_finds_anual",
    "restricciones.soft.equidad_fl3_fl4",
    "restricciones.soft.equidad_fsl",
    "restricciones.soft.equidad_feriados",
    "restricciones.soft.equidad_tipo_turno",
    "restricciones.soft.objetivo_rotacion_mensual",
    "restricciones.soft.penalizacion_turno_ausente",
    "restricciones.soft.bonus_carga_perfecta",
    "restricciones.soft.peso_brecha_horas",
    "restricciones.soft.peso_brecha_turno",
    "restricciones.soft.francos_fin_mes",
]

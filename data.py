TURNOS_SEMANA = ["Mañana_UTI", "Mañana_UCO", "Tarde_UTI", "Tarde_UCO", "Noche", "Mañana_especial", "Tarde_especial"]
TURNOS_FINDE = ["Dia_UTI", "Dia_UCO", "Noche"]
DEBUG_LOGS = True

FECHA_INICIO = "2026-05-25"
FECHA_FIN    = "2026-07-05"  # Inclusive. El rango debe ser múltiplo de 7 días (semanas completas).
# Lista de feriados en formato "YYYY-MM-DD"
FERIADOS = [
    # "2024-04-05", # Ejemplo
    "2026-05-25"
]
# LAR y LPP ya no se definen aquí — se cargan desde la base de datos (tabla licencias).

# AJUSTES SELECTIVOS DE VACANTES POR SEMANA (Índice 0, 1, 2...)
# Formato: { numero_semana: { "Turno": vacantes_nuevas } }
AJUSTES_VACANTES = {
    1:{"Mañana_UTI":3, "Tarde_UTI": 2},
    2:{"Mañana_UTI":3, "Tarde_UTI": 2},
    3:{"Mañana_UTI":4, "Tarde_UTI": 2},
    4:{"Mañana_UTI":4, "Tarde_UTI": 2}
}

PERSONAL = [
    # JEFATURA Y COORDINACIÓN (Seguimiento Mañana 4 semanas)
    {
        "Nombre": "Lic. Garcia",
        "Rol": "Jefe", "Puede_Noche": False, "Max_Noches": 0,
        "Turnos_Prohibidos_LV": ["Tarde_UTI", "Tarde_UCO", "Mañana_UCO", "Dia_UCO"], "Semanas_Seguimiento": {"Mañana_UTI": 4},
        "Asignaciones_Fijas": []
    },
    {
        "Nombre": "Lic. Toledo",
        "Rol": "Coordinador", "Puede_Noche": False, "Max_Noches": 0,
        "Turnos_Prohibidos_LV": ["Tarde_UTI", "Tarde_UCO", "Dia_UTI"], "Semanas_Seguimiento": {"Mañana_UCO": 4},
        "Asignaciones_Fijas": []
    },
    {
        "Nombre": "Lic. Franco",
        "Rol": "Coordinador", "Puede_Noche": False, "Max_Noches": 0,
        "Turnos_Prohibidos_LV": ["Tarde_UTI", "Tarde_UCO", "Mañana_UCO", "Dia_UCO"], "Semanas_Seguimiento": {"Mañana_UTI": 4},
        "Asignaciones_Fijas": []
    },
    {
        "Nombre": "Lic. Moyano",
        "Rol": "Coordinador", "Puede_Noche": False, "Max_Noches": 0,
        "Turnos_Prohibidos_LV": ["Tarde_UTI", "Tarde_UCO", "Mañana_UCO", "Dia_UCO"], "Semanas_Seguimiento": {"Mañana_UTI": 4},
        "Asignaciones_Fijas": []
    },

    # KINESIOLOGÍA NOCTURNA
    {
        "Nombre": "Lic. Juarez",
        "Rol": "Nocturno", "Puede_Noche": True, "Max_Noches": 12,
        "Turnos_Prohibidos_LV": ["Mañana_UTI", "Mañana_UCO", "Tarde_UTI", "Tarde_UCO", "Mañana_especial", "Tarde_especial"],
        "Semanas_Seguimiento": {}, "Asignaciones_Fijas": []
    },

    # CASOS ESPECIALES
    {
        "Nombre": "Lic. Giaccoppo",
        "Rol": "Rotativo", "Puede_Noche": True, "Max_Noches": 4,
        "Turnos_Prohibidos_LV": [], "Semanas_Seguimiento": {"Mañana_UTI": 1, "Tarde_UTI": 2},
        "Asignaciones_Fijas": [
            {"Dia": "Lunes",     "Turno": "Tarde_especial", "Tipo": "Especial",    "Horas": 6},
        ]
    },
    {
        "Nombre": "Lic. Camargo N.",
        "Rol": "Rotativo", "Puede_Noche": True, "Max_Noches": 4,
        "Turnos_Prohibidos_LV": ["Mañana_UTI", "Mañana_UCO", "Mañana_especial"], "Semanas_Seguimiento": {"Indistinto": 1},
        "Asignaciones_Fijas": [
            {"Dia": "Lunes",     "Turno": "Tarde_especial", "Tipo": "Especial",    "Horas": 6},
            {"Dia": "Miercoles", "Turno": "Tarde",          "Tipo": "Asistencial", "Horas": 6},
            {"Dia": "Viernes",   "Turno": "Tarde",          "Tipo": "Asistencial", "Horas": 6}
        ],
        "Turnos_Preferenciales": [
            {"Dia": "Domingo",   "Turno": "Dia",            "Tipo": "Asistencial", "Horas": 12}
        ],
        "Notas": "Lunes tarde: Base de datos (Especial). Domingo: Guardia 12hs. No mañanas L-V."
    },
    {
        "Nombre": "Lic. Coniglio",
        "Rol": "Rotativo",
        "Puede_Noche": True,
        "Max_Noches": 4,
        "Turnos_Prohibidos_LV": [],
        "Semanas_Seguimiento": {"Indistinto": 1},
        "Asignaciones_Fijas": [
            {"Dia": "Miercoles", "Turno": "Mañana_especial", "Tipo": "Especial", "Horas": 6},
            {"Dia": "Miercoles", "Turno": "Tarde_especial",  "Tipo": "Especial", "Horas": 6}
        ],
        "Notas": "Todos los miércoles: Mañana y Tarde_especial (12hs fijas)."
    },

    # ROTATIVOS COMUNES (1 Semana Seguimiento Indistinto)
    { "Nombre": "Lic. Guzman",    "Rol": "Rotativo", "Puede_Noche": True, "Max_Noches": 4, "Turnos_Prohibidos_LV": [], "Semanas_Seguimiento": {"Indistinto": 1}, "Asignaciones_Fijas": [] },
    { "Nombre": "Lic. Leonforte", "Rol": "Rotativo", "Puede_Noche": True, "Max_Noches": 4, "Turnos_Prohibidos_LV": [], "Semanas_Seguimiento": {"Indistinto": 1}, "Asignaciones_Fijas": [] },
    { "Nombre": "Lic. Marino",    "Rol": "Rotativo", "Puede_Noche": True, "Max_Noches": 4, "Turnos_Prohibidos_LV": [], "Semanas_Seguimiento": {"Indistinto": 1}, "Asignaciones_Fijas": [] },
    { "Nombre": "Lic. Mesa",      "Rol": "Rotativo", "Puede_Noche": True, "Max_Noches": 4, "Turnos_Prohibidos_LV": [], "Semanas_Seguimiento": {"Indistinto": 1}, "Asignaciones_Fijas": [] },
    { "Nombre": "Lic. Sosa",      "Rol": "Rotativo", "Puede_Noche": True, "Max_Noches": 4, "Turnos_Prohibidos_LV": [], "Semanas_Seguimiento": {"Indistinto": 1}, "Asignaciones_Fijas": [] },
    { "Nombre": "Lic. Syriani",   "Rol": "Rotativo", "Puede_Noche": True, "Max_Noches": 4, "Turnos_Prohibidos_LV": [], "Semanas_Seguimiento": {"Indistinto": 1}, "Asignaciones_Fijas": [] },
    { "Nombre": "Lic. Vander",    "Rol": "Rotativo", "Puede_Noche": True, "Max_Noches": 4, "Turnos_Prohibidos_LV": [], "Semanas_Seguimiento": {"Indistinto": 1}, "Asignaciones_Fijas": [] },
    { "Nombre": "Lic. Vivas",     "Rol": "Rotativo", "Puede_Noche": True, "Max_Noches": 4, "Turnos_Prohibidos_LV": [], "Semanas_Seguimiento": {"Indistinto": 1}, "Asignaciones_Fijas": [] },
    { "Nombre": "Lic. Espinosa",  "Rol": "Rotativo", "Puede_Noche": True, "Max_Noches": 4, "Turnos_Prohibidos_LV": [], "Semanas_Seguimiento": {"Indistinto": 1}, "Asignaciones_Fijas": [] },
    { "Nombre": "Lic. Welch",     "Rol": "Rotativo", "Puede_Noche": True, "Max_Noches": 4, "Turnos_Prohibidos_LV": [], "Semanas_Seguimiento": {"Indistinto": 1}, "Asignaciones_Fijas": [] },
    { "Nombre": "Lic. Guardia",   "Rol": "Rotativo", "Puede_Noche": True, "Max_Noches": 4, "Turnos_Prohibidos_LV": [], "Semanas_Seguimiento": {"Indistinto": 1}, "Asignaciones_Fijas": [] },
    { "Nombre": "Lic. Flores",    "Rol": "Rotativo", "Puede_Noche": True, "Max_Noches": 4, "Turnos_Prohibidos_LV": [], "Semanas_Seguimiento": {"Indistinto": 1}, "Asignaciones_Fijas": [] },
]

DEMANDA_TURNOS = {
    "Semana": { # Lunes a Viernes
        "Mañana_UTI":     {"Horas": 6,  "Vacantes": 5},
        "Mañana_UCO":     {"Horas": 6,  "Vacantes": 1},
        "Tarde_UTI":      {"Horas": 6,  "Vacantes": 3},
        "Tarde_UCO":      {"Horas": 6,  "Vacantes": 1},
        "Noche":          {"Horas": 12, "Vacantes": 2},
        "Mañana_especial": {"Horas": 6,  "Vacantes": 0},
        "Tarde_especial":  {"Horas": 6,  "Vacantes": 0}
    },
    "Finde_Feriado": { # Sábados, Domingos y Feriados
        "Dia_UTI":   {"Horas": 12, "Vacantes": 2},
        "Dia_UCO":   {"Horas": 12, "Vacantes": 1},
        "Noche":     {"Horas": 12, "Vacantes": 2}
    }
}

def calcular_horas_fijas(asignaciones):
    return sum(item['Horas'] for item in asignaciones)

def asignar_horas(turno):
    if turno.startswith("Noche") or turno.startswith("Dia"):
        return 12
    else:
        return 6

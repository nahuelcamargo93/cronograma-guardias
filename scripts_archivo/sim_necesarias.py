from datetime import date, timedelta

FECHA_INICIO = "2026-05-25"
FERIADOS = ["2026-05-25"] # Monday Week 0

DEMANDA_TURNOS = {
    "Semana": {
        "Mañana_UTI": 5, "Mañana_UCO": 1, "Tarde_UTI": 3, "Tarde_UCO": 1, "Noche": 2,
        "Mañana_especial": 0, "Tarde_especial": 0
    },
    "Finde_Feriado": {
        "Dia_UTI": 2, "Dia_UCO": 1, "Noche": 2
    }
}

# Updated adjustments
AJUSTES = {
    ("2026-06-01", "2026-06-07"): {"Mañana_UTI": 4, "Tarde_UTI": 2},
    ("2026-06-08", "2026-06-14"): {"Mañana_UTI": 4, "Tarde_UTI": 2},
    ("2026-06-15", "2026-06-21"): {"Mañana_UTI": 3, "Tarde_UTI": 2},
    ("2026-06-22", "2026-06-28"): {"Mañana_UTI": 4, "Tarde_UTI": 2},
}

fecha_inicio_dt = date.fromisoformat(FECHA_INICIO)
for sem in range(6):
    horas_necesarias = 0
    for d in range(sem * 7, (sem + 1) * 7):
        current_date = fecha_inicio_dt + timedelta(days=d)
        fecha_str = current_date.isoformat()
        es_f = (current_date.weekday() >= 5) or (fecha_str in FERIADOS)
        tipo_dia = "Finde_Feriado" if es_f else "Semana"
        
        for t_nombre, vac_base in DEMANDA_TURNOS[tipo_dia].items():
            vacantes = vac_base
            for (fi, ff), cambios in AJUSTES.items():
                if fi <= fecha_str <= ff and t_nombre in cambios:
                    vacantes = cambios[t_nombre]
                    break
            
            h = 12 if (es_f or t_nombre == "Noche") else 6
            horas_necesarias += vacantes * h
    
    print(f"Semana {sem}: {horas_necesarias} hs")

terms = ['PENALIZACION_TURNO_AUSENTE', 'ROTACION_MENSUAL', 'MEZCLA_SEMANAL', 'EVITAR_MEZCLA', 'EVITAR_MEZCLA_SEMANAL_DURA', 'ROTACION_MENSUAL_DURA']
with open("soft_rules.py", "r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        for term in terms:
            if term in line:
                print(f"{i+1}: {line.strip()}")
                break

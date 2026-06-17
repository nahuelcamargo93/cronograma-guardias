import sqlite3
from datetime import datetime, date, timedelta

db_path = 'cronograma_inteligente.db'
conn = sqlite3.connect(db_path)

# 1. Obtener empleados activos
empleados = conn.execute("SELECT nombre FROM personal WHERE servicio_id = 1 AND COALESCE(activo, 1) = 1").fetchall()
empleados = [e[0] for e in empleados]
print(f"Total empleados activos: {len(empleados)}")

# 2. Obtener licencias en julio 2026
licencias_raw = conn.execute("""
    SELECT nombre, fecha_inicio, fecha_fin 
    FROM licencias 
    WHERE (fecha_inicio <= '2026-07-31' AND fecha_fin >= '2026-07-01')
      AND COALESCE(activa, 1) = 1
""").fetchall()

print("\nLicencias en julio 2026:")
for lic in licencias_raw:
    print(f"- {lic[0]}: {lic[1]} a {lic[2]}")

# 3. Analizar disponibilidad día por día
fecha_inicio = date(2026, 7, 1)
dias = 31

print(f"\n{'Día':<4} | {'Fecha':<10} | {'Día Sem':<8} | {'Demanda':<7} | {'Disponibles':<11} | {'Margen':<6}")
print("-" * 60)

for d in range(dias):
    fecha_d = fecha_inicio + timedelta(days=d)
    fecha_str = fecha_d.isoformat()
    wd = fecha_d.weekday()
    wd_str = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"][wd]
    
    # Check if holiday
    is_feriado = conn.execute("SELECT COUNT(*) FROM feriados WHERE fecha = ?", (fecha_str,)).fetchone()[0] > 0
    
    es_finde_o_feriado = (wd >= 5) or is_feriado
    
    # Demanda total
    # UTI: Mañana (5), Tarde (4) [weekdays] | Dia (2) [weekends]
    # UCO: Mañana (2), Tarde (1) [weekdays] | Dia (1) [weekends]
    # General (Noche): Noche (2) [weekdays and weekends]
    if es_finde_o_feriado:
        demanda = 2 + 1 + 2 # UTI Dia (2), UCO Dia (1), Noche (2) = 5
    else:
        demanda = 5 + 4 + 2 + 1 + 2 # UTI Mañana (5), UTI Tarde (4), UCO Mañana (2), UCO Tarde (1), Noche (2) = 14
        
    # Calcular disponibles
    disponibles = []
    for emp in empleados:
        # Check if on license
        on_license = False
        for lic in licencias_raw:
            if lic[0] == emp and lic[1] <= fecha_str <= lic[2]:
                on_license = True
                break
        if not on_license:
            disponibles.append(emp)
            
    margen = len(disponibles) - demanda
    print(f"{d:<4} | {fecha_str} | {wd_str:<8} | {demanda:<7} | {len(disponibles):<11} | {margen:<6} {'!!!' if margen < 0 else ''}")

conn.close()

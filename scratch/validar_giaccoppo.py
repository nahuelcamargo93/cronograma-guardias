import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.connection import get_connection
from datetime import datetime, date, timedelta

def validar():
    cronograma_id = 316
    nombre = "Lic. Giaccoppo"
    
    with get_connection() as conn:
        # Obtener guardias de Lic. Giaccoppo para este cronograma
        cur = conn.execute("""
            SELECT fecha, turno, horas 
            FROM guardias 
            WHERE cronograma_id = ? AND nombre = ?
            ORDER BY fecha
        """, (cronograma_id, nombre))
        guardias = cur.fetchall()
        
    print(f"Guardias asignadas a {nombre} en Cronograma {cronograma_id}:")
    
    # Agrupar por semana (lunes)
    semanas = {}
    for fecha_str, turno, horas in guardias:
        fecha_dt = date.fromisoformat(fecha_str)
        lunes = fecha_dt - timedelta(days=fecha_dt.weekday())
        lunes_str = lunes.isoformat()
        semanas.setdefault(lunes_str, []).append((fecha_str, turno, horas, fecha_dt.weekday()))
        
    for lunes_str, g_list in sorted(semanas.items()):
        print(f"\nSemana del {lunes_str}:")
        count_m = 0
        count_t = 0
        count_n = 0
        
        # Turnos de mañana UTI/UCO y tarde UTI/UCO
        for fecha, turno, horas, weekday in g_list:
            # Solo de lunes a viernes (weekday < 5)
            is_lv = weekday < 5
            
            # Clasificar
            tag = ""
            if is_lv:
                if turno in ('Mañana_UTI', 'Mañana_UCO', 'Dia_UTI', 'Dia_UCO'):
                    count_m += 1
                    tag = " (M)"
                if turno in ('Tarde_UTI', 'Tarde_UCO', 'Dia_UTI', 'Dia_UCO'):
                    count_t += 1
                    tag = " (T)"
                if turno == 'Noche':
                    count_n += 1
                    tag = " (N)"
            else:
                tag = " [Fin de Semana]"
                
            print(f"  - {fecha} ({['Lun','Mar','Mie','Jue','Vie','Sab','Dom'][weekday]}): {turno} {horas}hs{tag}")
            
        print(f"  Resumen L-V: Mañana={count_m}, Tarde={count_t}, Noche={count_n}")
        if count_m >= 4:
            print("  -> ¡CUMPLE SEGUIMIENTO MAÑANA!")
        if count_t >= 4:
            print("  -> ¡CUMPLE SEGUIMIENTO TARDE!")

if __name__ == "__main__":
    validar()

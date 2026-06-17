import sqlite3
from datetime import date, timedelta
from database.connection import get_connection
from restricciones.hard._utils import get_semanas_calendario

def es_fecha_licencia(nombre: str, fecha_dt: date) -> bool:
    # Simulado/directo para verificar
    with get_connection() as conn:
        row = conn.execute("""
            SELECT COUNT(*) FROM licencias 
            WHERE nombre = ? AND activa = 1 AND ? BETWEEN fecha_inicio AND fecha_fin
        """, (nombre, fecha_dt.isoformat())).fetchone()
    return row[0] > 0

def verificar():
    nombre = "POLETTI NATALIA"
    crono_id = 486
    fecha_inicio = "2026-07-01"
    dias = 31

    fecha_inicio_dt = date.fromisoformat(fecha_inicio)
    semanas = get_semanas_calendario(dias, fecha_inicio_dt)

    with get_connection() as conn:
        guardias = conn.execute("""
            SELECT fecha, turno FROM guardias 
            WHERE cronograma_id = ? AND nombre = ?
            ORDER BY fecha
        """, (crono_id, nombre)).fetchall()
        
        # También traer historial del cronograma anterior (ID 437)
        guardias_prev = conn.execute("""
            SELECT g.fecha, g.turno FROM guardias g
            JOIN cronogramas c ON g.cronograma_id = c.id
            WHERE c.id = 437 AND g.nombre = ?
            ORDER BY g.fecha
        """, (nombre,)).fetchall()

    guardias_dict = {g[0]: g[1] for g in guardias}
    guardias_prev_dict = {g[0]: g[1] for g in guardias_prev}

    print(f"\n=== AUDITORÍA PARA {nombre} (CRONOGRAMA ID {crono_id}) ===")
    
    for (iso_y, iso_w), days in semanas.items():
        fl = days[0][1]
        lunes_dt = fl - timedelta(days=fl.isocalendar()[2] - 1)
        
        turnos_reales = []
        licencias = []
        francos = []
        
        for offset in range(7):
            fecha_d = lunes_dt + timedelta(days=offset)
            fecha_str = fecha_d.isoformat()
            
            # Ver si está en el rango de planificación o historial
            if fecha_d < fecha_inicio_dt:
                # Historial
                if es_fecha_licencia(nombre, fecha_d):
                    licencias.append(f"{fecha_str} (Licencia Histórica)")
                elif fecha_str in guardias_prev_dict:
                    turnos_reales.append(f"{fecha_str} ({guardias_prev_dict[fecha_str]} Histórico)")
                else:
                    francos.append(f"{fecha_str} (Franco Histórico)")
            else:
                # Planificación
                # Buscar en days si este día está dentro del bloque
                d_idx = (fecha_d - fecha_inicio_dt).days
                if 0 <= d_idx < dias:
                    # En la planificación
                    if es_fecha_licencia(nombre, fecha_d):
                        licencias.append(f"{fecha_str} (Licencia Planificada)")
                    elif fecha_str in guardias_dict:
                        turnos_reales.append(f"{fecha_str} ({guardias_dict[fecha_str]})")
                    else:
                        francos.append(f"{fecha_str} (Franco)")
                else:
                    # Fuera de planificación (mes siguiente)
                    pass
        
        total_trabajado_licencia = len(turnos_reales) + len(licencias)
        total_francos = len(francos)
        
        print(f"\nSemana {iso_y}w{iso_w} (Lunes {lunes_dt.isoformat()} a Domingo {(lunes_dt+timedelta(days=6)).isoformat()}):")
        print(f"  - Turnos reales: {turnos_reales}")
        print(f"  - Licencias:     {licencias}")
        print(f"  - Francos:       {francos}")
        print(f"  => TOTAL TRABAJADO + LICENCIAS: {total_trabajado_licencia}")
        print(f"  => TOTAL FRANCOS:               {total_francos}")

if __name__ == '__main__':
    verificar()

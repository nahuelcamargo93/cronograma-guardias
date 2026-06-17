import sys
import os
from datetime import date, timedelta
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_connection

def cargar_guardias_previas_OLD(fecha_inicio_str, dias_atras=28, servicio_id=None):
    with get_connection() as conn:
        if servicio_id is not None:
            ultimo_cr_query = """
                SELECT DISTINCT c.id FROM cronogramas c
                JOIN guardias g ON c.id = g.cronograma_id
                JOIN personal p ON g.nombre = p.nombre
                WHERE c.estado = 'aprobado' AND c.fecha_inicio < ? AND p.servicio_id = ?
                ORDER BY c.fecha_inicio DESC
                LIMIT 1
            """
            row_cr = conn.execute(ultimo_cr_query, [fecha_inicio_str, servicio_id]).fetchone()
        else:
            ultimo_cr_query = """
                SELECT id FROM cronogramas
                WHERE estado = 'aprobado' AND fecha_inicio < ?
                ORDER BY fecha_inicio DESC
                LIMIT 1
            """
            row_cr = conn.execute(ultimo_cr_query, [fecha_inicio_str]).fetchone()
        
        if not row_cr:
            return {}
        cronograma_id = row_cr[0]
        query = """
            SELECT g.nombre, g.fecha, g.turno, g.horas 
            FROM guardias g
            JOIN personal p ON g.nombre = p.nombre
            WHERE g.cronograma_id = ?
        """
        params = [cronograma_id]
        if servicio_id is not None:
            query += " AND p.servicio_id = ?"
            params.append(servicio_id)
        rows = conn.execute(query, params).fetchall()
    historial = {}
    for nombre, fecha, turno, horas in rows:
        historial.setdefault(nombre, []).append({'fecha': fecha, 'turno': turno, 'horas': horas})
    return historial

def cargar_guardias_previas_NEW(fecha_inicio_str, dias_atras=28, servicio_id=None):
    fecha_inicio_dt = date.fromisoformat(fecha_inicio_str)
    fecha_limite_dt = fecha_inicio_dt - timedelta(days=dias_atras)
    fecha_limite_str = fecha_limite_dt.isoformat()
    with get_connection() as conn:
        query = """
            SELECT g.nombre, g.fecha, g.turno, g.horas 
            FROM guardias g
            JOIN cronogramas c ON g.cronograma_id = c.id
            JOIN personal p ON g.nombre = p.nombre
            WHERE c.estado = 'aprobado' 
              AND g.fecha >= ? AND g.fecha < ?
        """
        params = [fecha_limite_str, fecha_inicio_str]
        if servicio_id is not None:
            query += " AND p.servicio_id = ?"
            params.append(servicio_id)
        query += " ORDER BY g.fecha ASC"
        rows = conn.execute(query, params).fetchall()
    historial = {}
    for nombre, fecha, turno, horas in rows:
        historial.setdefault(nombre, []).append({'fecha': fecha, 'turno': turno, 'horas': horas})
    return historial

print("--- OLD LOAD (Nesteruk) ---")
old_hist = cargar_guardias_previas_OLD("2026-07-01", servicio_id=3)
print(old_hist.get("Nesteruk, María Silvia", []))

print("\n--- NEW LOAD (Nesteruk) ---")
new_hist = cargar_guardias_previas_NEW("2026-07-01", servicio_id=3)
print(new_hist.get("Nesteruk, María Silvia", []))

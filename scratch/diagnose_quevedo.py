import sqlite3
from database.connection import get_connection

def main():
    print("--- Diagnóstico de Feriados para Personal ACTIVO del Servicio 2 ---")
    with get_connection() as conn:
        # 1. Obtener todos los feriados del catálogo
        feriados = [r[0] for r in conn.execute("SELECT fecha FROM feriados").fetchall()]
        placeholders = ",".join("?" for _ in feriados)
        
        # 2. Obtener lista de personal activo del servicio 2
        empleados_activos = [r[0] for r in conn.execute("SELECT nombre FROM personal WHERE servicio_id = 2 AND COALESCE(activo, 1) = 1").fetchall()]
        
        # 3. Calcular feriados acumulados aprobados (históricos) por persona activa
        historico_map = {}
        for emp in empleados_activos:
            historico_map[emp] = {'dias': 0, 'turnos': 0, 'actual': 0}
            
        rows_hist = conn.execute(f"""
            SELECT g.nombre, COUNT(DISTINCT g.fecha) as dias_feriados, COUNT(g.fecha) as turnos_feriados
            FROM guardias g
            JOIN cronogramas c ON g.cronograma_id = c.id
            WHERE g.fecha IN ({placeholders}) AND c.estado = 'aprobado' AND g.nombre IN ({",".join("?" for _ in empleados_activos)})
            GROUP BY g.nombre
        """, feriados + empleados_activos).fetchall()
        
        for r in rows_hist:
            historico_map[r[0]]['dias'] = r[1]
            historico_map[r[0]]['turnos'] = r[2]

        # 4. Obtener feriados asignados en el cronograma 437 (borrador actual)
        rows_act = conn.execute(f"""
            SELECT g.nombre, COUNT(DISTINCT g.fecha)
            FROM guardias g
            WHERE g.cronograma_id = 437 AND g.fecha IN ({placeholders}) AND g.nombre IN ({",".join("?" for _ in empleados_activos)})
            GROUP BY g.nombre
        """, feriados + empleados_activos).fetchall()
        
        for r in rows_act:
            historico_map[r[0]]['actual'] = r[1]
            
        print("\n=== Personal Activo | Histórico (Días / Turnos) | Asignados este mes (Días) ===")
        # Ordenar por histórico de días de menor a mayor
        ordenado = sorted(historico_map.items(), key=lambda x: x[1]['dias'])
        for emp, datos in ordenado:
            print(f"Personal: {emp:<25} | Historial: {datos['dias']} días ({datos['turnos']} turnos) | Asignados este mes: {datos['actual']} días")

if __name__ == "__main__":
    main()

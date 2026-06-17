import sqlite3
import json

def main():
    conn = sqlite3.connect("cronograma_inteligente.db")
    cursor = conn.cursor()
    
    # 1. Turnos configurados para servicio 3
    print("--- TURNOS CONFIGURADOS SERVICIO 3 ---")
    turnos = cursor.execute("""
        SELECT tc.nombre, tc.hora_inicio, tc.horas, tc.dias_semana, tc.activo
        FROM turnos_config tc
        WHERE tc.servicio_id = 3
    """).fetchall()
    for row in turnos:
        print(f"Nombre: {row[0]} | H.Inicio: {row[1]} | Horas: {row[2]} | Dias: {row[3]} | Activo: {row[4]}")
        
    # 2. Puestos configurados para servicio 3
    print("\n--- PUESTOS SERVICIO 3 ---")
    puestos = cursor.execute("SELECT id, nombre FROM puestos WHERE servicio_id = 3").fetchall()
    for row in puestos:
        print(f"ID: {row[0]} | Nombre: {row[1]}")
        
    # 3. Demanda configurada para servicio 3
    print("\n--- DEMANDA CONFIGURADA SERVICIO 3 ---")
    demanda = cursor.execute("""
        SELECT dc.id, p.nombre, dc.tipo_dia, dc.hora_inicio, dc.hora_fin, dc.cantidad_min, dc.cantidad_max, dc.dias_semana, dc.activo
        FROM demanda_config dc
        JOIN puestos p ON dc.puesto_id = p.id
        WHERE p.servicio_id = 3
    """).fetchall()
    for row in demanda:
        print(f"ID: {row[0]} | Puesto: {row[1]} | Tipo Dia: {row[2]} | H.Inicio: {row[3]} | H.Fin: {row[4]} | Min: {row[5]} | Max: {row[6]} | Dias: {row[7]} | Activo: {row[8]}")
        
    # 4. Ajustes de demanda para julio 2026
    print("\n--- AJUSTES DE DEMANDA JULIO 2026 SERVICIO 3 ---")
    ajustes = cursor.execute("""
        SELECT da.id, p.nombre, da.fecha_inicio, da.fecha_fin, da.cantidad_min, da.cantidad_max, da.dias_semana, da.activo
        FROM demanda_ajustes da
        JOIN demanda_config dc ON da.demanda_config_id = dc.id
        JOIN puestos p ON dc.puesto_id = p.id
        WHERE p.servicio_id = 3 AND da.fecha_inicio <= '2026-07-31' AND da.fecha_fin >= '2026-07-01'
    """).fetchall()
    for row in ajustes:
        print(f"ID: {row[0]} | Puesto: {row[1]} | Inicio: {row[2]} | Fin: {row[3]} | Min: {row[4]} | Max: {row[5]} | Dias: {row[6]} | Activo: {row[7]}")
        
    # 5. Total de guardias del cronograma 353 por persona y puesto
    print("\n--- RESUMEN DE GUARDIAS CRONOGRAMA 353 ---")
    guardias = cursor.execute("""
        SELECT g.nombre, g.turno, COUNT(*), SUM(g.horas)
        FROM guardias g
        WHERE g.cronograma_id = 353
        GROUP BY g.nombre, g.turno
        ORDER BY g.nombre, g.turno
    """).fetchall()
    for row in guardias:
        print(f"Persona: {row[0]:<35} | Turno: {row[1]:<15} | Cantidad: {row[2]:<2} | Total Horas: {row[3]}")
        
    conn.close()

if __name__ == "__main__":
    main()

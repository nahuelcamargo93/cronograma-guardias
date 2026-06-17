import sqlite3
import pandas as pd

def main():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()

    # 1. Cronograma 261 info
    crono = cursor.execute("SELECT id, fecha_inicio, fecha_fin, notas, estado FROM cronogramas WHERE id = 261").fetchone()
    print("=== Cronograma 261 ===")
    if crono:
        print(f"ID: {crono[0]}, Inicio: {crono[1]}, Fin: {crono[2]}, Notas: {crono[3]}, Estado: {crono[4]}")
    else:
        print("No se encontró el cronograma 261")
        conn.close()
        return

    # 2. Servicio del cronograma 261
    servicio_row = cursor.execute("""
        SELECT DISTINCT p.servicio_id, s.nombre
        FROM guardias g
        JOIN personal p ON g.nombre = p.nombre
        JOIN servicios s ON p.servicio_id = s.id
        WHERE g.cronograma_id = 261
    """).fetchall()
    print("\n=== Servicios en 261 ===")
    for row in servicio_row:
        print(f"Servicio ID: {row[0]}, Nombre: {row[1]}")
    
    servicio_id = servicio_row[0][0] if servicio_row else None

    # 3. Counts per day and turn
    if servicio_id:
        print("\n=== Guardias por Día y Turno (M / Mañana) ===")
        # Let's list all shifts starting with M or having M in their name
        df_guards = pd.read_sql_query("""
            SELECT g.fecha, g.turno, count(*) as cantidad
            FROM guardias g
            WHERE g.cronograma_id = 261
            GROUP BY g.fecha, g.turno
            ORDER BY g.fecha, g.turno
        """, conn)
        
        # Filter for turn containing M or similar
        print(df_guards[df_guards['turno'].str.contains('M', case=True)].to_string())

    # 4. Check if PESO_BRECHA_DIARIA_PERSONAL exists in catalog or service rules
    print("\n=== Regla PESO_BRECHA_DIARIA_PERSONAL ===")
    cat_rule = cursor.execute("SELECT * FROM reglas_catalogo WHERE codigo_regla = 'PESO_BRECHA_DIARIA_PERSONAL'").fetchone()
    print("Catálogo:", cat_rule)
    
    if servicio_id:
        srv_rule = cursor.execute("""
            SELECT * FROM servicios_reglas 
            WHERE servicio_id = ? AND codigo_regla = 'PESO_BRECHA_DIARIA_PERSONAL'
        """, (servicio_id,)).fetchone()
        print(f"Servicio {servicio_id} regla:", srv_rule)
        
        srv_ajustes = cursor.execute("""
            SELECT * FROM servicios_reglas_ajustes 
            WHERE servicio_id = ? AND codigo_regla = 'PESO_BRECHA_DIARIA_PERSONAL'
        """, (servicio_id,)).fetchall()
        print(f"Ajustes de regla en servicio {servicio_id}:", srv_ajustes)

    conn.close()

if __name__ == '__main__':
    main()

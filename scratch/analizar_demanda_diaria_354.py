import sqlite3

def main():
    conn = sqlite3.connect("cronograma_inteligente.db")
    cursor = conn.cursor()
    
    # Cantidad de guardias asignadas por dia para Residentes en cronograma 354
    print("--- CONCURRENCIA DIARIA DE RESIDENTES EN CRONOGRAMA 354 ---")
    rows_res = cursor.execute("""
        SELECT g.fecha, COUNT(*)
        FROM guardias g
        JOIN personal p ON g.nombre = p.nombre
        WHERE g.cronograma_id = 354 AND p.rol = 'Residente'
        GROUP BY g.fecha
        ORDER BY g.fecha
    """).fetchall()
    
    max_res = 0
    dias_max_res = []
    for fecha, cant in rows_res:
        print(f"Fecha: {fecha} | Cantidad Residentes: {cant}")
        if cant > max_res:
            max_res = cant
            dias_max_res = [fecha]
        elif cant == max_res:
            dias_max_res.append(fecha)
            
    print(f"\nMaximo de Residentes en un dia: {max_res} (Dias: {dias_max_res})")
    
    # Cantidad de guardias asignadas por dia para Planta en cronograma 354
    print("\n--- CONCURRENCIA DIARIA DE PLANTA EN CRONOGRAMA 354 ---")
    rows_pla = cursor.execute("""
        SELECT g.fecha, COUNT(*)
        FROM guardias g
        JOIN personal p ON g.nombre = p.nombre
        WHERE g.cronograma_id = 354 AND p.rol = 'Planta'
        GROUP BY g.fecha
        ORDER BY g.fecha
    """).fetchall()
    
    max_pla = 0
    dias_max_pla = []
    for fecha, cant in rows_pla:
        if cant > max_pla:
            max_pla = cant
            dias_max_pla = [fecha]
        elif cant == max_pla:
            dias_max_pla.append(fecha)
            
    print(f"Maximo de Planta en un dia: {max_pla} (Dias: {dias_max_pla})")
    
    conn.close()

if __name__ == "__main__":
    main()

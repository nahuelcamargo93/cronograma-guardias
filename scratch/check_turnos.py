import sqlite3

def check_turnos():
    conn = sqlite3.connect('cronograma_inteligente.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, nombre, sigla, horas, servicio_id 
        FROM turnos_config 
        WHERE servicio_id = 2
    """)
    rows = cursor.fetchall()
    print("Turnos config for servicio 2:")
    for r in rows:
        print(f"  ID: {r['id']}, Nombre: {r['nombre']}, Sigla: {r['sigla']}, Horas: {r['horas']}")

    # Let's also check the actual guardias of Abelenda in the original cronograma 437 if it exists
    cursor.execute("""
        SELECT id FROM cronogramas WHERE id = 437
    """)
    crono_exists = cursor.fetchone()
    if crono_exists:
        cursor.execute("""
            SELECT * FROM guardias 
            WHERE cronograma_id = 437 
              AND nombre LIKE '%Abelenda%'
            ORDER BY fecha
        """)
        print("\nGuardias for Abelenda in Cronograma 437:")
        for r in cursor.fetchall():
            print(f"  Fecha: {r['fecha']}, Turno: {r['turno']}, Horas: {r['horas']}")
    else:
        print("\nCronograma 437 does not exist in DB.")

if __name__ == '__main__':
    check_turnos()

import sqlite3

def main():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    query = """
        SELECT DISTINCT c.id, c.fecha_inicio, c.fecha_fin, c.creado_en, c.notas
        FROM cronogramas c
        JOIN guardias g ON c.id = g.cronograma_id
        JOIN personal p ON g.nombre = p.nombre
        WHERE p.servicio_id = 3
        ORDER BY c.id DESC
    """
    rows = cursor.execute(query).fetchall()
    for r in rows:
        print(f"ID {r[0]} | Período: {r[1]} al {r[2]} | Creado: {r[3]} | Notas: {r[4]}")
    conn.close()

if __name__ == '__main__':
    main()

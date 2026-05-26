import sqlite3

def fix():
    conn = sqlite3.connect("cronograma_inteligente.db")
    cursor = conn.cursor()
    
    query = """
        UPDATE personal_reglas_ajustes
        SET parametros_json = '{"por_disponibilidad": {"4": {"completos": 2, "medios": 0}, "5": {"completos": 2, "medios": 1}, "3": {"completos": 1, "medios": 1}, "2": {"completos": 1, "medios": 0}, "1": {"completos": 1, "medios": 0}, "0": {"completos": 0, "medios": 0}}}',
            codigo_regla = 'FINDES_COMPLETOS_Y_MEDIOS'
        WHERE id IN (1398, 1399)
    """
    cursor.execute(query)
    conn.commit()
    print("Fixed rows:", cursor.rowcount)
    conn.close()

if __name__ == '__main__':
    fix()

import sqlite3

def verify_adjustments():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM personal_reglas_ajustes WHERE codigo_regla = 'EXCLUIR_TURNOS';")
    for row in cursor.fetchall():
        print(row)
    conn.close()

if __name__ == "__main__":
    verify_adjustments()

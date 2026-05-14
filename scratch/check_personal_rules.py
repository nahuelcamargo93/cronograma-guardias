import sqlite3

def check_personal_rules():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    names = ['OLGUIN LUCIA', 'NIEVAS CARLA', 'BORIA MAYRA']
    cursor.execute("SELECT * FROM personal_reglas WHERE personal_nombre IN (?, ?, ?);", names)
    for row in cursor.fetchall():
        print(row)
    conn.close()

if __name__ == "__main__":
    check_personal_rules()

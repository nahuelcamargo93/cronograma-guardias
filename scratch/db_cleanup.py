import sqlite3
from database.connection import DB_PATH

def cleanup():
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM personal_reglas_ajustes WHERE personal_nombre = ? AND codigo_regla = ? AND fecha_inicio = ?",
        ('FERNANDEZ Claudia Elizabeth', 'ASIGNACION_FIJA', '2026-06-01')
    )
    conn.commit()
    conn.close()
    print("[CleanUp] BD limpia.")

if __name__ == "__main__":
    cleanup()

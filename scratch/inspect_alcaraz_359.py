import sqlite3
import datetime

DB_PATH = "c:/Users/asus/Desktop/Ryoko/cronograma_inteligente/cronograma_inteligente.db"

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Consultar información del cronograma 359
    crono = cursor.execute("SELECT id, fecha_inicio, fecha_fin, estado FROM cronogramas WHERE id = 359").fetchone()
    print("Cronograma:", crono)
    if not crono:
        return

    fecha_inicio, fecha_fin = crono[1], crono[2]

    # 2. Consultar las guardias de ALCARAZ ELIANA en este cronograma
    print("\nGuardias de ALCARAZ ELIANA:")
    guardias = cursor.execute("""
        SELECT fecha, turno, horas, es_finde 
        FROM guardias 
        WHERE cronograma_id = 359 AND nombre = 'ALCARAZ ELIANA'
        ORDER BY fecha
    """).fetchall()
    for g in guardias:
        print(f"  {g[0]} ({datetime.datetime.strptime(g[0], '%Y-%m-%d').strftime('%A')}): Turno {g[1]}, Horas {g[2]}")

    # 3. Consultar licencias en ese período
    print("\nLicencias de ALCARAZ ELIANA:")
    licencias = cursor.execute("""
        SELECT tipo, fecha_inicio, fecha_fin, metadata 
        FROM licencias 
        WHERE nombre = 'ALCARAZ ELIANA' AND (fecha_inicio <= ? AND fecha_fin >= ?)
    """, (fecha_fin, fecha_inicio)).fetchall()
    for l in licencias:
        print(f"  Tipo: {l[0]}, {l[1]} al {l[2]}, Metadata: {l[3]}")

    # 4. Consultar si tiene FLR asignado
    print("\nFLR Asignados en el cronograma 359:")
    flrs = cursor.execute("""
        SELECT nombre, fecha_inicio 
        FROM flr_asignados 
        WHERE cronograma_id = 359 AND nombre = 'ALCARAZ ELIANA'
    """).fetchall()
    for f in flrs:
        print(f"  {f[0]}: inicia el {f[1]} ({datetime.datetime.strptime(f[1], '%Y-%m-%d').strftime('%A')})")

    # 5. Reglas y suspensiones para ALCARAZ ELIANA
    print("\nReglas individuales de ALCARAZ ELIANA:")
    reglas = cursor.execute("""
        SELECT codigo_regla, parametros_json, activo 
        FROM personal_reglas 
        WHERE personal_nombre = 'ALCARAZ ELIANA'
    """).fetchall()
    for r in reglas:
        print(f"  {r[0]}: {r[1]} (Activo: {r[2]})")

    conn.close()

if __name__ == '__main__':
    main()

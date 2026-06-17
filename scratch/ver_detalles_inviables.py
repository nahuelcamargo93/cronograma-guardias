import sqlite3
import json

def analizar():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    nombres = ["ARCE DANIEL", "CAMPOS PRISCILA", "MIRANDA LUCIANA", "PALANA GRACIELA"]
    
    print("=== DATOS DE PERSONAL ===")
    for n in nombres:
        row = cursor.execute("SELECT nombre, horas_mensuales_reglamentarias, regimen_trabajo, activo FROM personal WHERE nombre = ?", (n,)).fetchone()
        print(f"Nombre: {row[0]} | Horas Reg: {row[1]} | Regimen: {row[2]} | Activo: {row[3]}")
        
    print("\n=== LICENCIAS EN JULIO 2026 ===")
    for n in nombres:
        rows = cursor.execute("SELECT tipo, fecha_inicio, fecha_fin, activa FROM licencias WHERE nombre = ? AND fecha_inicio <= '2026-07-31' AND fecha_fin >= '2026-07-01'", (n,)).fetchall()
        print(f"Nombre: {n} | Licencias:")
        for r in rows:
            print(f"  - Tipo: {r[0]} | {r[1]} a {r[2]} | Activa: {r[3]}")
            
    print("\n=== GUARDIAS EN BORRADOR (ID 437) ===")
    for n in nombres:
        rows = cursor.execute("SELECT fecha, turno, horas FROM guardias WHERE cronograma_id = 437 AND nombre = ? ORDER BY fecha", (n,)).fetchall()
        print(f"Nombre: {n} | Guardias base: {len(rows)}")
        for r in rows:
            print(f"  - {r[0]} | {r[1]} ({r[2]}hs)")

    print("\n=== GUARDIAS EN HISTORIAL DE JUNIO (APROBADO) ===")
    for n in nombres:
        rows = cursor.execute("""
            SELECT g.fecha, g.turno, g.horas 
            FROM guardias g 
            JOIN cronogramas c ON g.cronograma_id = c.id
            WHERE c.estado = 'aprobado' AND g.nombre = ? AND g.fecha BETWEEN '2026-06-22' AND '2026-06-30'
            ORDER BY g.fecha
        """, (n,)).fetchall()
        print(f"Nombre: {n} | Guardias historial: {len(rows)}")
        for r in rows:
            print(f"  - {r[0]} | {r[1]} ({r[2]}hs)")

if __name__ == '__main__':
    analizar()

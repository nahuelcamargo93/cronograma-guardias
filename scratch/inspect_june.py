import sqlite3
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import get_connection

def inspect():
    conn = get_connection()
    # List last 5 cronogramas
    print("--- LAST 5 CRONOGRAMAS ---")
    rows = conn.execute("SELECT id, fecha_inicio, fecha_fin, creado_en, notas, estado FROM cronogramas ORDER BY id DESC LIMIT 5").fetchall()
    for r in rows:
        print(f"ID: {r[0]}, Rango: {r[1]} to {r[2]}, Creado: {r[3]}, Notas: {r[4]}, Estado: {r[5]}")
        
    if not rows:
        print("No cronogramas found.")
        return
        
    # Get the latest cronograma for June 2026
    june_cr = conn.execute("""
        SELECT id, fecha_inicio, fecha_fin FROM cronogramas 
        WHERE fecha_inicio = '2026-06-01' AND fecha_fin = '2026-06-30'
        ORDER BY id DESC LIMIT 1
    """).fetchone()
    
    if not june_cr:
        # Let's search for any cronograma that covers June 2026
        june_cr = conn.execute("""
            SELECT id, fecha_inicio, fecha_fin FROM cronogramas 
            WHERE fecha_inicio <= '2026-06-01' AND fecha_fin >= '2026-06-30'
            ORDER BY id DESC LIMIT 1
        """).fetchone()
        
    if june_cr:
        cr_id, fi, ff = june_cr
        print(f"\nAnalyzing Cronograma ID: {cr_id} ({fi} to {ff})")
        
        # Let's check Mansilla Diego's guardias in this cronograma
        print("\n[MANSILLA Diego's Guardias]")
        guards = conn.execute("""
            SELECT fecha, turno, es_finde, horas
            FROM guardias
            WHERE cronograma_id = ? AND nombre = 'MANSILLA Diego'
            ORDER BY fecha
        """, (cr_id,)).fetchall()
        for g in guards:
            print(f"  Fecha: {g[0]}, Turno: {g[1]}, EsFinde: {g[2]}, Horas: {g[3]}")
            
        print(f"Total Guardias: {len(guards)}, Total Hours: {sum(g[3] for g in guards)}")
        
        # Let's count weekend guardias for everyone in this June cronograma
        # We need to determine the weekends in June 2026:
        # June 1 is Monday.
        # Weekends: June 6-7, 13-14, 20-21, 27-28. Feriados: June 15, June 20.
        # Let's see how many weekend/holiday guardias each person has
        print("\n[Weekend/Holiday guardias per person in June]")
        findes_june = conn.execute("""
            SELECT g.nombre, p.rol, COUNT(*), SUM(g.horas)
            FROM guardias g
            JOIN personal p ON g.nombre = p.nombre
            WHERE g.cronograma_id = ? AND g.es_finde = 1
            GROUP BY g.nombre, p.rol
            ORDER BY p.rol, g.nombre
        """, (cr_id,)).fetchall()
        for f in findes_june:
            print(f"  {f[0]} ({f[1]}): {f[2]} shifts, {f[3]} hours")
            
        # Let's see if anyone has 0 weekends
        all_monit = conn.execute("SELECT nombre FROM personal WHERE servicio_id = 4 AND rol = 'Monitorista'").fetchall()
        assigned_names = {f[0] for f in findes_june}
        print("\n[Monitoristas with 0 weekend shifts in June]")
        for m in all_monit:
            if m[0] not in assigned_names:
                # Get their total hours in the month
                tot_h = conn.execute("SELECT SUM(horas) FROM guardias WHERE cronograma_id = ? AND nombre = ?", (cr_id, m[0])).fetchone()[0] or 0
                print(f"  {m[0]}: 0 weekend shifts, total hours in month: {tot_h}")
    else:
        print("No June cronograma found.")

if __name__ == "__main__":
    inspect()

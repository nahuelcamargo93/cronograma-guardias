import sqlite3
import os
import sys

# Add parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_connection

def inspect():
    conn = get_connection()
    print("--- SERVICIO 4 INFO ---")
    
    # 1. Personal
    print("\n[PERSONAL]")
    personal = conn.execute("SELECT nombre, categoria, rol, activo FROM personal WHERE servicio_id = 4").fetchall()
    for p in personal:
        print(f"Name: {p[0]}, Categoria: {p[1]}, Rol: {p[2]}, Activo: {p[3]}")
        
    # 2. Puestos Habilitados
    print("\n[PUESTOS HABILITADOS PER PERSON]")
    pp = conn.execute("""
        SELECT pp.personal_nombre, p.nombre 
        FROM personal_puestos pp
        JOIN puestos p ON pp.puesto_id = p.id
        WHERE p.servicio_id = 4
    """).fetchall()
    for row in pp:
        print(f"  {row[0]} -> {row[1]}")
        
    # 3. Puestos
    print("\n[PUESTOS]")
    puestos = conn.execute("SELECT id, nombre FROM puestos WHERE servicio_id = 4").fetchall()
    for pst in puestos:
        print(f"ID: {pst[0]}, Nombre: {pst[1]}")
        
    # 4. Demanda Config
    print("\n[DEMANDA CONFIG]")
    demanda = conn.execute("""
        SELECT dc.id, p.nombre, dc.tipo_dia, dc.hora_inicio, dc.hora_fin, dc.cantidad_min, dc.cantidad_max, dc.activo, dc.dias_semana
        FROM demanda_config dc
        JOIN puestos p ON dc.puesto_id = p.id
        WHERE p.servicio_id = 4
    """).fetchall()
    for d in demanda:
        print(f"ID: {d[0]}, Puesto: {d[1]}, TipoDia: {d[2]}, Rango: {d[3]} to {d[4]}, Min: {d[5]}, Max: {d[6]}, Activo: {d[7]}, Dias: {d[8]}")
        
    # 5. Demanda Ajustes
    print("\n[DEMANDA AJUSTES]")
    ajustes_dem = conn.execute("""
        SELECT da.fecha_inicio, da.fecha_fin, p.nombre, da.cantidad_min, da.cantidad_max, da.activo, da.dias_semana
        FROM demanda_ajustes da
        JOIN demanda_config dc ON da.demanda_config_id = dc.id
        JOIN puestos p ON dc.puesto_id = p.id
        WHERE p.servicio_id = 4
    """).fetchall()
    for ad in ajustes_dem:
        print(f"Rango: {ad[0]} to {ad[1]}, Puesto: {ad[2]}, Min: {ad[3]}, Max: {ad[4]}, Activo: {ad[5]}, Dias: {ad[6]}")

    # 6. Turnos Config
    print("\n[TURNOS CONFIG]")
    turnos_cfg = conn.execute("""
        SELECT tc.id, tc.nombre, tc.hora_inicio, tc.horas, tc.dias_semana, tc.puesto_id, p.nombre, tc.activo
        FROM turnos_config tc
        LEFT JOIN puestos p ON tc.puesto_id = p.id
        WHERE tc.servicio_id = 4
    """).fetchall()
    for t in turnos_cfg:
        print(f"ID: {t[0]}, Turno: {t[1]}, HoraInicio: {t[2]}, Horas: {t[3]}, DiasSemana: {t[4]}, Puesto: {t[6]}, Activo: {t[7]}")

    # 7. Reglas de Servicio
    print("\n[REGLAS SERVICIO]")
    reglas_serv = conn.execute("SELECT codigo_regla, parametros_json, activo FROM servicios_reglas WHERE servicio_id = 4").fetchall()
    for r in reglas_serv:
        print(f"Regla: {r[0]}, Activo: {r[2]}")
        print(f"  Params: {r[1]}")

    # 8. Reglas de Personal Ajustes
    print("\n[REGLAS PERSONAL AJUSTES (July 2026)]")
    reglas_pers_aj = conn.execute("""
        SELECT personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo
        FROM personal_reglas_ajustes
        WHERE fecha_inicio <= '2026-07-31' AND fecha_fin >= '2026-07-01'
    """).fetchall()
    for r in reglas_pers_aj:
        print(f"Pers: {r[0]}, Regla: {r[1]}, Rango: {r[2]} to {r[3]}, Accion: {r[4]}, Activo: {r[6]}")
        print(f"  Params: {r[5]}")

    # 9. Último cronograma
    print("\n[ULTIMO CRONOGRAMA]")
    last_cr = conn.execute("SELECT id, fecha_inicio, fecha_fin, creado_en, notas, estado FROM cronogramas ORDER BY id DESC LIMIT 1").fetchone()
    if last_cr:
        cr_id, fi, ff, creado, notas, estado = last_cr
        print(f"ID: {cr_id}, Rango: {fi} to {ff}, Creado: {creado}, Notas: {notas}, Estado: {estado}")
        
        # Guardias de ese cronograma el finde 18/19 de julio
        print("\n[GUARDIAS FINDE 18 Y 19 DE JULIO]")
        guardias = conn.execute("""
            SELECT fecha, turno, nombre, horas 
            FROM guardias 
            WHERE cronograma_id = ? AND fecha IN ('2026-07-18', '2026-07-19')
            ORDER BY fecha, turno, nombre
        """, (cr_id,)).fetchall()
        for g in guardias:
            print(f"Fecha: {g[0]}, Turno: {g[1]}, Nombre: {g[2]}, Horas: {g[3]}")
            
        print("\n[TOTAL GUARDIAS POR PERSONA EN EL FINDE 18/19]")
        tot_finde = conn.execute("""
            SELECT nombre, COUNT(*), SUM(horas)
            FROM guardias
            WHERE cronograma_id = ? AND fecha IN ('2026-07-18', '2026-07-19')
            GROUP BY nombre
            ORDER BY nombre
        """, (cr_id,)).fetchall()
        for t in tot_finde:
            print(f"  {t[0]}: {t[1]} guardias, {t[2]} horas")

        print("\n[TOTAL HORAS EN TODO EL MES POR PERSONA]")
        tot_mes = conn.execute("""
            SELECT nombre, SUM(horas)
            FROM guardias
            WHERE cronograma_id = ?
            GROUP BY nombre
            ORDER BY nombre
        """, (cr_id,)).fetchall()
        for t in tot_mes:
            print(f"  {t[0]}: {t[1]} horas")
    else:
        print("No cronogramas found.")

if __name__ == "__main__":
    inspect()

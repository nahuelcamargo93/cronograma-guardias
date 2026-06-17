import sqlite3
import json
from datetime import date, timedelta
from database.connection import get_connection

def inspect():
    with get_connection() as conn:
        tables = [t[0] for t in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        print(f"Tablas en BD: {tables}")

        # 1. Info del cronograma 476
        crono = conn.execute("SELECT id, fecha_inicio, fecha_fin, estado FROM cronogramas WHERE id = 476").fetchone()
        if not crono:
            print("No se encontró el cronograma 476")
            return
        print(f"Cronograma 476: Desde {crono[1]} hasta {crono[2]}, Estado: {crono[3]}")
        
        # 2. Reglas del servicio 1 activas
        cols_sr = [c[1] for c in conn.execute("PRAGMA table_info(servicios_reglas)").fetchall()]
        reglas = conn.execute("SELECT * FROM servicios_reglas WHERE servicio_id = 1").fetchall()
        print("\nReglas del servicio 1:")
        for r in reglas:
            r_dict = dict(zip(cols_sr, r))
            code = r_dict.get('codigo_regla')
            activo = r_dict.get('activo')
            params = r_dict.get('parametros_json')
            print(f"  - {code}: {params} (Activo: {activo})")

        # 3. Detalle de guardias asignadas en fin de semana en cronograma 476
        cols_p = [c[1] for c in conn.execute("PRAGMA table_info(personal)").fetchall()]
        cargo_col = 'rol' if 'rol' in cols_p else ('categoria' if 'categoria' in cols_p else 'NULL')
        
        guardias = conn.execute(f"""
            SELECT g.nombre, g.fecha, g.turno, g.es_finde, p.{cargo_col}
            FROM guardias g
            JOIN personal p ON g.nombre = p.nombre
            WHERE g.cronograma_id = 476 
            ORDER BY g.nombre, g.fecha
        """).fetchall()
        
        guardias_por_persona = {}
        total_guardias = {}
        
        for nom, fecha_str, turno, es_finde, cargo in guardias:
            total_guardias.setdefault(nom, []).append(f"{fecha_str} ({turno})")
            if not es_finde:
                continue
            f_dt = date.fromisoformat(fecha_str)
            wd = f_dt.weekday() # 5=Sat, 6=Sun
            if wd in (5, 6):
                lunes_dt = f_dt - timedelta(days=wd)
                lunes_str = lunes_dt.isoformat()
                guardias_por_persona.setdefault(nom, {}).setdefault(lunes_str, []).append((fecha_str, turno, cargo))
        
        print("\nDistribución detallada de fines de semana en cronograma 476:")
        for nom, findes in sorted(guardias_por_persona.items()):
            completos = 0
            medios = 0
            detalles = []
            cargo = "Desconocido"
            for lunes_str, g_list in sorted(findes.items()):
                wds = {date.fromisoformat(g[0]).weekday() for g in g_list}
                turnos_str = ", ".join(f"{g[0]} {g[1]}" for g in g_list)
                cargo = g_list[0][2]
                if len(wds) >= 2:
                    completos += 1
                    detalles.append(f"{lunes_str} (Comp: {turnos_str})")
                else:
                    medios += 1
                    detalles.append(f"{lunes_str} (Medio: {turnos_str})")
            tot_g = len(total_guardias.get(nom, []))
            print(f"  {nom} (Cargo/Rol: {cargo}, Total Guardias: {tot_g}): {completos} completos, {medios} medios.\n    Detalles: {'; '.join(detalles)}")

        # 4. Ver qué demandas de fin de semana hay en el servicio 1 (tabla demanda_config y demanda_ajustes)
        print("\n--- CONFIGURACION DE DEMANDA ---")
        cols_dc = [c[1] for c in conn.execute("PRAGMA table_info(demanda_config)").fetchall()]
        # Filtrar por servicio_id si existe, o imprimir todo
        filtro_dc = "WHERE servicio_id = 1" if 'servicio_id' in cols_dc else ""
        dem_config = conn.execute(f"SELECT * FROM demanda_config {filtro_dc}").fetchall()
        for dc in dem_config:
            dc_dict = dict(zip(cols_dc, dc))
            # Filtrar solo si es fin de semana o feriado
            if dc_dict.get('tipo_dia') == 'Finde_Feriado':
                print(f"  Config Demanda Finde: {dc_dict}")
            
        cols_da = [c[1] for c in conn.execute("PRAGMA table_info(demanda_ajustes)").fetchall()]
        filtro_da = "WHERE servicio_id = 1" if 'servicio_id' in cols_da else ""
        dem_ajustes = conn.execute(f"SELECT * FROM demanda_ajustes {filtro_da}").fetchall()
        for da in dem_ajustes:
            print(f"  Ajuste Demanda: {dict(zip(cols_da, da))}")

        # 6. Consultar configuración de turnos y calcular horas de Moyano
        cols_tc = [c[1] for c in conn.execute("PRAGMA table_info(turnos_config)").fetchall()]
        print(f"\nColumnas en turnos_config: {cols_tc}")
        turnos_cfg = conn.execute("SELECT * FROM turnos_config WHERE servicio_id = 1").fetchall()
        duracion_turnos = {}
        for tc in turnos_cfg:
            tc_dict = dict(zip(cols_tc, tc))
            nombre_t = tc_dict.get('nombre') or tc_dict.get('turno')
            horas = tc_dict.get('horas') or tc_dict.get('duracion') or tc_dict.get('duracion_horas')
            # Si no está explícito, calculemos según hora_inicio y hora_fin
            if horas is None:
                hi = tc_dict.get('hora_inicio')
                hf = tc_dict.get('hora_fin')
                if hi and hf:
                    h_ini = int(hi.split(':')[0])
                    h_fin = int(hf.split(':')[0])
                    horas = h_fin - h_ini if h_fin > h_ini else (24 - h_ini + h_fin)
            duracion_turnos[nombre_t] = horas
            print(f"  Turno {nombre_t}: {horas} horas ({tc_dict.get('hora_inicio')} a {tc_dict.get('hora_fin')})")

        # 7. Consultar reglas de personal y ajustes
        print("\n--- REGLAS DE PERSONAL ---")
        cols_pr = [c[1] for c in conn.execute("PRAGMA table_info(personal_reglas)").fetchall()]
        print(f"Columnas en personal_reglas: {cols_pr}")
        p_reglas = conn.execute("""
            SELECT * FROM personal_reglas 
            WHERE personal_nombre IN ('Moyano, Fernando', 'Franco, Leandro')
        """).fetchall()
        for pr in p_reglas:
            print(f"  Regla Personal: {dict(zip(cols_pr, pr))}")
            
        print("\n--- AJUSTES DE REGLAS DE PERSONAL ---")
        cols_pra = [c[1] for c in conn.execute("PRAGMA table_info(personal_reglas_ajustes)").fetchall()]
        print(f"Columnas en personal_reglas_ajustes: {cols_pra}")
        p_ajustes = conn.execute("""
            SELECT * FROM personal_reglas_ajustes 
            WHERE personal_nombre IN ('Moyano, Fernando', 'Franco, Leandro')
        """).fetchall()
        for pra in p_ajustes:
            print(f"  Ajuste Personal: {dict(zip(cols_pra, pra))}")

if __name__ == '__main__':
    inspect()

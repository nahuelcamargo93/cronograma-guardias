import sqlite3
import json
from datetime import date, timedelta
import pandas as pd

def main():
    db_path = 'cronograma_inteligente.db'
    conn = sqlite3.connect(db_path)
    try:
        # 1. Obtener config de la regla
        row_config = conn.execute("""
            SELECT parametros_json FROM servicios_reglas 
            WHERE servicio_id = 1 AND codigo_regla = 'PESO_EQUIDAD_FSL'
        """).fetchone()
        
        if not row_config:
            print("No se encontró la regla PESO_EQUIDAD_FSL en el Servicio 1.")
            return
            
        config = json.loads(row_config[0])
        print("=== CONFIGURACIÓN DE REGLA ===")
        print(json.dumps(config, indent=2))
        
        niv_conf = config.get("nivelacion_historica", {})
        if not niv_conf.get("activo"):
            print("La nivelación histórica no está activa.")
            return
            
        fecha_inicio_niv = niv_conf.get("fecha_inicio", "2026-01-01")
        print(f"Fecha de inicio de nivelación: {fecha_inicio_niv}")
        
        # 2. Obtener cronograma de Julio 2026
        crono_actual = conn.execute("""
            SELECT id, fecha_inicio, fecha_fin, estado FROM cronogramas
            WHERE fecha_inicio = '2026-07-01'
            ORDER BY id DESC LIMIT 1
        """).fetchone()
        
        if not crono_actual:
            print("No se encontró cronograma generado para Julio de 2026.")
            return
            
        c_id_actual, c_ini_actual, c_fin_actual, estado_actual = crono_actual
        print(f"Cronograma actual: ID={c_id_actual}, Rango={c_ini_actual} a {c_fin_actual}, Estado={estado_actual}")
        
        # 3. Obtener personal del Servicio 1
        personal = conn.execute("""
            SELECT nombre FROM personal WHERE servicio_id = 1 AND COALESCE(activo, 1) = 1
        """).fetchall()
        empleados = [p[0] for p in personal]
        
        # 4. Calcular fecha de primera guardia (fecha_inicio_historial) para cada uno
        fecha_inicio_historial = {}
        for emp in empleados:
            row_fd = conn.execute("""
                SELECT MIN(fecha) FROM guardias g
                JOIN cronogramas c ON g.cronograma_id = c.id
                WHERE g.nombre = ? AND c.estado = 'aprobado' AND c.fecha_inicio < '2026-07-01'
            """, (emp,)).fetchone()
            fecha_inicio_historial[emp] = row_fd[0] if row_fd else None
            
        # 5. Obtener cronogramas aprobados en el rango histórico de nivelación
        fecha_fin_hist_dt = date.fromisoformat(c_ini_actual) - timedelta(days=1)
        fecha_fin_hist_str = fecha_fin_hist_dt.isoformat()
        
        cronos_hist = conn.execute("""
            SELECT DISTINCT c.id, c.fecha_inicio, c.fecha_fin
            FROM cronogramas c
            JOIN guardias g ON c.id = g.cronograma_id
            JOIN personal p ON g.nombre = p.nombre
            WHERE p.servicio_id = 1
              AND c.estado = 'aprobado'
              AND c.fecha_inicio >= ?
              AND c.fecha_fin <= ?
            ORDER BY c.fecha_inicio
        """, (fecha_inicio_niv, fecha_fin_hist_str)).fetchall()
        
        fl3_hist = {emp: 0.0 for emp in empleados}
        fl4_hist = {emp: 0.0 for emp in empleados}
        
        if cronos_hist:
            crono_ids = [c[0] for c in cronos_hist]
            placeholders = ",".join("?" for _ in crono_ids)
            
            # Bloques
            bloques_hist = conn.execute(f"""
                SELECT cronograma_id, fecha_inicio, fecha_fin, tipo
                FROM bloques_finde_largo
                WHERE cronograma_id IN ({placeholders})
            """, crono_ids).fetchall()
            
            # Guardias
            guardias_hist = conn.execute(f"""
                SELECT g.nombre, g.fecha, g.cronograma_id
                FROM guardias g
                JOIN personal p ON g.nombre = p.nombre
                WHERE g.cronograma_id IN ({placeholders})
                  AND g.es_finde = 1
                  AND p.servicio_id = 1
            """, crono_ids).fetchall()
            
            guardias_by_emp_crono = {}
            for nom, fecha_str, c_id in guardias_hist:
                guardias_by_emp_crono.setdefault((c_id, nom), set()).add(fecha_str)
                
            for c_id, c_ini_str, c_fin_str in cronos_hist:
                c_fin_dt = date.fromisoformat(c_fin_str)
                
                # Activos en este cronograma
                activos = []
                for emp in empleados:
                    if fecha_inicio_historial[emp] and fecha_inicio_historial[emp] <= c_fin_str:
                        activos.append(emp)
                if not activos:
                    activos = empleados
                    
                c_bloques = [b for b in bloques_hist if b[0] == c_id]
                trabajados_fl3 = {emp: 0 for emp in activos}
                trabajados_fl4 = {emp: 0 for emp in activos}
                tot_fl3 = 0
                tot_fl4 = 0
                
                for _, fi_str, ff_str, tipo in c_bloques:
                    fi_dt = date.fromisoformat(fi_str)
                    ff_dt = date.fromisoformat(ff_str)
                    bloque_fechas = [(fi_dt + timedelta(days=d)).isoformat() for d in range((ff_dt - fi_dt).days + 1)]
                    
                    for emp in activos:
                        emp_g_dates = guardias_by_emp_crono.get((c_id, emp), set())
                        if any(d_str in emp_g_dates for d_str in bloque_fechas):
                            if tipo == 3:
                                trabajados_fl3[emp] += 1
                                tot_fl3 += 1
                            elif tipo >= 4:
                                trabajados_fl4[emp] += 1
                                tot_fl4 += 1
                                
                num_activos = len(activos)
                avg_fl3 = tot_fl3 / num_activos
                avg_fl4 = tot_fl4 / num_activos
                
                for emp in empleados:
                    if emp in activos:
                        fl3_hist[emp] += trabajados_fl3[emp]
                        fl4_hist[emp] += trabajados_fl4[emp]
                    else:
                        fl3_hist[emp] += avg_fl3
                        fl4_hist[emp] += avg_fl4
                        
        # 6. Calcular FSL del mes actual (Julio 2026)
        bloques_actual = conn.execute("""
            SELECT fecha_inicio, fecha_fin, tipo
            FROM bloques_finde_largo
            WHERE cronograma_id = ?
        """, (c_id_actual,)).fetchall()
        
        guardias_actual = conn.execute("""
            SELECT nombre, fecha FROM guardias
            WHERE cronograma_id = ? AND es_finde = 1
        """, (c_id_actual,)).fetchall()
        
        guardias_by_emp_actual = {}
        for nom, fecha_str in guardias_actual:
            guardias_by_emp_actual.setdefault(nom, set()).add(fecha_str)
            
        fl3_actual = {emp: 0 for emp in empleados}
        fl4_actual = {emp: 0 for emp in empleados}
        
        for fi_str, ff_str, tipo in bloques_actual:
            fi_dt = date.fromisoformat(fi_str)
            ff_dt = date.fromisoformat(ff_str)
            bloque_fechas = [(fi_dt + timedelta(days=d)).isoformat() for d in range((ff_dt - fi_dt).days + 1)]
            
            for emp in empleados:
                emp_g_dates = guardias_by_emp_actual.get(emp, set())
                if any(d_str in emp_g_dates for d_str in bloque_fechas):
                    if tipo == 3:
                        fl3_actual[emp] += 1
                    elif tipo >= 4:
                        fl4_actual[emp] += 1
                        
        # 7. Armar reporte comparativo
        filas = []
        for emp in empleados:
            f_ini = fecha_inicio_historial[emp]
            h3 = fl3_hist[emp]
            h4 = fl4_hist[emp]
            h3_int = int(round(h3))
            h4_int = int(round(h4))
            
            a3 = fl3_actual[emp]
            a4 = fl4_actual[emp]
            
            tot3 = h3_int + a3
            tot4 = h4_int + a4
            
            filas.append({
                "Empleado": emp,
                "Primer_Guardia": f_ini or "Ninguna",
                "Hist_FL3_Virtual": round(h3, 2),
                "Hist_FL3_Round": h3_int,
                "Mes_FL3": a3,
                "Total_FL3": tot3,
                "Hist_FL4_Virtual": round(h4, 2),
                "Hist_FL4_Round": h4_int,
                "Mes_FL4": a4,
                "Total_FL4": tot4
            })
            
        df = pd.DataFrame(filas)
        print("\n=== AUDITORÍA DE NIVELACIÓN DE FSL (JULIO 2026) ===")
        print(df.to_string(index=False))
        
        # Mostrar brechas
        print("\nBrechas Totales:")
        print(f"Brecha FL3 (Max - Min): {df['Total_FL3'].max() - df['Total_FL3'].min()}")
        print(f"Brecha FL4 (Max - Min): {df['Total_FL4'].max() - df['Total_FL4'].min()}")
        
    finally:
        conn.close()

if __name__ == '__main__':
    main()

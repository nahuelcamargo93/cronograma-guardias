import sqlite3
import pandas as pd
from datetime import datetime, timedelta

def run_capacity_diagnostic():
    FECHA_INICIO = "2026-05-25"
    FECHA_FIN = "2026-07-05"
    fecha_inicio_dt = datetime.strptime(FECHA_INICIO, "%Y-%m-%d")
    fecha_fin_dt = datetime.strptime(FECHA_FIN, "%Y-%m-%d")
    total_dias = (fecha_fin_dt - fecha_inicio_dt).days + 1
    
    conn = sqlite3.connect('cronograma_inteligente.db')
    df_personal = pd.read_sql("SELECT nombre as Nombre FROM personal", conn)
    
    # Licencias
    licencias = pd.read_sql("SELECT nombre, tipo, fecha_inicio, fecha_fin FROM licencias", conn)
    
    # Config Turnos (Default)
    # Semana: Mañana_UTI(5), Tarde_UTI(3), Mañana_UCO(1), Tarde_UCO(1), Noche(2) = 12 total
    # Finde: Dia_UTI(2), Dia_UCO(1), Noche(2) = 5 total
    
    # Ajustes
    ajustes = pd.read_sql("""
        SELECT a.fecha_inicio, c.nombre as turno_nombre, a.vacantes 
        FROM turnos_ajustes a
        JOIN turnos_config c ON a.turno_config_id = c.id
    """, conn)
    
    print(f"{'Día':<4} | {'Fecha':<10} | {'Nec':<4} | {'Disp':<4} | {'Margen':<6} | {'Conflicto?'}")
    print("-" * 50)
    
    for d in range(total_dias):
        fecha_d = fecha_inicio_dt + timedelta(days=d)
        fecha_str = fecha_d.strftime("%Y-%m-%d")
        dia_semana = fecha_d.weekday()
        es_finde = dia_semana >= 5
        
        # Necesarios
        if es_finde:
            n_necesarios = 5
        else:
            n_necesarios = 12
            
        # Aplicar ajustes
        ajustes_dia = ajustes[ajustes['fecha_inicio'] <= fecha_str]
        # Simplificación: el último ajuste que empezó antes de hoy aplica (si no ha terminado)
        # Pero tus ajustes son por semana.
        # Busquemos el ajuste exacto para la semana
        semana_inicio = (fecha_d - timedelta(days=dia_semana)).strftime("%Y-%m-%d")
        ajustes_sem = ajustes[ajustes['fecha_inicio'] == semana_inicio]
        
        if not ajustes_sem.empty:
            # Recalcular n_necesarios basado en ajustes
            # Necesitamos el default de los que NO están en ajustes
            if es_finde:
                # Finde no suele tener ajustes en tu plan
                pass
            else:
                # Turnos: Mañana_UTI(5), Tarde_UTI(3), Mañana_UCO(1), Tarde_UCO(1), Noche(2)
                m_uti = ajustes_sem[ajustes_sem['turno_nombre'] == 'Mañana_UTI']
                t_uti = ajustes_sem[ajustes_sem['turno_nombre'] == 'Tarde_UTI']
                
                v_m_uti = m_uti.iloc[0]['vacantes'] if not m_uti.empty else 5
                v_t_uti = t_uti.iloc[0]['vacantes'] if not t_uti.empty else 3
                n_necesarios = v_m_uti + v_t_uti + 1 + 1 + 2
        
        # Disponibles
        n_disponibles = 0
        for name in df_personal['Nombre']:
            lic = licencias[(licencias['nombre'] == name) & (licencias['fecha_inicio'] <= fecha_str) & (licencias['fecha_fin'] >= fecha_str)]
            if lic.empty:
                n_disponibles += 1
        
        margen = n_disponibles - n_necesarios
        conflicto = "!!!" if margen < 2 else ""
        print(f"{d:<4} | {fecha_str} | {n_necesarios:<4} | {n_disponibles:<4} | {margen:<6} | {conflicto}")

if __name__ == "__main__":
    run_capacity_diagnostic()

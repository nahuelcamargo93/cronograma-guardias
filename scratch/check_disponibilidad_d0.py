import sqlite3
from datetime import datetime, date, timedelta

# Conexión
conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

# Cargar licencias activas
cursor.execute("SELECT nombre, tipo, fecha_inicio, fecha_fin FROM licencias WHERE COALESCE(activa, 1) = 1")
licencias = cursor.fetchall()

def tiene_licencia(nombre, fecha_str):
    d = date.fromisoformat(fecha_str)
    for l_nombre, l_tipo, fi, ff in licencias:
        if l_nombre == nombre:
            if date.fromisoformat(fi) <= d <= date.fromisoformat(ff):
                return l_tipo
    return None

# Cargar reglas personales
cursor.execute("SELECT personal_nombre, codigo_regla, parametros_json FROM personal_reglas WHERE activo = 1")
reglas = {}
for name, code, params in cursor.fetchall():
    reglas.setdefault(name, {})[code] = params

# Cargar guardias previas de crono 492 (asumiendo aprobado)
cursor.execute("SELECT nombre, fecha, turno, horas FROM guardias WHERE cronograma_id = 492")
guardias_492 = {}
for name, fecha, turno, horas in cursor.fetchall():
    guardias_492.setdefault(name, []).append({'fecha': fecha, 'turno': turno, 'horas': horas})

# Médicos del servicio 3 activos
cursor.execute("SELECT nombre, rol FROM personal WHERE servicio_id = 3 AND COALESCE(activo, 1) = 1")
medicos = cursor.fetchall()

print("=== Analisis de Disponibilidad para el 1 de Julio de 2026 (d0) y 2 de Julio (d1) ===")

def analizar_dia(fecha_analisis):
    print(f"\nFecha: {fecha_analisis}")
    dispo_planta = []
    dispo_residente = []
    
    for nombre, rol in medicos:
        motivos_bloqueo = []
        
        # 1. Licencia
        lic = tiene_licencia(nombre, fecha_analisis)
        if lic:
            motivos_bloqueo.append(f"Licencia ({lic})")
            
        # 2. Descanso obligatorio desde crono 492
        g_previas = guardias_492.get(nombre, [])
        for gp in g_previas:
            fecha_gp = date.fromisoformat(gp['fecha'])
            T_prev = gp['turno']
            D_prev = gp['horas']
            
            # Descanso obligatorio: 48 hs para G_Planta/G_Residente, 12 para D, 36 para N
            R_prev = 48 if 'G_' in T_prev else (36 if 'N_' in T_prev or T_prev == 'Noche' else 12)
            
            H_start_prev = 8.0 # fallback
            if "Noche" in T_prev: H_start_prev = 20.0
            elif "Tarde" in T_prev: H_start_prev = 14.0
            
            H_fin_prev = H_start_prev + D_prev
            
            d_diff = (date.fromisoformat(fecha_analisis) - fecha_gp).days
            
            # Para el peor caso (turno de mañana que empieza a las 08:00)
            descanso_real_manana = d_diff * 24 + 8.0 - H_fin_prev
            if descanso_real_manana < R_prev:
                motivos_bloqueo.append(f"Descanso insuficiente desde {gp['fecha']} {T_prev} (descanso real Manana: {descanso_real_manana}hs < {R_prev}hs)")
                
        # 3. Solo asignaciones fijas sin asignación fija hoy
        tiene_saf = 'SOLO_ASIGNACIONES_FIJAS' in reglas.get(nombre, {})
        if tiene_saf:
            p_fijas = reglas.get(nombre, {}).get('ASIGNACION_FIJA')
            has_fixed_today = False
            if p_fijas:
                import json
                try:
                    asigs = json.loads(p_fijas)
                    if not isinstance(asigs, list): asigs = [asigs]
                    mapa_dias = {"Monday": "Lunes", "Tuesday": "Martes", "Wednesday": "Miercoles", "Thursday": "Jueves", "Friday": "Viernes", "Saturday": "Sabado", "Sunday": "Domingo"}
                    dia_semana_esp = mapa_dias[datetime.strptime(fecha_analisis, "%Y-%m-%d").strftime("%A")]
                    for asig in asigs:
                        if asig.get('Fecha') == fecha_analisis:
                            has_fixed_today = True
                        elif asig.get('Dia') == dia_semana_esp:
                            has_fixed_today = True
                except Exception as e:
                    pass
            if not has_fixed_today:
                motivos_bloqueo.append("Regla SOLO_ASIGNACIONES_FIJAS activa (y sin asignacion fija hoy)")
                
        # 4. Francos forzados de personal_reglas_ajustes
        cursor.execute("""
            SELECT 1 FROM personal_reglas_ajustes
            WHERE personal_nombre = ? AND codigo_regla = 'FRANCO_FORZADO' AND activo = 1
              AND fecha_inicio <= ? AND fecha_fin >= ?
        """, (nombre, fecha_analisis, fecha_analisis))
        if cursor.fetchone():
            motivos_bloqueo.append("Franco Forzado (Ajuste temporal)")

        if motivos_bloqueo:
            print(f"[X] {nombre:<35} ({rol:<9}) | BLOQUEADO: {', '.join(motivos_bloqueo)}")
        else:
            print(f"[OK] {nombre:<35} ({rol:<9}) | DISPONIBLE")
            if rol == 'Planta':
                dispo_planta.append(nombre)
            else:
                dispo_residente.append(nombre)
                
    print(f"Total Planta disponibles: {len(dispo_planta)} -> {dispo_planta}")
    print(f"Total Residente disponibles: {len(dispo_residente)} -> {dispo_residente}")

analizar_dia("2026-07-01")
analizar_dia("2026-07-02")

conn.close()

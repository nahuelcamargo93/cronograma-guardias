import sys; sys.stdout.reconfigure(encoding='utf-8')
import sqlite3
from datetime import date, timedelta
from collections import defaultdict

def run_check():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cur = conn.cursor()
    
    CRONOGRAMA_ID = 122
    FECHA_INICIO = "2026-07-01"
    FECHA_FIN    = "2026-07-31"
    fecha_inicio_dt = date.fromisoformat(FECHA_INICIO)
    fecha_fin_dt    = date.fromisoformat(FECHA_FIN)
    dias_del_bloque = (fecha_fin_dt - fecha_inicio_dt).days + 1
    
    # Weeks mapping (Lun-Dom)
    dias_por_semana_calendario = {}
    for d in range(dias_del_bloque):
        fecha_d = fecha_inicio_dt + timedelta(days=d)
        lunes_semana = fecha_d - timedelta(days=fecha_d.weekday())
        sem_key = lunes_semana.isoformat()
        dias_por_semana_calendario.setdefault(sem_key, []).append(d)
        
    # Get assignments
    cur.execute("SELECT nombre, fecha, turno FROM guardias WHERE cronograma_id=?", (CRONOGRAMA_ID,))
    guardias = cur.fetchall()
    
    por_persona = defaultdict(list)
    for nombre, fecha, turno in guardias:
        por_persona[nombre].append((date.fromisoformat(fecha), turno))
        
    # Get licencias
    cur.execute("SELECT nombre, fecha_inicio, fecha_fin FROM licencias WHERE fecha_inicio <= ? AND fecha_fin >= ?", (FECHA_FIN, FECHA_INICIO))
    lic_raw = cur.fetchall()
    licencias_por_persona = defaultdict(set)
    for nombre, fi, ff in lic_raw:
        fi_dt = date.fromisoformat(fi)
        ff_dt = date.fromisoformat(ff)
        for d in range(dias_del_bloque):
            fecha_d = fecha_inicio_dt + timedelta(days=d)
            if fi_dt <= fecha_d <= ff_dt:
                licencias_por_persona[nombre].add(d)
                
    # Get all service 2 nurses
    cur.execute("SELECT nombre FROM personal WHERE servicio_id=2")
    nursing_staff = [r[0] for r in cur.fetchall()]
    
    # Map turnos to families
    def get_families(turno):
        if turno == 'M': return {'M'}
        if turno == 'T': return {'T'}
        if turno == 'TN': return {'TN'}
        if turno == 'N': return {'N'}
        if turno == 'MT': return {'M', 'T'}
        if turno == 'TNN': return {'TN', 'N'}
        return set()
        
    print(f"Verificación de Rotación Mensual (Cronograma {CRONOGRAMA_ID})")
    print(f"{'Nombre':<30} {'S.Disp':>6} {'Req':>3} {'Fam.Trab':>8}  Status")
    print("-" * 65)
    
    failed_count = 0
    for nombre in sorted(nursing_staff):
        dias_lic = licencias_por_persona[nombre]
        
        # Calculate semanas_disponibles
        semanas_disponibles = 0
        for sem_key_rot, dias_sem_rot in dias_por_semana_calendario.items():
            if len(dias_sem_rot) >= 4:
                dias_libres_rot = [d for d in dias_sem_rot if d not in dias_lic]
                if len(dias_libres_rot) >= 4:
                    semanas_disponibles += 1
                    
        req_families = min(4, semanas_disponibles)
        
        # Calculate families actually worked
        worked_families = set()
        for fd, turno in por_persona.get(nombre, []):
            worked_families.update(get_families(turno))
            
        num_worked = len(worked_families)
        
        status = "OK"
        if num_worked < req_families:
            status = "❌ FALLÓ"
            failed_count += 1
            
        print(f"{nombre:<30} {semanas_disponibles:>6} {req_families:>3} {num_worked:>8} ({','.join(sorted(worked_families)) if worked_families else '-'})  {status}")
        
    print("-" * 65)
    if failed_count == 0:
        print("ÉXITO: ¡Todos los enfermeros cumplieron con la rotación obligatoria ajustada por licencia!")
    else:
        print(f"ALERTA: {failed_count} enfermeros no cumplieron con la rotación obligatoria.")
        
    conn.close()

if __name__ == '__main__':
    run_check()

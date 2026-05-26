import sys
sys.stdout.reconfigure(encoding='utf-8')
from datetime import date, timedelta

FECHA_INICIO = "2026-07-01"
FECHA_FIN    = "2026-07-31"

fecha_inicio_dt = date.fromisoformat(FECHA_INICIO)
fecha_fin_dt    = date.fromisoformat(FECHA_FIN)
dias_del_bloque = (fecha_fin_dt - fecha_inicio_dt).days + 1

dias_por_semana_calendario = {}
for d in range(dias_del_bloque):
    fecha_d = fecha_inicio_dt + timedelta(days=d)
    lunes_semana = fecha_d - timedelta(days=fecha_d.weekday())
    sem_key = lunes_semana.isoformat()
    dias_por_semana_calendario.setdefault(sem_key, []).append(d)

print(f"Julio 2026 empieza el: {fecha_inicio_dt.strftime('%A %d/%m/%Y')}")
print(f"Total dias en bloque: {dias_del_bloque}")
print(f"\nSemanas calendario en el bloque:")
for sem_key, dias_sem in sorted(dias_por_semana_calendario.items()):
    lunes_dt = date.fromisoformat(sem_key)
    domingo_dt = lunes_dt + timedelta(days=6)
    dias_en_mes = len(dias_sem)
    cuenta = "CUENTA" if dias_en_mes >= 4 else "NO CUENTA (< 4 dias)"
    print(f"  {sem_key} (Lun {lunes_dt.strftime('%d/%m')} - Dom {domingo_dt.strftime('%d/%m')}): {dias_en_mes} dias -> {cuenta}")

total_cuenta = sum(1 for dias in dias_por_semana_calendario.values() if len(dias) >= 4)
print(f"\nTotal semanas que cuentan (>= 4 dias): {total_cuenta}")
print(f"Para empleado sin licencias: req_families = min(4, {total_cuenta}) = {min(4, total_cuenta)}")

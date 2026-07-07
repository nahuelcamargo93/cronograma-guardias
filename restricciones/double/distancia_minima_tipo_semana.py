"""restricciones/double/distancia_minima_tipo_semana.py — DISTANCIA_MINIMA_TIPO_SEMANA

Asegura que un empleado mantenga una distancia mínima (en semanas) entre semanas
del mismo tipo de turno (ej: Noche o Tarde Noche).

JSON de configuración:
{
    "modo": "HARD",            # "HARD" o "SOFT"
    "peso_soft": 10000,
    "distancias": {
        "N": 3,                # Noche: mínimo 3 semanas libres entre semanas N (ventana de 4)
        "TN": 3                # Tarde Noche: mínimo 3 semanas libres entre semanas TN (ventana de 4)
    }
}
"""
from datetime import date, timedelta
from restricciones.cargador import add_hard
from restricciones.hard._utils import determinar_familia_ganadora
import rule_engine as _re


def apply(modelo, ctx) -> None:
    params = ctx.reglas_servicio.get('DISTANCIA_MINIMA_TIPO_SEMANA')
    if not params:
        return

    distancias = params.get('distancias')
    if not distancias or not isinstance(distancias, dict):
        return

    modo = params.get('modo', 'SOFT').upper()
    peso_soft = params.get('peso_soft', 10000)

    fecha_inicio_dt = date.fromisoformat(ctx.fecha_inicio)

    # Construir mapa semana → lista de días (índices)
    dias_por_semana: dict[str, list[int]] = {}
    for d in range(ctx.dias):
        fd = fecha_inicio_dt + timedelta(days=d)
        lunes = (fd - timedelta(days=fd.weekday())).isoformat()
        dias_por_semana.setdefault(lunes, []).append(d)

    semanas_keys = sorted(dias_por_semana.keys())
    if not semanas_keys:
        return

    primer_lunes = date.fromisoformat(semanas_keys[0])

    for emp in ctx.empleados:
        nombre = emp.nombre
        nombre_safe = nombre.replace(' ', '_').replace(',', '').replace('-', '_')
        hist_prev = ctx.historial_semana_previa.get(nombre, []) if ctx.historial_semana_previa else []

        for fam, d_min in distancias.items():
            try:
                d_min = int(d_min)
            except (ValueError, TypeError):
                continue

            w = d_min + 1
            if w <= 1:
                continue

            # 1. Determinar el estado de las d_min semanas previas a partir del historial (w - 1 = d_min)
            secuencia_hist = []
            for sem_idx in range(w - 1, 0, -1):
                lunes_prev_dt = primer_lunes - timedelta(days=sem_idx * 7)
                ganador_prev = determinar_familia_ganadora(hist_prev, lunes_prev_dt)
                hist_flag = 1 if ganador_prev == fam else 0
                secuencia_hist.append(hist_flag)

            # 2. Formar la secuencia de variables
            secuencia = list(secuencia_hist)
            for sem_key in semanas_keys:
                ganador_sem = determinar_familia_ganadora(hist_prev, date.fromisoformat(sem_key))
                if ganador_sem is not None:
                    hist_flag = 1 if ganador_sem == fam else 0
                    secuencia.append(hist_flag)
                else:
                    v_dict = ctx.vars_turno_sem.get((nombre, sem_key))
                    if v_dict and fam in v_dict:
                        secuencia.append(v_dict[fam])

            if len(secuencia) < 2:
                continue

            # 3. Aplicar restricción en ventanas deslizantes de tamaño w
            for i in range(len(secuencia) - w + 1):
                vars_ventana = secuencia[i:i+w]

                # Si todos son constantes enteras (0 o 1), no hace falta agregar restricción al solver
                if all(isinstance(v, int) for v in vars_ventana):
                    continue

                # Separar constantes (historial) de variables (planificación)
                constantes = [v for v in vars_ventana if isinstance(v, int)]
                variables = [v for v in vars_ventana if not isinstance(v, int)]

                sum_const = sum(constantes)
                rhs = max(0, 1 - sum_const)

                if modo == 'HARD':
                    add_hard(
                        modelo, ctx,
                        modelo.Add(sum(variables) <= rhs),
                        f"{nombre}_dist_{fam}_w{i}"
                    )
                else:
                    viol = modelo.NewIntVar(0, len(variables), f"viol_dist_{fam}_{nombre_safe}_w{i}")
                    modelo.Add(sum(variables) <= rhs + viol)
                    ctx.penalizaciones_soft.append(viol * peso_soft)

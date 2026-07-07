"""restricciones/double/min_francos_consecutivos.py — Agrupación mínima de francos consecutivos.

Esta regla asegura que los días de franco de un profesional se den en bloques
de al menos `min_francos` días consecutivos. Un día franco aislado (sin ningún
vecino también franco) es penalizado (SOFT) o prohibido (HARD).
Los días de licencia no se consideran francos y no rompen ni forman bloques.
Regla: MIN_FRANCOS_CONSECUTIVOS
"""
from restricciones.cargador import add_hard
from restricciones.hard._utils import is_finde
import rule_engine as _re


def apply(modelo, ctx) -> None:
    for emp in ctx.empleados:
        params = _re.resolver_parametros_regla(
            'MIN_FRANCOS_CONSECUTIVOS', emp.nombre, ctx.fecha_inicio,
            ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
        )
        if not _re.regla_existe(params) or _re.regla_suspendida(params):
            continue

        min_francos = params.get('min_francos', 2) if isinstance(params, dict) else 2
        modo        = params.get('modo', 'SOFT').upper() if isinstance(params, dict) else 'SOFT'
        peso_soft   = params.get('peso_soft', 8000) if isinstance(params, dict) else 8000

        if min_francos < 2:
            continue  # Con min=1 cualquier franco es válido; no hay nada que restringir.

        # ── Paso 1: construir variable F[d] = es franco laboral (excluye licencias) ──
        traba_dia = {}
        for d in range(ctx.dias):
            td = "Finde_Feriado" if is_finde(d, ctx.offset_dia, ctx.feriados) else "Semana"
            t_dia = [
                ctx.turnos[(emp.nombre, d, t)]
                for t in ctx.demanda_turnos.get(td, {}).keys()
                if (emp.nombre, d, t) in ctx.turnos
            ]
            if t_dia:
                v = modelo.NewBoolVar(f"td_mfc_{emp.nombre}_d{d}")
                modelo.Add(v == sum(t_dia))
                traba_dia[d] = v
            else:
                traba_dia[d] = 0

        F = {}
        for d in range(ctx.dias):
            if d in emp.dias_licencia:
                F[d] = None  # día de licencia: excluido del análisis
                continue
            v_f = modelo.NewBoolVar(f"franco_mfc_{emp.nombre}_d{d}")
            # F[d] = 1 - traba_dia[d]  (solo si no es licencia)
            modelo.Add(v_f + traba_dia[d] == 1)
            F[d] = v_f

        # ── Paso 2: detectar francos "aislados" según min_francos ──
        #
        # Para min_francos = 2:
        #   aislado[d] = 1  ↔  F[d]=1  ∧  F[d-1]=0  ∧  F[d+1]=0
        #   (el día franco no tiene ningún vecino adyacente también franco)
        #
        # Para min_francos = 3:
        #   aislado[d] = 1  ↔  F[d]=1  ∧  (F[d-1]+F[d+1]) < 2
        #   es decir, el bloque del que forma parte tiene menos de 3 días.
        #   Equivalentemente penalizamos si la suma de la ventana [d-1, d, d+1] < min_francos.
        #
        # Formulación generalizada para cualquier min_francos m:
        #   Una ventana de tamaño (2*m - 1) centrada en d.
        #   Si F[d]=1, la suma de esa ventana debe ser >= min_francos.
        #   Violación = F[d]=1  ∧  sum_ventana < min_francos
        #
        # Para min_francos=2 la ventana es [-1, 0, +1] (tamaño 3):
        #   si F[d]=1, necesitamos sum(F[d-1..d+1]) >= 2  →  al menos un vecino franco.
        # Para min_francos=3 la ventana es [-2, -1, 0, +1, +2] (tamaño 5):
        #   si F[d]=1, necesitamos sum(F[d-2..d+2]) >= 3.
        #
        # Implementación con variable auxiliar `aislado_d`:
        #   aislado_d = 1  implica  F[d]=1
        #   aislado_d = 1  implica  sum_ventana - 1 < min_francos - 1
        #                           sum_ventana <= min_francos - 1
        # Usamos la dirección inversa: si F[d]=1 y sum_ventana < min_francos → aislado.

        radio = min_francos - 1  # cuántos vecinos necesitamos a cada lado

        for d in range(ctx.dias):
            if F[d] is None:
                continue  # licencia

            # Construir la ventana centrada en d (tamaño 2*radio+1 = 2*min_francos-1)
            ventana = []
            for offset in range(-radio, radio + 1):
                nd = d + offset
                if nd < 0 or nd >= ctx.dias:
                    continue  # bordes del mes
                if F[nd] is None:
                    continue  # días de licencia no cuentan
                ventana.append(F[nd])

            if not ventana:
                continue

            # Variable aislado[d]: 1 si F[d]=1 y la ventana tiene menos de min_francos francos
            v_aislado = modelo.NewBoolVar(f"aislado_mfc_{emp.nombre}_d{d}")

            # Si aislado=1 → F[d]=1
            modelo.Add(F[d] == 1).OnlyEnforceIf(v_aislado)

            # Si aislado=1 → sum(ventana) < min_francos
            #   ↔  sum(ventana) <= min_francos - 1
            modelo.Add(sum(ventana) <= min_francos - 1).OnlyEnforceIf(v_aislado)

            # Si F[d]=0 → aislado=0
            modelo.Add(v_aislado == 0).OnlyEnforceIf(F[d].Not())

            # Si sum(ventana) >= min_francos → aislado=0
            # (evitar que quede forzado a 1 cuando la ventana ya es suficiente)
            v_ventana_ok = modelo.NewBoolVar(f"ventana_ok_mfc_{emp.nombre}_d{d}")
            modelo.Add(sum(ventana) >= min_francos).OnlyEnforceIf(v_ventana_ok)
            modelo.Add(sum(ventana) < min_francos).OnlyEnforceIf(v_ventana_ok.Not())
            modelo.Add(v_aislado == 0).OnlyEnforceIf(v_ventana_ok)

            if modo == 'HARD':
                add_hard(modelo, ctx,
                         modelo.Add(v_aislado == 0),
                         f"{emp.nombre}_no_franco_aislado_d{d}")
            else:
                ctx.penalizaciones_soft.append(v_aislado * peso_soft)

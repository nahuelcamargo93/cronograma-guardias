# Diagnóstico y Propuestas de Solución - Regla: MANEJO_FINDES

Este documento detalla el problema de inviabilidad matemática generado por la regla de fines de semana (`MANEJO_FINDES`) para el Servicio 2 (Enfermería) en Agosto 2026, y las propuestas de solución para abordarlo en el futuro.

---

## 1. Detalles del Conflicto de Inviabilidad

### Comportamiento Actual
Para un profesional con disponibilidad máxima en el mes ($k\_disp = 5$ fines de semana libres de licencias), la regla en el Servicio 2 exige de forma obligatoria un Fin de Semana Largo Reglamentario (`flr` de 4 días libres consecutivos):
$$\sum \text{vars\_flr} == 1$$

Dado que la regla está configurada globalmente como `HARD` en la base de datos para este servicio, todos los enfermeros sin licencias registradas en el mes de agosto están obligados a tomar este descanso de 4 días.

### Impacto de la Transición (Cronograma 583)
Al activarse el historial previo de julio, se inyectan restricciones de transición rígidas (como descansos mínimos de 24 horas y límites de días de trabajo consecutivos) para el 1 y 2 de agosto. Esto limita severamente qué profesionales pueden cubrir el primer fin de semana de agosto. Al chocar la cobertura mínima del servicio con la obligación de otorgar fines de semana largos (`flr`) de 4 días a todo el plantel activo durante el mes, la capacidad del plantel se vuelve matemáticamente insuficiente y el modelo se declara inviable.

---

## 2. Propuestas de Solución

### Opción A: Configurar `MANEJO_FINDES` como `SOFT` en Base de Datos
- **Implementación:** Cambiar el parámetro `"modo": "HARD"` a `"modo": "SOFT"` en la tabla `servicios_reglas` para el Servicio 2.
- **Funcionamiento:** Las desviaciones en los targets de `flr`, `finde_comp` (completos) y `finde_med` (medios) se penalizarán en la función objetivo en lugar de causar inviabilidad. El solver otorgará el beneficio siempre que sea posible, pero ante tensiones de cobertura preferirá sacrificarlo a cambio de mantener el cronograma viable.

### Opción B: Acotar Targets dinámicamente según Licencias y Disponibilidad Real
- **Implementación:** Modificar la lógica de pre-procesamiento en `restricciones/double/manejo_findes.py`.
- **Funcionamiento:** En lugar de acotar los targets netos usando la longitud total de las variables mensuales (`len(vars_completo)`):
  $$\text{target\_c\_neto} = \max(0, \min(\text{target\_c\_neto}, \text{len(vars\_completo)}))$$
  Acotar usando la disponibilidad real de fines de semana del profesional en el mes (descontando días de licencia en fines de semana):
  $$\text{target\_c\_neto} = \max(0, \min(\text{target\_c\_neto}, \text{findes\_disponibles\_sin\_licencia}))$$
  Esto evitará que a profesionales con licencias prolongadas se les exijan targets de fin de semana imposibles de cumplir en modo `HARD`.

### Opción C: Introducción de Holguras Automáticas ante Inviabilidad de Capacidad
- **Implementación:** Incorporar una relajación automática en el modelo matemático en caso de que la capacidad total del plantel sea inferior a la sumatoria de targets obligatorios del mes.
- **Funcionamiento:** Se definen variables enteras de holgura $v\_flr \ge 0$ asociadas a la restricción:
  $$\sum \text{vars\_flr} + v\_flr == 1$$
  Estas holguras se penalizan con un peso intermedio en la función objetivo, permitiendo al solucionador relajar dinámicamente el beneficio en situaciones de alta tensión.

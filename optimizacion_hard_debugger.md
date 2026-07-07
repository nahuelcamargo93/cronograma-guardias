# Diagnóstico de Inviabilidad - Servicio 2 (Enfermería) - Agosto 2026

Este documento detalla la investigación técnica sobre la inviabilidad matemática surgida en el Servicio 2 al activar el **cronograma 583 (Julio 2026)** como historial previo, y por qué el debugger hard no logró aislar el problema de forma completa.

---

## 1. Regla: `MEZCLA_SEMANAL_DURA`

### Comportamiento y Ecuaciones
La regla prohíbe mezclar familias de turnos en una misma semana calendaria. Para la semana de transición (semana que contiene los últimos días de julio y los primeros de agosto), la regla busca el "ganador" de la familia de turnos en el historial de la última semana de julio y agrega una restricción dura para forzar a que la categoría de esa semana en el solver sea únicamente la ganadora:
$$\text{is\_Turno\_Familia\_Ganadora} == 1$$

Al mismo tiempo, la regla de mezcla semanal impone que:
$$\text{is\_M} + \text{is\_T} + \text{is\_TN} + \text{is\_N} \le 1$$

### Origen de la Inviabilidad
1. **Transición Rígida:** Si un profesional trabajó la familia de turnos de Mañana ($M$) en la última semana de julio, el ganador de la transición se fija como $M$. Esto obliga a que el solver en los días sábado 1 y domingo 2 de agosto **sólo** pueda asignarle turnos de Mañana ($M$), o dejarlo libre.
2. **Colisión con Demanda del Fin de Semana:** Si la cobertura del primer fin de semana de agosto requiere turnos de otras familias (como Tarde o Noche) y los enfermeros disponibles tienen su transición bloqueada en familias distintas, se genera una inviabilidad matemática directa. El solver no puede cubrir la demanda porque las opciones de asignación permitidas para el fin de semana están limitadas por el historial de julio.
3. **Infracciones Detectadas (Modo Debug Soft):**
   - `MAÑE LORENA_hist_winner_2026_07_27_N`
   - `PALANA GRACIELA_hist_winner_2026_07_27_TN`
   - `TULA DAIANA_hist_winner_2026_07_27_TN`

---

## 2. Regla: `MANEJO_FINDES`

### Comportamiento y Ecuaciones
Regula de forma paramétrica la asignación de descansos y guardias los fines de semana. Si un empleado no tiene licencias en agosto, su disponibilidad calculada es máxima ($k\_disp = 5$). Bajo esta disponibilidad, la regla del servicio 2 exige que el empleado tenga exactamente:
$$\text{target\_flr} == 1 \quad \text{(Fin de Semana Largo Reglamentario, libre de 4 días consecutivos)}$$

En modo `HARD`, el cargador inyecta una restricción dura de igualdad:
$$\sum \text{vars\_flr} == 1$$

### Origen de la Inviabilidad
1. **Restricciones de Transición Heredadas:** Al estar el cronograma 583 activo, se inyectan las guardias previas de la última semana de julio. Esto activa de forma estricta las reglas de descanso posterior a guardias (`DESCANSO_ENTRE_TURNOS`) y días consecutivos máximos de trabajo (`MAX_DIAS_CONTINUOS`) del 31 de julio al 1 de agosto, limitando la flexibilidad y disponibilidad de personal para el sábado 1 y domingo 2 de agosto.
2. **Conflicto de Capacidad y Rigidez:** Obligar a que todos los enfermeros disponibles del plantel (que no tengan licencias registradas en el mes de agosto) se tomen de forma obligatoria e ineludible un bloque de 4 días libres consecutivos (`flr`), combinado con las restricciones de transición que reducen la disponibilidad el primer fin de semana, hace colapsar la capacidad de cobertura del servicio frente a la demanda mínima diaria.
3. **Infracciones Detectadas (Modo Debug Soft):**
   El solver tuvo que violar la restricción de `flr` para 5 profesionales para poder satisfacer la demanda y viabilizar el cronograma:
   - `CALDERON MARIA JOSE_flr`
   - `CORIA LUCIANO_flr`
   - `FERNANDEZ PAOLA_flr`
   - `FERNANDEZ YESICA_flr`
   - `PALACIOS FACUNDO_flr`

---

## 3. Limitación del Debugger Hard (`debug_hard.py`)

El debugger hard falló en aislar ambos conflictos debido a un problema de diseño en su flujo secuencial:
1. **Evaluación Acumulativa con Salida Prematura:** El script `restricciones/debug_hard.py` evalúa las reglas agregándolas de una en una por orden alfabético. Al encender la regla `MANEJO_FINDES`, el modelo se vuelve inviable. El debugger entonces prueba desactivar *únicamente* `MANEJO_FINDES` con el resto de las reglas globales encendidas. 
2. **Enmascaramiento de Conflictos:** Dado que `MEZCLA_SEMANAL_DURA` (que está más adelante en orden alfabético) también está quebrada por sí sola, la prueba de desactivación individual de `MANEJO_FINDES` da inviable (porque `MEZCLA_SEMANAL_DURA` sigue activa y rompe el modelo).
3. **Salida Abrupta:** Al fallar la desactivación individual, el debugger cataloga el error como `COLISION_MULTIPLE` y ejecuta un `break` que termina el bucle. Esto impide evaluar y descubrir de manera independiente el conflicto en `MEZCLA_SEMANAL_DURA`.
4. **Persistencia del Historial:** El debugger hard en ningún escenario desactiva las guardias del historial previo (`historial_semana_previa`), lo que hace que las transiciones de fin de mes sigan afectando a los modelos simplificados.

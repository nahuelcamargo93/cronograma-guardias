# Conflicto Técnico: Francos Forzados de 4 días sin Guardia Previa (Caso Palana)

Este documento detalla el conflicto de inviabilidad matemática detectado para el Servicio 2 (Enfermería) en el mes de agosto de 2026, originado por la interacción entre la regla global `MANEJO_FINDES`, el historial de guardias previas y la asignación manual de francos forzados.

## 1. Descripción del Conflicto

La profesional **PALANA GRACIELA** tenía asignado un franco forzado de 4 días en la base de datos (tabla `personal_francos_forzados`) desde el **1 de agosto de 2026** al **4 de agosto de 2026**. 

Matemáticamente, un franco forzado de 4 días que coincide exactamente con el bloque de fin de semana largo (FLR) gatilla las siguientes restricciones duras en el motor:

1. **Forzado de FLR:** La regla `MANEJO_FINDES` ([manejo_findes.py](file:///c:/Users/asus/Desktop/Ryoko/cronograma_inteligente/restricciones/double/manejo_findes.py)) detecta que los 4 días del bloque de sábado a martes (`sm`, del 1 al 4 de agosto) están forzados. Consecuentemente, inyecta la restricción dura:
   $$\text{var\_bloque} == 1$$

2. **Requisitos de Contorno del FLR:** Para que un bloque de 4 días libres sea considerado un FLR reglamentario válido, la definición exige que esté rodeado por días de trabajo. Esto obliga al solver a forzar:
   $$\text{prev\_ok} == 1 \quad (\text{Trabajar el día anterior, 31 de julio})$$
   $$\text{post\_ok} == 1 \quad (\text{Trabajar el día posterior, 5 de agosto})$$

3. **Inexistencia de Cronograma Activo de Julio:** Al estar el cronograma de julio desactivado o desaprobado en la base de datos, la consulta de historial previo (`cargar_guardias_previas`) no encuentra guardias del 31 de julio para la profesional. Esto es interpretado en el código como un **franco de facto (Null convertido en 0)**.

4. **Colisión Matemática de Restricciones:**
   * Dado que el historial previo indica que no trabajó el 31 de julio, el contorno exige incondicionalmente:
     $$\text{var\_bloque} == 0$$
   * Pero el franco forzado de 4 días del usuario exige:
     $$\text{var\_bloque} == 1$$
   * El solver encuentra que $\{0 == 1\}$ es **infeasible**, provocando el fallo del cronograma completo incluso si la regla de servicio `MANEJO_FINDES` está en modo `SOFT`.

---

## 2. Recomendación de Logs de Alerta y Prevención

Para evitar que el solver falle silenciosamente con una inviabilidad dura, se propone agregar una pre-auditoría en la carga de datos que advierta en consola antes de invocar al solver:

* **Regla a validar:** Buscar profesionales que tengan 4 días de francos forzados consecutivos que coincidan con un bloque FLR.
* **Verificación de contorno previo:** Si el cronograma previo no está aprobado, o el profesional no registra una guardia el día anterior, emitir una advertencia explícita.
* **Log propuesto:**
  ```text
  [WARN] [Auditoría] La profesional PALANA GRACIELA tiene configurado un franco forzado de 4 días (01/08 - 04/08) que gatilla un FLR, pero no registra guardia el día previo (31/07) en el historial. Esto generará una INVIABILIDAD MATEMÁTICA en el solver.
  ```

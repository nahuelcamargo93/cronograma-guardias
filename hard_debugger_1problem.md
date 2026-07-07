# Por qué el Hard Debugger no detectó el conflicto (Caso Palana)

Este documento analiza las deficiencias y vacíos en el diseño del diagnóstico secuencial en [debug_hard.py](file:///c:/Users/asus/Desktop/Ryoko/cronograma_inteligente/restricciones/debug_hard.py) que impidieron que el debugger aislara e informara el conflicto de **PALANA GRACIELA** detallado en [palana_problem.md](file:///c:/Users/asus/Desktop/Ryoko/cronograma_inteligente/palana_problem.md).

## 1. Fuga de Diagnóstico en el Paso 1 (Reglas Globales)

En el Paso 1, el debugger busca determinar si la inviabilidad matemática es producto de alguna regla global del servicio. Para ello, corre versiones simplificadas del modelo donde limpia las restricciones individuales de personal.

* **El mecanismo:** El debugger invoca el solver con la directiva `sin_ajustes_de=todos_nombres`. Esto elimina del modelo temporal todos los ajustes específicos del personal cargados en memoria.
* **El fallo:** Al desactivar los ajustes individuales, se borraron las directivas de `FRANCO_FORZADO` cargadas desde la tabla `personal_francos_forzados`. Sin el franco forzado de 4 días de Palana, la regla `MANEJO_FINDES` no inyectó la restricción `var_bloque == 1`. 
* **Consecuencia:** El modelo en el Paso 1 resultó completamente factible (viable), ocultando el problema debido a que el debugger asiló las reglas globales removiendo los datos que provocaban la colisión.

---

## 2. Fuga de Diagnóstico en el Paso 2 (Restricciones de Personal)

El Paso 2 del debugger enciende individualmente las restricciones de cada empleado sobre un modelo global libre de restricciones de personal para ver quién gatilla la inviabilidad. Sin embargo, para acelerar el proceso, el debugger realiza un filtrado selectivo de empleados.

* **El mecanismo (Filtrado en [debug_hard.py:L118](file:///c:/Users/asus/Desktop/Ryoko/cronograma_inteligente/restricciones/debug_hard.py#L118)):**
  ```python
  for e in empleados:
      tiene_licencias = len(e.dias_licencia) > 0
      tiene_reglas = len(e.reglas) > 0
      
      if tiene_licencias or tiene_reglas or e.rol != "Rotativo":
          e_con_restricciones.append(e)
  ```
  Solo los empleados con licencias activas, reglas de personal permanentes en la tabla `personal_reglas`, o roles específicos (no Rotativos) son analizados individualmente en el Paso 2.

* **El fallo con Palana:**
  1. **PALANA GRACIELA** no tiene licencias en el mes de agosto.
  2. No tiene reglas de personal personalizadas en la tabla `personal_reglas` (las reglas aplicadas son las globales del servicio).
  3. Su rol es **"Rotativo"**.
  4. Los francos forzados de la tabla `personal_francos_forzados` son considerados **ajustes temporales** en memoria, no modifican la lista de `e.reglas` ni el rol del empleado.

* **Consecuencia:** Palana fue **excluida por completo** del bucle de diagnóstico individual. El debugger nunca ejecutó un solver en el Paso 2 con sus ajustes encendidos, lo que causó una fuga de detección absoluta de su conflicto.

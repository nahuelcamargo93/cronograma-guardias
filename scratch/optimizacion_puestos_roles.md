# Guía de Optimización: Puestos, Roles y Caso "Ricardo Martín" (Rotativo)

Este documento describe la arquitectura actual de asignación de puestos y roles para el personal, enfocándose en cómo funciona el fallback de compatibilidad y detallando el caso del empleado rotativo **Ricardo Martín** para su posterior limpieza y normalización.

## Estado Actual de la Arquitectura

Actualmente, el sistema utiliza dos mecanismos paralelos para determinar a qué puestos puede ser asignado un empleado en el motor de optimización (`main.py`):

1. **Tabla `personal_puestos` (Arquitectura Nueva):** Mapea explícitamente qué puestos (`UTI`, `UCO`, `General`, `Especial`, etc.) tiene habilitados cada empleado.
2. **Columna `rol` en la tabla `personal` (Arquitectura Legacy):** Almacena una etiqueta de texto que describe el rol del empleado (ej. `UTI`, `UCO`, `Rotativo`, `Supervisor`).

### El Flujo en el Motor (`main.py`)
Cuando el optimizador construye el modelo, evalúa si el empleado está habilitado para cubrir el puesto del turno analizado. La lógica sigue esta precedencia:
- Si el empleado tiene puestos asociados en `personal_puestos`, el motor **solo** le permite cubrir esos puestos.
- Si el empleado **no** tiene puestos asociados en `personal_puestos` (tabla vacía para él), se activa el **fallback de compatibilidad**:
  - Utiliza el campo `rol` del empleado.
  - Si el rol es `"Rotativo"`, se omite el filtrado (se le permite hacer cualquier turno/puesto).
  - Si el rol es distinto de `"Rotativo"`, solo puede hacer turnos cuyo puesto coincida con su rol.

---

## Diagnóstico del Caso "Martin, Ricardo" (Servicio 1: Kinesiología)

Al inspeccionar la base de datos con el script de diagnóstico, se detectó que:
- **133 de 134** empleados activos tienen sus puestos configurados correctamente en `personal_puestos`.
- **Ricardo Martín** es el único empleado activo que no tiene ningún registro en `personal_puestos`.

### ¿Por qué ocurrió esto?
Durante la migración de datos que puebla la tabla `personal_puestos` en base al `rol` del empleado:
- El rol de Ricardo Martín está registrado como `'Rotativo'`.
- El script de migración intenta asignar un puesto llamado `'Rotativo'`.
- Al no existir el puesto `'Rotativo'` en el catálogo del servicio 1 (los únicos puestos válidos son `UTI`, `UCO`, `General` y `Especial`), la inserción se descarta silenciosamente (`INSERT OR IGNORE`).

### Comportamiento Resultante (Deseado pero Desprolijo)
Al no quedar asociado a ningún puesto en `personal_puestos`, en cada corrida del motor Ricardo Martín cae en el fallback de compatibilidad en `main.py`. Como su rol es `'Rotativo'`, el motor salta la restricción de exclusión de puesto y le permite cubrir **todos los puestos** del servicio. 

Aunque el resultado final es matemáticamente correcto (un rotativo debe poder cubrir cualquier puesto), la implementación depende de que la tabla `personal_puestos` esté vacía para él, lo cual es propenso a errores y desprolijo.

---

## Propuesta de Limpieza para el Futuro

Para normalizar esta lógica y no depender de fallbacks silenciosos por compatibilidad, se proponen las siguientes alternativas de diseño:

### Opción A: Habilitar explícitamente todos los puestos en `personal_puestos` (Recomendado)
Consiste en asociar a Ricardo Martín (y a cualquier futuro empleado rotativo) con **todos** los puestos individuales del servicio en la tabla `personal_puestos`.
- **Ventaja:** Elimina la necesidad del fallback por compatibilidad en `main.py`. Si un empleado no tiene puestos habilitados, el motor debería dar un error de configuración en lugar de asumir el rol.
- **SQL para aplicar en el futuro:**
  ```sql
  -- Asociar a Ricardo Martín con todos los puestos del servicio 1
  INSERT INTO personal_puestos (personal_nombre, puesto_id)
  SELECT 'Martin, Ricardo', id FROM puestos WHERE servicio_id = 1;
  ```

### Opción B: Incorporar el tipo de rol "Rotativo" directamente en `personal_puestos`
Crear un puesto virtual "Rotativo" o manejar una columna `es_rotativo` en la tabla `personal` para que el cargador de datos `data_loader.py` le asigne automáticamente todos los puestos de su servicio al construir el objeto `Empleado` en memoria.

---

## Tareas Pendientes para el Siguiente Chat
1. **Limpieza de la Base de Datos:** Correr la asociación explícita de puestos para Ricardo Martín.
2. **Remoción del Fallback de main.py:** Una vez que todos los empleados tengan sus puestos configurados en `personal_puestos`, eliminar el bloque `else` de compatibilidad legacy en `main.py` y lanzar una excepción (`ValueError`) si `emp.puestos_habilitados` está vacío.

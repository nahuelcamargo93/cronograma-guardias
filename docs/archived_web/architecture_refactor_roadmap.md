# Roadmap de Refactorización Arquitectónica: Motor de Cronogramas Inteligente

Este documento sirve como la guía maestra de diseño y el mapa de ruta secuencial para transformar el MVP actual en un producto de software multi-tenant, desacoplado de lógicas de negocio específicas, con un debugger visual/analítico integrado y optimizado para un consumo mínimo de tokens con herramientas de IA.

---

## 📌 Visión General y Filosofía de Diseño

El objetivo central de esta refactorización es **separar el "Idioma de Negocio" (nombres de turnos, puestos, roles humanos) del "Idioma Matemático" (IDs numéricos, horas, matrices de restricciones)**. 

En la arquitectura actual, el motor de optimización sufre de un acoplamiento severo: conoce strings explícitos como `"Mañana_UTI"` o `"Supervisor"` y mezcla la lectura de la base de datos con la lógica de las restricciones en archivos colosales. Esto genera rigidez (impedir que el motor sirva para otros sectores sin modificar el código) y un gasto excesivo de tokens al mantener el proyecto con IA, ya que para modificar una regla simple se debe arrastrar el contexto de archivos de cientos de líneas.

La nueva arquitectura se divide en componentes independientes y aislados que se comunican mediante estructuras de datos abstractas. El motor se vuelve "ciego" al tipo de negocio que está organizando; solo procesa números y lógica de optimización pura.

---

## 🛠️ Los Tres Pilares del Sistema de Debugger

Para solucionar el problema de la "Inviabilidad Matemática" (`INFEASIBLE`) de OR-Tools sin recurrir a búsquedas secuenciales lentas, el sistema implementará una doble red de seguridad:

1. **Análisis Técnico por Suposiciones (Assumptions):** En ejecuciones normales, el orquestador central vinculará cada restricción de forma transparente a un flag lógico con nombre dinámico (ej. `MIN_HORAS_MES__Pepito`). Si el modelo colapsa, OR-Tools identificará en microsegundos qué flags específicos causaron el conflicto y los imprimirá en la consola con nombre y apellido.
2. **Debugger Visual por Penalización Extrema (MODO_DEBUG):** Al activar este modo, las restricciones de las carpetas `/hard` y `/double` se transformarán automáticamente en restricciones blandas asociadas a una penalización de costo extremo (ej. `10.000.000` puntos en la función objetivo). El modelo **nunca dará inviable**; siempre generará un cronograma forzado en la base de datos, permitiendo al administrador abrir DB Browser y detectar visualmente qué regla se sacrificó para poder cubrir la demanda del plantel.
3. **Reportes de Infracciones:** Cuando el motor corra en modo de diagnóstico, los resultados no pisarán las tablas de producción. Se generará un archivo Excel independiente con el prefijo `cronograma_debugger_[Nombre_Servicio].xlsx`, cuya primera solapa será un "Reporte de Infracciones" explícito detallando los quiebres lógicos realizados por el solver.

---

## 📂 Clasificación de la Carpeta `/restricciones`

Las reglas dejarán de estar aglomeradas y se dividirán en tres subcarpetas según su naturaleza matemática:
* **`/hard` (Leyes Físicas del Cronograma):** Restricciones que bajo ninguna circunstancia se pueden flexibilizar porque romperían la lógica elemental (ej. `UN_TURNO_POR_DIA`, `LICENCIAS`).
* **`/soft` (Preferencias y Equidad Nativas):** Lógicas que por definición buscan equilibrar el esquema de trabajo o cumplir deseos del personal mediante penalizaciones estándar en la función objetivo (ej. `PESO_MIX_HORARIO`, `BONUS_COMBO_FINDE`).
* **`/double` (Límites y Reglas Paramétricas):** Restricciones institucionales que el usuario puede configurar desde la base de datos para que actúen de forma estricta (`HARD`) o como una preferencia flexible (`SOFT`), adaptándose dinámicamente según el campo `modo` del registro.

---

## 🗺️ Mapa de Tareas Secuenciales

### 🟥 FASE 1: Base de Datos y Capa de Traducción (Data Ingestion)
* **Objetivo de la Fase:** Preparar el terreno para que la información esté disponible de forma cómoda para administración manual y masticada para el optimizador.

- [ ] **Tarea 1.1: Migración del Esquema y Datos en DB Browser**
  - **Idea General:** Facilitar el filtrado directo y la comodidad de trabajo en DB Browser sin tener que escribir `JOINs` complejos en SQL, impactando positivamente en la velocidad de lectura del motor.
  - **Acción Técnica:** Modificar `schema.py` para añadir la columna `servicio_id` (INTEGER REFERENCES servicios(id)) en las tablas: `personal_reglas`, `personal_reglas_ajustes`, `personal_puestos` y `guardias`.
  - **Migración de Datos Históricos:** Implementar bloques `try/except` seguros que ejecuten sentencias `UPDATE` automáticas al inicializar la DB. Rellenar la nueva columna `servicio_id` con el valor `1` (Kinesiología Crítica) en todos los registros existentes donde el campo sea `NULL`, vinculándolos correctamente a través del nombre de la persona.

- [ ] **Tarea 1.2: Implementación de `traductor.py` (Mapeo Bidireccional)**
  - **Idea General:** Crear el puente agnóstico del sistema. Este módulo se encarga de aislar al motor de los strings de la base de datos.
  - **Acción Técnica:** Desarrollar un componente que lea la DB para un `servicio_id` específico y genere diccionarios en memoria de doble vía (`string_nombre <-> id_numerico`). Al constructor del modelo de OR-Tools ya no ingresan objetos de base de datos complejos, sino colecciones de datos limpias basadas exclusivamente en IDs numéricos y atributos matemáticos puros (horas del turno, flags de fines de semana, etc.).

---

### 🟨 FASE 2: Arquitectura de Micro-Reglas e Infraestructura de Debugger
* **Objetivo de la Fase:** Despedazar los archivos gigantescos actuales en componentes mínimos y dotar al motor de la capacidad de reportar fallos de forma automática sin ensuciar la lógica de las reglas.

- [x] **Tarea 2.1: Creación de la Estructura de Directorios** ✅
  - **Idea General:** Organizar físicamente el espacio de las restricciones para que cada regla viva aislada en su propio universo cerrado.
  - **Acción Técnica:** Crear la carpeta `/restricciones` en la raíz del proyecto con sus tres subcarpetas correspondientes: `/hard`, `/soft` y `/double`.

- [x] **Tarea 2.2: Implementación de la Lógica de Doble Restricción para Debugger** ✅
  - **Idea General:** Preparar la infraestructura central del orquestador para soportar las dos redes de seguridad del debugger sin obligar a que las micro-reglas repitan código.
  - **Acción Técnica:** Diseñar el cargador dinámico de reglas para que asocie de manera automática cada restricción a un flag lógico indicador (`OnlyEnforceIf`). Si el motor falla de forma dura, usará `SufficientAssumptionsForInfeasibility()` para cantar el conflicto en la consola. Si se activa `MODO_DEBUG = True`, transformará las restricciones en penalizaciones extremas de la función objetivo.
  - **Estado:** `restricciones/cargador.py` (add_hard, preparar_assumption, reportar_conflicto) y `restricciones/contexto.py` (ContextoModelo) implementados.

- [~] **Tarea 2.3: Migración Gradual de Reglas Duras a Archivos Únicos** ⚠️ PARCIAL
  - **Idea General:** Vaciar el archivo `hard_rules.py` aislando cada comportamiento en un micro-archivo matemático puro de pocas líneas.
  - **Acción Técnica:** Extraer de forma individual lógicas como licencias, exclusiones y un turno por día hacia `/restricciones/hard/`, adaptando su código para que consuma únicamente los IDs numéricos provistos por el traductor.
  - **Estado:** Los 22 micro-archivos de `/restricciones/hard/` fueron creados. El monolito `hard_rules.py` (1833 líneas) **sigue activo** — pendiente desacoplarlo de `main.py` y vaciarlo.

- [x] **Tarea 2.4: Migración Gradual de Reglas Blandas y Dobles** ✅
  - **Idea General:** Vaciar el archivo `soft_rules.py` distribuyendo las nivelaciones de equidad y los límites configurables según la clasificación estructural.
  - **Acción Técnica:** Aislar las reglas en `/soft` o `/double` (leyendo el campo `modo` del JSON de la DB para resolver si penalizan o bloquean).
  - **Estado:** 15 micro-reglas en `/restricciones/soft/` + registro `__init__.py`. 10 reglas double documentadas en `/restricciones/double/__init__.py`. `ContextoModelo` extendido con `penalizaciones_soft` y `bonuses_soft`. `construir_objetivo_soft()` en `cargador.py` ensambla el objetivo en un solo punto.

- [x] **Tarea 2.5: Cargador Dinámico de Restricciones** ✅
  - **Idea General:** Hacer que el motor sea auto-configurable. El optimizador ya no tiene llamadas harcodeadas a funciones de reglas; lee la base de datos y arma el rompecabezas en tiempo de ejecución.
  - **Acción Técnica:** Implementar un bucle genérico en el orquestador que recorra los códigos de regla activos en la DB para el servicio, busque los archivos correspondientes en `/restricciones` y los ejecute secuencialmente pasándoles el modelo.
  - **Estado:** `ejecutar_reglas()` y `cargar_y_ejecutar_todas()` en `cargador.py`. Registros `REGLAS_HARD` (21), `REGLAS_DOUBLE` (10), `REGLAS_SOFT` (15) en los `__init__.py` de cada subpaquete. 36 módulos validados. Flujo: hard → double → soft → `construir_objetivo_soft()` → `activar_assumptions()`.

---

### 🟩 FASE 3: Refactor de `main.py` y Orquestación Corta
* **Objetivo de la Fase:** Limpiar el archivo principal para quitarle todas las responsabilidades accesorias y dejarlo como un director de orquesta puramente matemático de menos de 100 líneas.

- [x] **Tarea 3.1: Depuración de Dependencias Globales y CLI** ✅
  - **Idea General:** Eliminar el archivo de variables estáticas rígidas `data.py` para transicionar hacia un motor dinámico alimentado por argumentos.
  - **Acción Técnica:** Modificar la firma de las funciones principales para asegurar que las fechas de inicio/fin, feriados e índices entren estrictamente como parámetros de ejecución provenientes de la base de datos.
  - **Estado:** Completada. El archivo `data.py` fue eliminado, los feriados se migraron a la DB, y `main.py` utiliza `argparse` y consultas a la base de datos de manera dinámica.


- [x] **Tarea 3.2: Implementación del Postprocesador**
  - **Idea General:** Reconstruir la realidad del negocio una vez que el motor matemático termine su trabajo.
  - **Acción Técnica:** Desarrollar la función inversa que tome la matriz de unos y ceros resuelta por OR-Tools (IDs de empleados y turnos asignados), consulte el diccionario de traducción bidireccional en memoria de la Tarea 1.2, rescate los strings originales y proceda a ejecutar los `INSERTs` limpios en la tabla `guardias` (o en el reporte de debug si corresponde).

---

### 🟦 FASE 4: Desacoplamiento de Reportes Visuales y Debugger Excel
* **Objetivo de la Fase:** Sacar por completo la lógicas de formato (Excel, PDF) del flujo de optimización. Modificar un color o un diseño visual jamás debe requerir tocar el código del motor matemático.

- [x] **Tarea 4.1: Estructura de Carpetas de Reportes** ✅
  - **Idea General:** Organizar los generadores visuales de forma aislada e independiente por cada sector comercial o servicio.
  - **Acción Técnica:** Crear el directorio `/reportes` y segmentarlo en subcarpetas específicas (ej. `reportes/servicio_1_kinesiologia/`, `reportes/servicio_2_monitoreo/`, `reportes/generales/`).

- [ ] **Tarea 4.2: Script de Extracción e Impresión de Producción y Debug**
  - **Idea General:** Los reportes ya no se alimentan de variables internas de OR-Tools en caliente; se ejecutan como un proceso posterior e independiente leyendo directamente los datos guardados en la tabla `guardias`.
  - **Acción Técnica:** Migrar los archivos de exportación de kinesiología, enfermería y médicos actuales. Implementar en `reportes/generales/excel_debugger.py` la lógica que se dispara únicamente en `MODO_DEBUG`, guardando el archivo con el prefijo `cronograma_debugger_[Servicio].xlsx` e inyectando como primera hoja el Reporte de Infracciones detallando qué regla se rompió y quién la rompió.

---
*Nota para la IA: No avances a la siguiente tarea hasta que la actual haya sido programada, testeada de forma unitaria y aprobada explícitamente por el usuario.*
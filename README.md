# Motor de Cronogramas Inteligentes

Motor de optimización matemática basado en **Google OR-Tools (CP-SAT Solver)** para la planificación y asignación eficiente de turnos de personal médico y de soporte.

---

## 1. Arquitectura & Desacoplamiento

El sistema implementa un desacoplamiento estricto entre la lógica de negocio y el motor matemático:
- **Modelo de Datos:** Las entidades (`Empleado`, `Turno`) se modelan en [models.py](file:///c:/Users/asus/Desktop/Ryoko/cronograma_inteligente/models.py).
- **Lógica de Restricciones:** Ubicada en `/restricciones`. Cada regla es un módulo Python independiente cargado de forma dinámica.
- **Orquestador:** [main.py](file:///c:/Users/asus/Desktop/Ryoko/cronograma_inteligente/main.py) configura las variables de decisión, ejecuta las restricciones dinámicamente y llama al solver.
- **Base de Datos:** SQLite encapsulada en `/database`. El motor no realiza queries directas de negocio en las reglas; los datos ingresan limpios a través de los cargadores.

---

## 2. Estructura del Proyecto

```text
cronograma_inteligente/
├── main.py                    # Orquestador del modelo, resolución y CLI
├── models.py                  # Definición de clases Empleado y Turno
├── rule_engine.py             # Motor legacy / Asignaciones fijas personalizadas
├── database/                  # Capa de datos (SQLite)
│   ├── connection.py          # Conexión centralizada
│   ├── schema.py              # Definición de tablas y migraciones
│   ├── queries.py             # Queries transaccionales y de reglas
│   └── data_loader.py         # Mapeo de BD a objetos de dominio (Empleado/Turno)
├── restricciones/             # Reglas del motor matemático
│   ├── cargador.py            # Orquestador dinámico e infraestructura de debug
│   ├── contexto.py            # ContextoModelo (almacena variables y acumuladores)
│   ├── hard/                  # Restricciones duras obligatorias (ej. licencias, descansos)
│   ├── soft/                  # Restricciones blandas (preferencias, equidad anual)
│   └── double/                # Reglas duales (configurables como hard o soft)
├── reportes/                  # Generadores de planillas Excel premium
│   ├── generales/             # Base de reportes e inyección de infracciones (debug)
│   └── servicio_[1-4]...      # Reportes a medida para cada servicio de salud
└── herramientas_y_diagnostico/# Scripts CLI de soporte y migraciones rápidas
```

---

## 3. Flujo de Datos

```mermaid
graph TD
    DB[(cronograma_inteligente.db)] -->|queries.py / data_loader.py| Domain[Objetos Empleado & Turno]
    Domain -->|main.py: construir_modelo| Context[ContextoModelo & CpModel]
    Context -->|cargador.py: ejecutar_reglas| Rules[Reglas: hard / double / soft]
    Rules -->|cargador.py: construir_objetivo_soft| Objective[Función Objetivo + Assumptions]
    Objective -->|main.py: resolver_modelo| Solver[OR-Tools CP-SAT Solver]
    Solver -->|Resuelto (OPTIMAL/FEASIBLE)| DBWrite[Guardar en DB y Generar Excel]
    DBWrite --> DB
    DBWrite --> Excel[Reporte Excel Servicio]
    Solver -->|Inviable (INFEASIBLE)| Conflict[reportar_conflicto - debug]
```

1. **Extracción y Carga:** `data_loader.py` consulta la BD SQLite, procesa reglas y licencias, y devuelve listas de objetos `Empleado` y `Turno`.
2. **Construcción:** `main.py` genera el espacio de variables booleanas de decisión `(Empleado, Día, Turno)`.
3. **Inyección Dinámica:** `cargador.py` importa y aplica secuencialmente los módulos de `/restricciones`.
4. **Resolución:** El solver de OR-Tools optimiza el modelo de programación de restricciones.
5. **Persistencia y Reporte:** Si es viable, el resultado se almacena en la BD y se dispara el script de exportación en `/reportes` para estructurar la planilla Excel premium del servicio.

---

## 4. Infraestructura de Doble Red de Seguridad

El motor incluye un sistema de diagnóstico integrado administrado por [cargador.py](file:///c:/Users/asus/Desktop/Ryoko/cronograma_inteligente/restricciones/cargador.py):

* **Assumptions (Modo Normal):** Cada regla se ejecuta con una variable de suposición (`OnlyEnforceIf(REG_REGLA)`). Si el solver determina que el modelo es `INFEASIBLE`, se consulta el conflicto (`SufficientAssumptionsForInfeasibility()`) y se imprimen en consola las reglas exactas que causaron la colisión matemática.
* **Modo Debug (Relajación):** Si se ejecuta con la bandera `--debug`, las restricciones duras se desactivan y se transforman en variables de violación penalizadas con un peso extremo (`PESO_DEBUG = 10_000_000`) en la función objetivo. Esto garantiza que el cronograma **siempre se resuelva**, mostrando visualmente en una pestaña especial de Excel (`Infracciones (DEBUG)`) qué regla se tuvo que violar y en qué empleado/día para lograr la viabilidad.

---

## 5. Instrucciones de Ejecución

El proceso de optimización se inicia desde la CLI ejecutando `main.py`.

### Parámetros Disponibles:
- `--servicio`: ID del servicio (Ej. `1` Kinesiología, `2` Enfermería, `3` Médicos, `4` Monitoreo).
- `--inicio`: Fecha de inicio del bloque (`YYYY-MM-DD`).
- `--fin`: Fecha de fin del bloque (opcional; por defecto calcula el fin del mes de inicio).
- `--notas`: Comentario o etiqueta descriptiva para guardar en base de datos.
- `--debug`: Activa el modo debug de relajación.

### Ejemplos de Comandos:

**Optimización normal para médicos (Servicio 3) en junio 2026:**
```bash
python main.py --servicio 3 --inicio 2026-06-01
```

**Optimización con MODO_DEBUG activo para diagnosticar conflictos:**
```bash
python main.py --servicio 3 --inicio 2026-06-01 --debug
```

---

## 6. Rendimiento y Modelos de Satisfacción

> [!IMPORTANT]
> **Necesidad de una Función Objetivo:**
> Para resolver cronogramas complejos con restricciones duras muy ajustadas (como en el Servicio 2), **es indispensable que al menos una regla blanda (soft) de balance o penalización esté activa** en la base de datos (por ejemplo, `PESO_BRECHA_DIARIA_PERSONAL`).
>
> Sin ninguna regla soft activa, el modelo se convierte en uno de **satisfacción pura** (objetivo = 0) y el solver CP-SAT pierde las heurísticas basadas en la relajación lineal (LP) y el Feasibility Pump. Esto resulta en búsquedas ciegas que comúnmente agotan el tiempo límite de 600 segundos sin encontrar solución. Activar al menos una regla soft guía al solver a encontrar soluciones factibles en menos de 35 segundos.

---

## 7. Reglas de Negocio Específicas

### Descanso entre Turnos (`DESCANSO_ENTRE_TURNOS`)
Garantiza el descanso mínimo obligatorio posterior a cada turno antes de iniciar el siguiente.
- **Tipo**: HARD (configurable como SOFT en MODO_DEBUG).
- **Lógica**: Para cada empleado, si se asigna un turno $T_1$ en el día $d_1$ y un turno $T_2$ en el día $d_2$ (donde $d_2 > d_1$), se calcula la diferencia temporal:
  $$Descanso = (d_2 - d_1) \times 24 + H_{start}(T_2) - (H_{start}(T_1) + D(T_1))$$
  Si este descanso es menor que el requerido por la regla para el turno $T_1$, se inyecta la restricción de exclusión mutua:
  $$Var(emp, d_1, T_1) + Var(emp, d_2, T_2) \le 1$$

### Regla Maestra de Fines de Semana (`MANEJO_FINDES`)
Unifica y regula de forma paramétrica la asignación de fines de semana libres completos, fines de semana trabajados y días específicos para cada profesional en base a su disponibilidad.
- **Tipo**: DOUBLE (configurable como HARD o SOFT en la base de datos).
- **Lógica**: Evalúa para cada empleado su disponibilidad de fines de semana hábiles ($k\_disp$) en el mes (descontando licencias y francos forzados). Según este valor, aplica targets específicos configurados en `parametros_json` para:
  - `flr`: Fines de semana largos reglamentarios (libres de 4 días).
  - `completos`: Fines de semana trabajados sábado y domingo.
  - `medios`: Fines de semana trabajados un solo día (sábado o domingo).
- **Configuración del Servicio 1 (Kinesiología Crítica)**:
  - **Modo**: `SOFT` (peso de penalización `10000`) para evitar inviabilidad ante licencias y guiar al solver a una distribución equitativa.
  - **Targets por disponibilidad ($k\_disp$)**:
    - $k\_disp = 5$: 3 libres (`flr`), 1 completo, 1 medio.
    - $k\_disp = 4$: 3 libres (`flr`), 1 completo, 0 medios.
    - $k\_disp = 3$: 2 libres (`flr`), 1 completo, 0 medios.
    - $k\_disp = 2$: 1 libre (`flr`), 1 completo, 0 medios.
    - $k\_disp = 1$: 0 libres, 1 completo, 0 medios.

### Equidad Unificada de Fines de Semana Largos (`PESO_EQUIDAD_FSL`)
Regula y nivela la asignación de fines de semana largos de 3 días (FSL3) y 4 días o más (FSL4) entre el personal, utilizando unificación paramétrica de pesos y soporte para nivelación histórica.
- **Tipo**: SOFT.
- **Lógica**: Para cada profesional, calcula los FSL3 y FSL4 acumulados en el historial de cronogramas aprobados desde la fecha de inicio (`2026-01-01`).
  - **Ingresos tardíos**: Se les imputa de forma virtual el promedio de FSL trabajados por el personal activo en los periodos históricos donde aún no formaban parte del servicio (según la fecha de su primera guardia), evitando que sean sobrecargados.
  - El solver minimiza la brecha global (Gap) de FSL3 y FSL4 acumulados (Historial Real/Virtual + Mes Actual) entre todos los profesionales del servicio.

### Máximo una semana con turno N por mes (`NO_REPETIR_N_CONSECUTIVO`)
Limita la cantidad de semanas en las que un profesional puede tener asignado el turno N (Noche) en el transcurso del mes planificado.
- **Tipo**: DOUBLE (configurable como HARD o SOFT en la base de datos).
- **Lógica**: Para cada profesional, se evalúan las variables semanales del turno N (Noche) para todas las semanas planificadas del mes ($v_{sem\_N}$).
  - Si `modo == "HARD"`, se agrega la restricción dura:
    $$\sum v_{sem\_N} \le 1$$
  - Si `modo == "SOFT"`, se define una variable entera de holgura $violacion \ge 0$ tal que:
    $$violacion \ge (\sum v_{sem\_N}) - 1$$
    Y se añade a la función objetivo la penalización $violacion \times peso\_soft$.

### Límite máximo de francos consecutivos (`MAX_FRANCOS_CONTINUOS`)
Asegura que ningún profesional tenga más de la cantidad máxima de francos seguidos configurada en el mes, contemplando la transición del historial de la semana previa.
- **Tipo**: DOUBLE (configurable como HARD o SOFT en la base de datos).
- **Lógica**: Para cada empleado, se define una variable de franco $F[d] = 1 - traba\_dia[d] - es\_licencia[d]$, excluyendo los días de licencia para evitar inviabilidades por inactividad justificada. Sobre una ventana móvil de tamaño $window = max\_francos + 1$ días:
  - Si `modo == "HARD"`, se agrega la restricción dura:
    $$\sum_{i=start}^{start+window-1} F[i] \le max\_francos$$
  - Si `modo == "SOFT"`, se define una variable de violación $v\_viol \in [0, 1]$ para cada ventana tal que:
    $$\sum_{i=start}^{start+window-1} F[i] \le max\_francos + v\_viol$$
    Y se añade a la función objetivo la penalización $v\_viol \times peso\_soft$.
  - Si no existe historial previo de guardias para el profesional, los días anteriores al inicio del mes se inicializan sin francos para evitar inviabilidades artificiales debido a la falta de datos históricos en la base de datos.


# Walkthrough - Cambios en Cronograma (PDF, Word, Historial y Regla de Viernes)

Se realizaron cuatro cambios principales en el sistema de cronogramas para cumplir con todos los requerimientos y solucionar los problemas reportados:

---

## 1. Agregar columna 'guardias' al PDF

Se modificó el script de generación de PDF ([exportar_pdf.py](file:///c:/Users/asus/Desktop/Ryoko/cronograma_inteligente/exportar_pdf.py)) para agregar una columna al final de la tabla de la segunda hoja (vista por personal) que muestra el total de guardias de 24 horas equivalentes que realiza.

### Detalles:
- Se agregaron estilos de celda y encabezado adecuados.
- Se lee el total de horas efectivas (`"Horas Ef."` de `df_persona`) y se calcula la equivalencia en guardias dividiendo por `24.0`.
- El número se visualiza de forma limpia: como entero si no tiene parte decimal (ej. `2`) o con un decimal en caso contrario (ej. `1.5`).
- Se reajustaron los anchos de columnas para asegurar que la tabla encaje perfectamente en la hoja A4 apaisada.

---

## 2. Nueva exportación a Word (.docx) de la primera hoja

Se creó el script [exportar_docx.py](file:///c:/Users/asus/Desktop/Ryoko/cronograma_inteligente/exportar_docx.py) que recrea de forma editable el calendario mensual de guardias (primera hoja) en formato Word.

### Detalles:
- Configura de forma automática el documento en A4 horizontal con márgenes estrechos.
- Diseña una tabla idéntica visualmente al PDF, con sombreado de fines de semana y feriados, e incluye los turnos (Guardia, Día y Noche).
- Sincroniza la lectura del cronograma a exportar utilizando la variable `CRONOGRAMA_ID_FORZADO`.

---

## 3. Corrección de guardias consecutivas en la transición de mes

Se corrigió la función `cargar_guardias_previas` (en [database/queries.py](file:///c:/Users/asus/Desktop/Ryoko/cronograma_inteligente/database/queries.py) y [db.py](file:///c:/Users/asus/Desktop/Ryoko/cronograma_inteligente/db.py)) que estaba omitiendo el filtro de `servicio_id` al buscar el historial de guardias del mes anterior.

### Detalles:
- **Error:** Al no filtrar por `servicio_id`, la consulta cargaba un cronograma de otro servicio (Enfermería) en lugar del de Médicos si ambos iniciaban el mismo día. Esto resultaba en un historial vacío para los médicos, permitiendo que Matricadi trabajara el último día de mayo y el primer día de junio de forma consecutiva.
- **Solución:** Se corrigió la consulta para asegurar el filtro de `servicio_id`. Ahora el solver sabe que Matricadi estuvo de guardia el 31 de mayo, por lo que aplica las 48hs obligatorias de descanso y recién le asigna su primera guardia el 3 de junio.

---

## 4. Solución a la regla de viernes limitados (EXACTO_DIA_ESPECIFICO_MES)

Se detectó y solucionó un bug lógico en el cálculo dinámico de licencias para la regla de viernes dentro de [soft_rules.py](file:///c:/Users/asus/Desktop/Ryoko/cronograma_inteligente/soft_rules.py).

### Detalles:
- **Error:** En la función `_aplicar_min_dia_especifico_mes_soft`, cuando la opción `dinamico_licencias` estaba activa para los viernes, el código contenía una inversión lógica:
  - `k == 3` (3 semanas disponibles) se evaluaba a `target_dias = 0` viernes.
  - `k == 2` (2 semanas disponibles) se evaluaba a `target_dias = 1` viernes.
  Esto forzaba incorrectamente a que todos los médicos disponibles por 3 semanas (como Aguilera Graciela, Garcia Rodriguez, Motta Mayra, etc.) tuvieran un objetivo de 0 viernes. Al retirarles los viernes, se reducía drásticamente la capacidad de personal disponible para cubrir los viernes requeridos del mes, forzando a que otros médicos (como Pregot, Zeballos, o Matricadi en corridas anteriores) tuvieran que cubrir múltiples viernes.
- **Solución:** Se simplificó y corrigió el cálculo. Si un empleado está disponible 3 o más semanas en el mes (`k >= 3`), su objetivo es trabajar **exactamente 1 viernes**. Si está disponible 2 semanas o menos (por licencias prolongadas), su objetivo es **0 viernes**.

### Análisis Matemático de Cronograma ID 216:
* **Capacidad vs Demanda:**
  - June 2026 tiene 4 viernes. La demanda mínima requiere **12 guardias de Planta** en total de viernes. Sin embargo, para cumplir con el mínimo de horas mensuales del personal (`MIN_HORAS_MES_CALENDARIO = 185` horas, que obliga a los médicos de planta a realizar al menos 8 guardias de 24h), el solver debió distribuir horas adicionales, asignando un total de **19 turnos de Planta en días viernes**.
  - De los 20 médicos de planta activos, 3 tienen objetivos de 0 viernes (por licencias prolongadas o límites de 24h/48h mensuales como Quintero, Diaz Villafañe, y Quiroga Sassu). Esto nos deja con **17 médicos de planta disponibles** para cubrir los viernes.
  - **Principio del Palomar:** Distribuir 19 turnos necesarios de viernes entre 17 médicos disponibles hace **matemáticamente obligatorio** que al menos 2 médicos cubran 2 viernes.
* **Resultado:** El solver distribuyó perfectamente la carga:
  - **Matricadi Wendy Ailen:** Ahora trabaja **exactamente 1 viernes** (el 26/06).
  - **Pregot Analia Mariana** y **Zeballos Valeria Alejandra:** Son las únicas que cubren 2 viernes (el 05/06 y 19/06).
  - Todos los demás médicos con la regla activa trabajan **exactamente 1 viernes** (o 0 si estaban licenciados). El sistema funciona ahora con la máxima equidad teóricamente posible.

---

## Verificación

1. Se ejecutó la optimización de CLI:
   ```bash
   venv\Scripts\python.exe main.py
   ```
   Generó correctamente el **Cronograma ID 216**.
2. Se exportaron los documentos actualizados:
   - PDF: [Cronograma_Medicos_Junio_2026.pdf](file:///c:/Users/asus/Desktop/Ryoko/cronograma_inteligente/Cronograma_Medicos_Junio_2026.pdf)
   - Word: [Cronograma_Medicos_Junio_2026.docx](file:///c:/Users/asus/Desktop/Ryoko/cronograma_inteligente/Cronograma_Medicos_Junio_2026.docx)

---

## 5. Solución a la Inviabilidad del Servicio 3 (Julio 2027)

Se diagnosticó y resolvió una imposibilidad matemática directa que impedía generar el cronograma de Julio de 2027 para el Servicio 3.

### Causa Raíz del Conflicto:
El modelo entraba en una contradicción directa (inviable en la propagación inicial de variables) por la interacción de cuatro reglas críticas:
1. **`MIN_HORAS_MES_CALENDARIO` (185h)**: El plantel de 26 médicos promedia un máximo de 86h/médico si la demanda es de 3 por turno, o 171.7h si es de 6. Exigir 185h era matemáticamente insostenible para el tamaño del plantel.
2. **`EXCLUIR_TURNOS`**: Prohíbe que 4 médicos realicen guardias de 24h (`G_Planta`). Esto los fuerza a cubrir únicamente turnos de 12h (`D_Planta` y `N_Planta`).
3. **`DESCANSO_ENTRE_TURNOS` (36h para D/N)**: Al exigir un descanso de 36 horas posterior a cada guardia de 12h, los médicos limitados a estos turnos solo podían trabajar como máximo cada 2.5 días. Intentar cubrir su mínimo de horas mensuales bajo esta restricción saturaba su disponibilidad.
4. **`EXACTO_FINDE_Y_DIA` (modo HARD)**: Obligaba a todos los profesionales a cumplir de forma estricta un target específico de viernes y fines de semana, lo cual chocaba directamente con las exclusiones y descansos de los médicos de 12h.

### Modificaciones Aplicadas:
- **Ajuste de Horas Mínimas**: Se bajó `MIN_HORAS_MES_CALENDARIO` de 185h a **168h** (equivalente a 7 guardias de 24h), un número coherente y balanceado para el plantel.
- **Cambio de Modo de Regla**: Se cambió el modo de la regla `EXACTO_FINDE_Y_DIA` de `HARD` a **`SOFT`** en la base de datos (`servicios_reglas`), permitiendo que el solver distribuya equitativamente y penalice desvíos en lugar de fallar inmediatamente.
- **Mantener Capacidad Máxima Balanceada**: Se validó la viabilidad con un límite de `cantidad_max = 6` médicos por turno en Planta. Al resolverse la incompatibilidad de las reglas, **el modelo generó de forma exitosa y óptima** sin necesidad de subir la capacidad a 8.
- **Equidad Diaria**: Se activó `PESO_BRECHA_DIARIA_PERSONAL` como soft rule en la BD para evitar variaciones extremas de personal entre días.

### Resultado de la Verificación:
El cronograma se generó exitosamente con estado **`OPTIMAL`** en 43 segundos:
- **Cronograma ID 236** (Julio 2027) guardado en la base de datos.
- Archivo Excel de reporte generado correctamente: **`Cronograma_Area_Medica_UTI.xlsx`**.
- El solver asignó los turnos respetando los descansos de 36h para el personal de 12h y distribuyendo con equidad los fines de semana.

---

## 6. Depuración de Dependencias Globales y CLI (Tarea 3.1)

Se desacoplaron todas las dependencias estáticas rígidas del archivo `data.py` (el cual fue eliminado del repositorio) en favor de un diseño completamente dinámico alimentado por argumentos de CLI y consultas directas a la base de datos.

### Cambios Realizados:
1. **Migración de Feriados a la DB:** Se creó y pobló la tabla `feriados` en la base de datos con los feriados nacionales base (25 de mayo, 15 de junio, 20 de junio y 9 de julio).
2. **Cálculo Dinámico de Fechas Especiales:** Se actualizó `restricciones/hard/fechas_especiales.py` para calcular el día del padre (3er domingo de junio) y de la madre (3er domingo de octubre) de manera dinámica según el año de ejecución del cronograma.
3. **Feriados e Historial Parametrizados:** Se modificó `database/queries.py` para extraer feriados e historial directamente de la base de datos sin importar archivos externos.
4. **Refactorización de CLI:** Se actualizó `main.py` reemplazando la importación estática con un parseador de argumentos robusto (`argparse`) que permite configurar el `servicio_id`, la fecha de inicio, la fecha de fin y notas de forma dinámica:
   ```bash
   python main.py --servicio 1 --inicio 2026-07-01 --fin 2026-07-31
   ```
5. **Corrección de Tests:** Se actualizaron `soft_rules.py`, `hard_rules.py` y `test_cargador.py` para sincronizarse con la carga dinámica de feriados y fechas.

### Verificación:
* Se ejecutó el script comparador `test_cargador.py`, validando que tanto la versión legacy como la nueva basada en cargador de micro-reglas son factibles y coinciden en sus resultados con un margen del `1.7%` (menor al 5% requerido).
* Se ejecutó exitosamente la optimización CLI para el Servicio 1.


## 7. Implementación del Postprocesador (Tarea 3.2)

Se implementó el componente [postprocesador.py](file:///c:/Users/asus/Desktop/Ryoko/cronograma_inteligente/database/postprocesador.py) para independizar el motor matemático (OR-Tools) de la persistencia de datos y de la base de datos de producción.

### Detalles:
1. **Traducción Híbrida Inteligente:** El postprocesador recibe la matriz de variables de decisión del solver y detecta si el motor está utilizando IDs numéricos (nueva arquitectura) o strings tradicionales (arquitectura legacy), traduciendo los resultados al nombre real de la persona y del turno de forma transparente.
2. **Persistencia Atómica:** Las inserciones en las tablas `cronogramas`, `guardias`, `bloques_finde_largo`, `semanas_categorias` y `flr_asignados` se ejecutan bajo una sola transacción SQLite atómica.
3. **Carga Automática de Horas:** Recupera las horas de cada turno directamente a través de `Traductor.horas_turno` o como fallback seguro desde la base de datos, eliminando la duplicación de código que existía en `queries.py`.
4. Verificación Exitosa:
   - Se desarrolló y ejecutó el script [test_postprocesador.py](file:///c:/Users/asus/Desktop/Ryoko/cronograma_inteligente/scratch/test_postprocesador.py) confirmando que ambas modalidades (IDs numéricos y Strings legacy) persisten los datos de manera idéntica e impecable en la base de datos `cronograma_inteligente.db`.

---

## 8. Estructura de Carpetas de Reportes (Tarea 4.1)

Se organizaron y segmentaron los generadores de reportes del directorio `reportes/` para lograr un desacoplamiento visual y por tipo de servicio/negocio.

### Cambios Realizados:
1. **Creación de Subcarpetas:** Se estructuró el directorio `reportes/` en subcarpetas específicas:
   - `generales/`: Contiene el archivo base de estilos y reportes compartidos.
   - `servicio_1_kinesiologia/`: Generador de reportes de Kinesiología Crítica.
   - `servicio_2_enfermeria/`: Generador de reportes de Enfermería UTI.
   - `servicio_3_medicos/`: Generador de reportes de Médicos UTI.
   - `servicio_4_monitoreo/`: Generador de reportes de Personal de Monitoreo (COM).
2. **Reubicación de Archivos y Ajuste de Imports:** 
   - `base.py` se movió a `reportes/generales/base.py`.
   - `kinesiologia.py` a `reportes/servicio_1_kinesiologia/kinesiologia.py`.
   - `enfermeria.py` a `reportes/servicio_2_enfermeria/enfermeria.py`.
   - `medicos.py` a `reportes/servicio_3_medicos/medicos.py`.
   - `com.py` a `reportes/servicio_4_monitoreo/com.py`.
   - Se actualizaron todos los imports internos en cada uno de estos archivos para apuntar correctamente a `reportes.generales.base`.
3. **Desacoplamiento del Archivo `data.py` (Feriados):**
   - Se removió la dependencia del extinto archivo `data.py` (eliminado en la Tarea 3.1) en todos los scripts de reportes específicos (`enfermeria.py`, `medicos.py`, `com.py`) y en el script de prueba `scratch/test_excel_gen.py`.
   - Los reportes ahora obtienen la lista de feriados directamente de la base de datos a través de `database.queries.obtener_feriados`.
4. **Actualización de Consumidores:**
   - Se actualizaron las importaciones dinámicas en `main.py` y `exportar_ultimo_cronograma.py` para usar las nuevas ubicaciones de los archivos de reportes.
   - Se actualizó el script `scratch/test_excel_gen.py` para sincronizarlo con el nuevo esquema de módulos y la carga de feriados de la base de datos.
5. **Eliminación de Archivos Obsoletos:** Se eliminaron los archivos `.py` redundantes ubicados en la raíz del directorio `reportes/`.

### Verificación Exitosa:
* Se ejecutó el script de verificación `scratch/test_excel_gen.py` con el comando `$env:PYTHONPATH="."; .\venv\Scripts\python scratch/test_excel_gen.py` y completó exitosamente.
* Se generaron con éxito los cuatro archivos Excel correspondientes a los diferentes servicios:
  - `Cronograma_Servicio_Kinesiologia.xlsx`
  - `Cronograma_Enfermeria_UTI_actualizado.xlsx`
  - `Cronograma_Area_Medica_UTI.xlsx`
  - `Cronograma_Servicio_COM.xlsx`

---

## 9. Corrección de Fórmulas Dinámicas, Formato y Subida a Drive (Servicio 3)

Se implementaron mejoras críticas en el reporte Excel para el Servicio 3 (Médicos) y en la sincronización con Google Drive:

### Cambios Realizados:
1. **Fórmulas Dinámicas Robustas en "Vista por Personal":**
   - Se ajustó el generador de fórmulas dinámicas para utilizar referencias individuales por celda y evitar colisiones de llaves (`{row}`) en Python al compilar las expresiones.
   - Se corrigieron los nombres de licencias entre comillas dobles (ej: `"LAR"`, `"LM"`, `"CM"`, `"LPP"`) dentro de las expresiones condicionales de Excel, solucionando el error `#NAME?` o `#ERROR!`.
2. **Redondeo de Horas de Licencia:**
   - Se envolvió la fórmula de cálculo de horas de licencia en la función `ROUND(..., 0)` para que muestre horas enteras sin decimales.
3. **Evitar Duplicados en Google Drive:**
   - Se modificó `subir_cronograma_drive.py` agregando una búsqueda previa (`service.files().list`) por nombre de archivo y ID de carpeta contenedora.
   - Si se encuentra un archivo coincidente, se actualiza mediante `service.files().update` con `media_body`, reemplazando el contenido en lugar de duplicar el archivo.

### Verificación Exitosa:
* Se ejecutó el script con éxito:
  ```powershell
  .\venv\Scripts\python subir_cronograma_drive.py --servicio 3 --crono-id 535
  ```
* El sistema identificó el archivo existente en Google Drive (`1KxwO0ND3TLswzlBJl-MkuTAbxBzWSZAt_V50vwjZMXM`) y actualizó su contenido directamente:
  - **Enlace Web:** `https://docs.google.com/spreadsheets/d/1KxwO0ND3TLswzlBJl-MkuTAbxBzWSZAt_V50vwjZMXM/edit?usp=drivesdk`


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


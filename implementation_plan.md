# Plan de Implementación: Viabilidad del Cronograma sin Núñez Florencia Natalia

Este plan detalla el diagnóstico del conflicto matemático (UNSAT) al desactivar a Núñez Florencia Natalia en el mes de junio de 2026, y propone las opciones disponibles para hacerlo viable respetando las restricciones del usuario.

## Diagnóstico del Cuello de Botella (13 al 15 de Junio)

El fin de semana largo del **13 al 15 de junio** (sábado 13, domingo 14 y lunes 15 feriado) tiene una demanda de cobertura obligatoria de **al menos 1 Residente de guardia por día**.

Al excluir a Núñez Florencia Natalia, contamos con **6 Residentes activos**. Sin embargo, la disponibilidad en este fin de semana largo es la siguiente:
* **Arce Carolina:** Tiene licencia y `FRANCO_FORZADO` activo (no disponible).
* **Pacheco Celeste:** Tiene licencia el 15/06 y `FRANCO_FORZADO` activo (no disponible).
* **Biscarra Joaquín Martin:** Tiene `FRANCO_FORZADO` activo (no disponible).
* **Villegas Oliva Maria Belén:** Tiene `FRANCO_FORZADO` activo (no disponible).
* **Palermo Agustín:** Disponible.
* **Matricadi Wendy Ailen:** Disponible.

Esto nos deja con **solo 2 Residentes disponibles (Palermo y Matricadi)** para cubrir **3 días consecutivos** de 24 horas. Debido a la regla dura de descanso post-guardia de 48 horas (`DESCANSO_ENTRE_TURNOS` = 48h para G), es matemáticamente imposible que 2 personas cubran 3 días seguidos (ya que el que trabaja el sábado no puede trabajar domingo ni lunes, y el que trabaja el domingo no puede trabajar el lunes).

---

## Opciones de Resolución

Para resolver la imposibilidad matemática manteniendo a Núñez inactiva y sin alterar las guardias de Godoy, Barloa, Mora ni Quintero, la solución más limpia es **desactivar el franco forzado de solo uno de los residentes** durante ese fin de semana largo, permitiéndole cubrir la guardia faltante.

Hemos validado mediante simulación que deactivar el franco de **cualquiera** de los siguientes tres residentes hace que el cronograma sea inmediatamente viable:

> [!IMPORTANT]
> ### Opción 1 (Recomendada): Desactivar Franco Forzado de **Biscarra Joaquín Martin** (ID Ajuste: 1364)
> Se inactiva su franco forzado del 13 al 15 de junio en la base de datos. Esto lo habilita para trabajar el lunes 15/06 (o el día del fin de semana largo que el solver elija), logrando la viabilidad total.

> [!IMPORTANT]
> ### Opción 2: Desactivar Franco Forzado de **Villegas Oliva Maria Belén** (ID Ajuste: 1365)
> Se inactiva su franco forzado del 13 al 15 de junio en la base de datos, habilitándola para cubrir el día faltante.

> [!IMPORTANT]
> ### Opción 3: Desactivar Franco Forzado de **Pacheco Celeste** (ID Ajuste: 1363)
> Se inactiva su franco forzado del 13 al 15 de junio. Dado que ella tiene licencia el lunes 15, esto la habilitaría para trabajar únicamente el sábado 13 o el domingo 14.

---

## Cambios Propuestos

### Base de Datos

#### [MODIFY] [personal_reglas_ajustes](file:///c:/Users/asus/Desktop/Ryoko/cronograma_inteligente/cronograma_inteligente.db)
Dependiendo de la opción elegida por el usuario, se ejecutará una consulta SQL para cambiar a `activo = 0` en la fila correspondiente del ajuste temporal de franco forzado:
* **Opción 1:** `UPDATE personal_reglas_ajustes SET activo = 0 WHERE id = 1364` (Biscarra)
* **Opción 2:** `UPDATE personal_reglas_ajustes SET activo = 0 WHERE id = 1365` (Villegas)
* **Opción 3:** `UPDATE personal_reglas_ajustes SET activo = 0 WHERE id = 1363` (Pacheco)

---

## Plan de Verificación

1. **Resolver Modelo:** Ejecutar el motor de optimización (`main.py`) para confirmar que el modelo es factible (retorna estado `OPTIMAL` o `FEASIBLE` y genera el Cronograma ID 217).
2. **Auditoría de Guardias Protegidas:** Verificar mediante script que las asignaciones del cronograma 217 para `Godoy Maria`, `Barloa Matías Damián`, `Mora, Sergio Enrique` y `Quintero Anabela Belen` no han sufrido modificaciones con respecto a sus asignaciones fijas.
3. **Exportar Reportes:** Generar los nuevos reportes actualizados en formato PDF y Word (.docx) para el Cronograma ID 217.

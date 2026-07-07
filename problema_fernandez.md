# Conflicto Lógico: Fines de Semana - Yésica Fernández (Agosto 2026)

Este documento detalla la imposibilidad matemática del solver para cumplir con la regla `MANEJO_FINDES` (modo `HARD` o `SOFT` con alta penalización) de Yésica Fernández durante la semana del **03/08 al 09/08 de 2026** en el Servicio 2 (Enfermería UTI).

---

## 1. Contexto y Reglas en Conflicto

El solver debe balancear tres reglas lógicas simultáneamente:

1. **`MANEJO_FINDES` (Fines de semana targets por disponibilidad):**
   * Yésica Fernández tiene una disponibilidad de **5 fines de semana** en el mes (no tiene licencias).
   * Su target asignado por regla es: **3 fines de semana completos**, **1 fin de semana medio** y **1 fin de semana largo reglamentario (FLR)**.
2. **`MEZCLA_SEMANAL_DURA` (Regla HARD):**
   * Prohíbe trabajar turnos de diferentes familias de turnos (Mañana, Tarde, Tarde-Noche, Noche) en una misma semana calendario (lunes a domingo).
3. **`EXCLUIR_TURNOS` (Regla HARD - Ajuste personal):**
   * Yésica tiene exclusiones explícitas de turnos para ciertos días y turnos de fines de semana.

---

## 2. El Bloqueo del Fin de Semana (Sábado 08/08 y Domingo 09/08)

El análisis del solver demuestra que **elija la familia de turnos que elija para esa semana**, es imposible evitar que uno de los dos días del fin de semana sea franco, impidiendo que el fin de semana sea "Completo".

### A. Exclusiones de Yésica para ese fin de semana:
* **Sábado 08/08:** Tiene excluidos los turnos `T` (Tarde), `TN` (Tarde-Noche) y `TNN` (Tarde-Noche Largo).
* **Domingo 09/08:** Tiene excluidos los turnos `M` (Mañana), `MT` (Mañana-Tarde) y `TNN` (Tarde-Noche Largo).

---

## 3. Escenarios de Familias Semanales posibles

Si evaluamos cada una de las familias posibles de turnos semanales para esa semana, el bloqueo ocurre de la siguiente manera:

| Familia Semanal | Turnos permitidos en la semana | Bloqueo en el Sábado 08/08 | Bloqueo en el Domingo 09/08 | Consecuencia en el Finde |
| :--- | :--- | :--- | :--- | :--- |
| **Mañana (M / MT)** | `M`, `MT` | Permitido trabajar | **Prohibido** por exclusión (`M`, `MT`) | **Franco el Domingo** (Finde Medio o Libre) |
| **Tarde (T)** | `T`, `MT` (Tarde parcial) | **Prohibido** por exclusión (`T`) | **Prohibido** por exclusión (`MT`) | **Franco ambos días** (Finde Libre) |
| **Tarde Noche (TN)** | `TN`, `TNN` | **Prohibido** por exclusión (`TN`, `TNN`) | **Prohibido** por exclusión (`TNN`) | **Franco el Sábado** (Finde Medio o Libre) |
| **Noche (N)** | `N`, `TNN` | **Prohibido** por exclusión (`TNN`) | **Prohibido** por exclusión (`TNN`) | Colisiona con `NO_REPETIR_TURNO_CONSECUTIVO` * |

> [!NOTE]
> \* **Escenario Noche (N):** Si la semana fuera de la familia Noche, Yésica tendría que trabajar de noche en la semana del 03/08 al 09/08. Sin embargo, ella trabaja de noche en la semana consecutiva (del 10/08 al 16/08), lo cual violaría la regla dura `NO_REPETIR_TURNO_CONSECUTIVO` y las distancias mínimas entre semanas de noche.

---

## 4. Conclusión del Solver

1. El primer fin de semana del mes (01/08 y 02/08) ya es un fin de semana **Medio** (trabaja el sábado de Tarde pero tiene franco el domingo).
2. El último fin de semana del mes (29/08 y 30/08) está reservado para su **FLR** (franco reglamentario largo de 4 días).
3. El fin de semana del 08/08 y 09/08 queda bloqueado lógicamente por sus exclusiones personales y la compatibilidad semanal de turnos, obligando a que sea un fin de semana **Libre**.
4. Con 1 finde medio, 1 libre y 1 FLR, a Yésica sólo le quedan disponibles el tercer y cuarto fin de semana para trabajar completos. Por ende, el máximo de fines de semana completos realizables es **2** (en lugar del target de 3).

El solver (con `MANEJO_FINDES` configurado como `SOFT`) prefiere asumir la penalización del target de Yésica en lugar de violar una regla `HARD` de exclusión o de mezcla semanal.

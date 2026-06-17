# Reporte de Auditoría de Configuración

- **Servicio:** Personal de Monitoreo (ID: 4)
- **Organización:** COM Juana Koslay
- **Período a Auditar:** 2026-07
- **Fecha Generación:** 2026-06-13 05:51:53

## 1. Resumen Servicio & Reglas Activas

### Reglas de Negocio Aplicables

| Código Regla | Tipo | Origen | Activo | Descripción | Parámetros |
| --- | --- | --- | --- | --- | --- |
| LIMITES_SOFT_RULES | SOFT | Servicio | Sí | Límite superior de horas mensuales para dimensionar variables del solver (MAX_HORAS_LIMITE_BASE) | `{"SEMANAS_BASE": 4, "MIN_HORAS_BASE": 108, "MAX_HORAS_LIMITE_BASE": 200, "MAX_ANUAL_LIMITE": 5000, "MAX_SEG_LIMITE_BASE": 50, "MAX_FINDES_LIMITE_BASE": 8}` |
| PENALIZACION_TURNO | SOFT | Servicio | Sí | Penaliza la asignación de un turno específico | `[{"turno": "00-06_Supervisor", "peso": 300, "solo_finde": true}, {"turno": "06-12_Supervisor", "peso": 300, "solo_finde": true}, {"turno": "12-18_Supervisor", "peso": 300, "solo_finde": true}, {"turno": "18-24_Supervisor", "peso": 300, "solo_finde": true}, {"turno": "00-06_Monitorista", "peso": 300, "solo_finde": true}, {"turno": "06-12_Monitorista", "peso": 300, "solo_finde": true}, {"turno": "12-18_Monitorista", "peso": 300, "solo_finde": true}, {"turno": "18-24_Monitorista", "peso": 300, "solo_finde": true}]` |
| PESO_BRECHA_DIARIA_PERSONAL | SOFT | Servicio | Sí | Peso de penalización por diferencia de personal asignado por día y puesto/turno | `{"peso_brecha": 100, "peso_cobertura": 10}` |
| PESO_BRECHA_MENSUAL | SOFT | Servicio | Sí | Peso de penalización por diferencia de horas en el mes | `{"peso": 50}` |
| PESO_EQUIDAD_FERIADOS | SOFT | Servicio | Sí | Peso de penalización por desigualdad en feriados trabajados anuales | `{"peso": 500}` |
| PESO_EQUIDAD_FINDES_MENSUAL | SOFT | Servicio | Sí | Peso de equidad de findes (solo cronograma actual) | `{"peso": 5000}` |
| MAX_DIAS_CONTINUOS | HARD | Servicio | Sí | Límite máximo de días consecutivos/seguidos de trabajo | `{"max_dias": 5}` |
| MAX_HORAS_MES_CALENDARIO | HARD | Servicio | Sí | Límite máximo estricto de horas a trabajar por mes calendario. JSON: {"max_horas": 144} | `{"max_horas": 120}` |
| MAX_HORAS_SEMANA | HARD | Servicio | Sí | Límite máximo de horas por semana | `{"limite": 30}` |
| MIN_HORAS_MES_CALENDARIO | HARD | Servicio | Sí | Mínimo de horas trabajadas más licencias por mes calendario. | `{"min_horas": 120, "minimo": 120}` |
| PERSONAL_ASOCIADO | HARD | Servicio | Sí | Siempre les toca turno juntos y franco juntos | `{"parejas": [["VERGARA Nazareno", "TORRES Yesica"], ["FERNANDEZ Claudia Elizabeth", "GUERRIDO Noelia"]]}` |
| UN_TURNO_POR_DIA | HARD | Servicio | Sí | Restriccion universal: una persona no puede tener mas de un turno asignado el mismo dia. No tiene parametros configurables. | `{}` |

### Ajustes Temporales de Servicio

*(Sin ajustes temporales del servicio en este período)*

## 2. Personal y Perfiles

| Nombre | Categoría | Rol | Régimen | Horas Reg. | Cumpleaños | M/P | Puestos |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ALCARAZ Xavier | B | Monitorista | - | - | - | - | Monitorista |
| BARROSO Alan | C | Monitorista | - | - | - | - | Monitorista |
| BRIZUELA Irma | C | Supervisor Suplente | - | - | - | - | Supervisor, Monitorista |
| ESCUDERO Gabriela | A | Monitorista | - | - | - | - | Monitorista |
| FERNANDEZ Celeste Ivana | A | Monitorista | - | - | - | - | Monitorista |
| FERNANDEZ Claudia Elizabeth | A | Supervisor Suplente | - | - | - | - | Supervisor |
| FERNANDEZ Juan Emir | A | Monitorista | - | - | - | - | Monitorista |
| FLORES Enzo | A | Monitorista | - | - | - | - | Monitorista |
| FLORES Jose Nicolas | C | Monitorista | - | - | - | - | Monitorista |
| FUNEZ Valeria Vanesa | D | Monitorista | - | - | - | - | Monitorista |
| GUERRERO Cesar | C | Monitorista | - | - | - | - | Monitorista |
| GUERRIDO Noelia | A | Supervisor Suplente | - | - | - | - | Supervisor, Monitorista |
| KOPRIVSEK Francisco | A | Monitorista | - | - | - | - | Monitorista |
| LEDESMA PAZ Micaela | B | Monitorista | - | - | - | - | Monitorista |
| MANSILLA Diego | B | Monitorista | - | - | - | - | Monitorista |
| MESSINA Eduardo | B | Monitorista | - | - | - | - | Monitorista |
| MIRANDA Luis | D | Monitorista | - | - | - | - | Monitorista |
| MOCDESE Marcelo Leonel | C | Monitorista | - | - | - | - | Monitorista |
| MUÑOZ Maria Carolina | D | Monitorista | - | - | - | - | Monitorista |
| OJEDA Miriam | B | Administracion | - | - | - | - | Monitorista, Administrativo |
| OLGUIN ALDECO Jennifer Sofia | A | Supervisor Titular | - | - | - | - | Supervisor |
| QUINTANA Felipe Gabriel | D | Monitorista | - | - | - | - | Monitorista |
| RODRIGUEZ Maximiliano | B | Monitorista | - | - | - | - | Monitorista |
| RUOCCO MUÑOZ Luis Alfredo | B | Supervisor Suplente | - | - | - | - | Supervisor, Monitorista |
| SANCIO Paola | B | Supervisor Titular | - | - | - | - | Supervisor |
| STEIMBRECHER Yolanda | B | Monitorista | - | - | - | - | Monitorista |
| SUAREZ Carolina | D | Supervisor Titular | - | - | - | - | Supervisor |
| SUÑER Mara Tatiana | C | Monitorista | - | - | - | - | Monitorista |
| TORRES Yesica | C | Supervisor Titular | - | - | - | - | Supervisor |
| VELEZ Facundo | D | Monitorista | - | - | - | - | Monitorista |
| VERGARA Mariano | D | Monitorista | - | - | - | - | Monitorista |
| VERGARA Nazareno | C | Monitorista | - | - | - | - | Monitorista |
| VILLEGAS Gaston | C | Monitorista | - | - | - | - | Monitorista |

### Reglas Individuales de Personal

| Profesional | Código Regla | Tipo | Descripción | Parámetros |
| --- | --- | --- | --- | --- |
| ALCARAZ Xavier | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["00-06_Monitorista", "12-18_Monitorista", "18-24_Monitorista", "00-06_Supervisor", "12-18_Supervisor", "18-24_Supervisor", "Administrativo"]}` |
| BARROSO Alan | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["00-06_Monitorista", "06-12_Monitorista", "18-24_Monitorista", "00-06_Supervisor", "06-12_Supervisor", "18-24_Supervisor", "Administrativo"]}` |
| BRIZUELA Irma | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["00-06_Monitorista", "12-18_Monitorista", "18-24_Monitorista", "00-06_Supervisor", "06-12_Supervisor", "Administrativo"]}` |
| ESCUDERO Gabriela | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["06-12_Monitorista", "12-18_Monitorista", "18-24_Monitorista", "06-12_Supervisor", "12-18_Supervisor", "18-24_Supervisor", "Administrativo"]}` |
| ESCUDERO Gabriela | MAX_HORAS_MES_CALENDARIO | HARD | Límite máximo estricto de horas a trabajar por mes calendario. JSON: {"max_horas": 144} | `{"max_horas": 6, "modo": "HARD"}` |
| FERNANDEZ Celeste Ivana | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["06-12_Monitorista", "12-18_Monitorista", "18-24_Monitorista", "06-12_Supervisor", "12-18_Supervisor", "18-24_Supervisor", "Administrativo"]}` |
| FERNANDEZ Celeste Ivana | MAX_HORAS_MES_CALENDARIO | HARD | Límite máximo estricto de horas a trabajar por mes calendario. JSON: {"max_horas": 144} | `{"max_horas": 6, "modo": "HARD"}` |
| FERNANDEZ Claudia Elizabeth | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["06-12_Monitorista", "12-18_Monitorista", "18-24_Monitorista", "06-12_Supervisor", "12-18_Supervisor", "18-24_Supervisor", "Administrativo"]}` |
| FERNANDEZ Juan Emir | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["06-12_Monitorista", "12-18_Monitorista", "18-24_Monitorista", "06-12_Supervisor", "12-18_Supervisor", "18-24_Supervisor", "Administrativo"]}` |
| FERNANDEZ Juan Emir | MAX_HORAS_MES_CALENDARIO | HARD | Límite máximo estricto de horas a trabajar por mes calendario. JSON: {"max_horas": 144} | `{"max_horas": 6, "modo": "HARD"}` |
| FLORES Enzo | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["06-12_Monitorista", "12-18_Monitorista", "18-24_Monitorista", "06-12_Supervisor", "12-18_Supervisor", "18-24_Supervisor", "Administrativo"]}` |
| FLORES Enzo | MAX_HORAS_MES_CALENDARIO | HARD | Límite máximo estricto de horas a trabajar por mes calendario. JSON: {"max_horas": 144} | `{"max_horas": 6, "modo": "HARD"}` |
| FLORES Jose Nicolas | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["00-06_Monitorista", "06-12_Monitorista", "18-24_Monitorista", "00-06_Supervisor", "06-12_Supervisor", "18-24_Supervisor", "Administrativo"]}` |
| FUNEZ Valeria Vanesa | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["00-06_Monitorista", "06-12_Monitorista", "12-18_Monitorista", "00-06_Supervisor", "06-12_Supervisor", "12-18_Supervisor", "Administrativo"]}` |
| GUERRERO Cesar | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["00-06_Monitorista", "06-12_Monitorista", "18-24_Monitorista", "00-06_Supervisor", "06-12_Supervisor", "18-24_Supervisor", "Administrativo"]}` |
| GUERRIDO Noelia | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["06-12_Monitorista", "12-18_Monitorista", "18-24_Monitorista", "06-12_Supervisor", "12-18_Supervisor", "18-24_Supervisor", "Administrativo"]}` |
| KOPRIVSEK Francisco | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["06-12_Monitorista", "12-18_Monitorista", "18-24_Monitorista", "06-12_Supervisor", "12-18_Supervisor", "18-24_Supervisor", "Administrativo"]}` |
| KOPRIVSEK Francisco | MAX_HORAS_MES_CALENDARIO | HARD | Límite máximo estricto de horas a trabajar por mes calendario. JSON: {"max_horas": 144} | `{"max_horas": 6, "modo": "HARD"}` |
| LEDESMA PAZ Micaela | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["00-06_Monitorista", "12-18_Monitorista", "18-24_Monitorista", "00-06_Supervisor", "12-18_Supervisor", "18-24_Supervisor", "Administrativo"]}` |
| MANSILLA Diego | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["00-06_Monitorista", "12-18_Monitorista", "18-24_Monitorista", "00-06_Supervisor", "12-18_Supervisor", "18-24_Supervisor", "Administrativo"]}` |
| MESSINA Eduardo | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["00-06_Monitorista", "12-18_Monitorista", "18-24_Monitorista", "00-06_Supervisor", "12-18_Supervisor", "18-24_Supervisor", "Administrativo"]}` |
| MIRANDA Luis | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["00-06_Monitorista", "06-12_Monitorista", "12-18_Monitorista", "00-06_Supervisor", "06-12_Supervisor", "12-18_Supervisor", "Administrativo"]}` |
| MOCDESE Marcelo Leonel | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["00-06_Monitorista", "06-12_Monitorista", "18-24_Monitorista", "00-06_Supervisor", "06-12_Supervisor", "18-24_Supervisor", "Administrativo"]}` |
| MUÑOZ Maria Carolina | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["00-06_Monitorista", "06-12_Monitorista", "12-18_Monitorista", "00-06_Supervisor", "06-12_Supervisor", "12-18_Supervisor", "Administrativo"]}` |
| OJEDA Miriam | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["00-06_Monitorista", "12-18_Monitorista", "18-24_Monitorista", "00-06_Supervisor", "12-18_Supervisor", "18-24_Supervisor"]}` |
| OLGUIN ALDECO Jennifer Sofia | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["06-12_Monitorista", "12-18_Monitorista", "18-24_Monitorista", "06-12_Supervisor", "12-18_Supervisor", "18-24_Supervisor", "Administrativo"]}` |
| QUINTANA Felipe Gabriel | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["00-06_Monitorista", "06-12_Monitorista", "12-18_Monitorista", "00-06_Supervisor", "06-12_Supervisor", "12-18_Supervisor", "Administrativo"]}` |
| RODRIGUEZ Maximiliano | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["00-06_Monitorista", "12-18_Monitorista", "18-24_Monitorista", "00-06_Supervisor", "12-18_Supervisor", "18-24_Supervisor", "Administrativo"]}` |
| RUOCCO MUÑOZ Luis Alfredo | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["00-06_Monitorista", "12-18_Monitorista", "18-24_Monitorista", "00-06_Supervisor", "12-18_Supervisor", "18-24_Supervisor", "Administrativo"]}` |
| SANCIO Paola | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["00-06_Monitorista", "12-18_Monitorista", "18-24_Monitorista", "00-06_Supervisor", "12-18_Supervisor", "18-24_Supervisor", "Administrativo"]}` |
| STEIMBRECHER Yolanda | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["00-06_Monitorista", "12-18_Monitorista", "18-24_Monitorista", "00-06_Supervisor", "12-18_Supervisor", "18-24_Supervisor", "Administrativo"]}` |
| SUAREZ Carolina | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["00-06_Monitorista", "06-12_Monitorista", "12-18_Monitorista", "00-06_Supervisor", "06-12_Supervisor", "12-18_Supervisor", "Administrativo"]}` |
| SUÑER Mara Tatiana | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["00-06_Monitorista", "06-12_Monitorista", "18-24_Monitorista", "00-06_Supervisor", "06-12_Supervisor", "18-24_Supervisor", "Administrativo"]}` |
| TORRES Yesica | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["00-06_Monitorista", "06-12_Monitorista", "18-24_Monitorista", "00-06_Supervisor", "06-12_Supervisor", "18-24_Supervisor", "Administrativo"]}` |
| VELEZ Facundo | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["00-06_Monitorista", "06-12_Monitorista", "12-18_Monitorista", "00-06_Supervisor", "06-12_Supervisor", "12-18_Supervisor", "Administrativo"]}` |
| VERGARA Mariano | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["00-06_Monitorista", "06-12_Monitorista", "12-18_Monitorista", "00-06_Supervisor", "06-12_Supervisor", "12-18_Supervisor", "Administrativo"]}` |
| VERGARA Nazareno | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["00-06_Monitorista", "06-12_Monitorista", "18-24_Monitorista", "00-06_Supervisor", "06-12_Supervisor", "18-24_Supervisor", "Administrativo"]}` |
| VILLEGAS Gaston | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["00-06_Monitorista", "06-12_Monitorista", "18-24_Monitorista", "00-06_Supervisor", "06-12_Supervisor", "18-24_Supervisor", "Administrativo"]}` |

## 3. Ajustes Personales & Licencias

### Ajustes Temporales de Reglas Personales

| Profesional | Código Regla | Inicio | Fin | Acción | Parámetros |
| --- | --- | --- | --- | --- | --- |
| FERNANDEZ Claudia Elizabeth | FINDES_COMPLETOS_Y_MEDIOS | 2026-06-01 | 2026-12-31 | SOBRESCRIBIR | `{"por_disponibilidad": {"5": {"completos": 2, "medios": 1}, "4": {"completos": 2, "medios": 0}, "3": {"completos": 1, "medios": 1}, "2": {"completos": 1, "medios": 0}, "1": {"completos": 1, "medios": 0}, "0": {"completos": 0, "medios": 0}}}` |
| GUERRIDO Noelia | FINDES_COMPLETOS_Y_MEDIOS | 2026-06-01 | 2026-12-31 | SOBRESCRIBIR | `{"por_disponibilidad": {"5": {"completos": 2, "medios": 1}, "4": {"completos": 2, "medios": 0}, "3": {"completos": 1, "medios": 1}, "2": {"completos": 1, "medios": 0}, "1": {"completos": 1, "medios": 0}, "0": {"completos": 0, "medios": 0}}}` |
| OLGUIN ALDECO Jennifer Sofia | FINDES_COMPLETOS_Y_MEDIOS | 2026-06-01 | 2026-12-31 | SOBRESCRIBIR | `{"por_disponibilidad": {"5": {"completos": 2, "medios": 1}, "4": {"completos": 2, "medios": 0}, "3": {"completos": 1, "medios": 1}, "2": {"completos": 1, "medios": 0}, "1": {"completos": 1, "medios": 0}, "0": {"completos": 0, "medios": 0}}}` |
| RUOCCO MUÑOZ Luis Alfredo | FINDES_COMPLETOS_Y_MEDIOS | 2026-06-01 | 2026-12-31 | SOBRESCRIBIR | `{"por_disponibilidad": {"5": {"completos": 2, "medios": 1}, "4": {"completos": 2, "medios": 0}, "3": {"completos": 1, "medios": 1}, "2": {"completos": 1, "medios": 0}, "1": {"completos": 1, "medios": 0}, "0": {"completos": 0, "medios": 0}}}` |
| SANCIO Paola | FINDES_COMPLETOS_Y_MEDIOS | 2026-06-01 | 2026-12-31 | SOBRESCRIBIR | `{"por_disponibilidad": {"5": {"completos": 2, "medios": 1}, "4": {"completos": 2, "medios": 0}, "3": {"completos": 1, "medios": 1}, "2": {"completos": 1, "medios": 0}, "1": {"completos": 1, "medios": 0}, "0": {"completos": 0, "medios": 0}}}` |

### Licencias Cargadas

*(Sin licencias activas en este período)*

### Asignaciones Fijas / Guardias Aprobadas

*(Sin guardias aprobadas / asignaciones previas para este período)*

## 4. Demanda y Oferta de Turnos

### Demanda Base (Vacantes Requeridas)

| Puesto | Tipo Día | Hora Inicio | Hora Fin | Mínimo | Máximo | Días Habilitados |
| --- | --- | --- | --- | --- | --- | --- |
| Administrativo | Semana | 06:00 | 12:00 | 0 | 1 | - |
| Monitorista | Finde_Feriado | 00:00 | 06:00 | 4 | 6 | - |
| Monitorista | Finde_Feriado | 00:00 | 06:00 | 0 | 0 | 5,6 |
| Monitorista | Finde_Feriado | 06:00 | 12:00 | 4 | 7 | - |
| Monitorista | Finde_Feriado | 12:00 | 18:00 | 4 | 7 | - |
| Monitorista | Finde_Feriado | 18:00 | 23:59 | 4 | 7 | - |
| Monitorista | Semana | 00:00 | 06:00 | 4 | 6 | - |
| Monitorista | Semana | 00:00 | 06:00 | 6 | 6 | 0 |
| Monitorista | Semana | 06:00 | 12:00 | 4 | 7 | - |
| Monitorista | Semana | 12:00 | 18:00 | 4 | 7 | - |
| Monitorista | Semana | 18:00 | 23:59 | 4 | 7 | - |
| Supervisor | Finde_Feriado | 00:00 | 06:00 | 1 | 2 | - |
| Supervisor | Finde_Feriado | 06:00 | 12:00 | 1 | 1 | - |
| Supervisor | Finde_Feriado | 12:00 | 18:00 | 1 | 1 | - |
| Supervisor | Finde_Feriado | 18:00 | 23:59 | 1 | 1 | - |
| Supervisor | Semana | 00:00 | 06:00 | 1 | 2 | - |
| Supervisor | Semana | 06:00 | 12:00 | 1 | 1 | - |
| Supervisor | Semana | 12:00 | 18:00 | 1 | 1 | - |
| Supervisor | Semana | 18:00 | 23:59 | 1 | 1 | - |

### Ajustes Temporales de Demanda

*(Sin ajustes de demanda activos en este período)*

### Oferta de Turnos Configurada

| Turno | Hora Inicio | Horas | Días Semana | Puesto | Orden |
| --- | --- | --- | --- | --- | --- |
| 00-06_Supervisor | 00:00 | 6 | 0,1,2,3,4,5,6 | Supervisor | 1 |
| 06-12_Supervisor | 06:00 | 6 | 0,1,2,3,4,5,6 | Supervisor | 2 |
| 12-18_Supervisor | 12:00 | 6 | 0,1,2,3,4,5,6 | Supervisor | 3 |
| 18-24_Supervisor | 18:00 | 6 | 0,1,2,3,4,5,6 | Supervisor | 4 |
| 00-06_Monitorista | 00:00 | 6 | 0,1,2,3,4,5,6 | Monitorista | 5 |
| 06-12_Monitorista | 06:00 | 6 | 0,1,2,3,4,5,6 | Monitorista | 6 |
| 12-18_Monitorista | 12:00 | 6 | 0,1,2,3,4,5,6 | Monitorista | 7 |
| 18-24_Monitorista | 18:00 | 6 | 0,1,2,3,4,5,6 | Monitorista | 8 |
| Administrativo | 06:00 | 6 | 0,1,2,3,4 | Administrativo | 9 |

### Ajustes Temporales de Turnos / Vacantes

*(Sin ajustes temporales de turnos activos en este período)*


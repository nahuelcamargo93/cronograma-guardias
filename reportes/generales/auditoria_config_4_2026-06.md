# Reporte de Auditoría de Configuración

- **Servicio:** Personal de Monitoreo (ID: 4)
- **Organización:** COM Juana Koslay
- **Período a Auditar:** 2026-06
- **Fecha Generación:** 2026-06-20 17:11:26

## 1. Resumen Servicio & Reglas Activas

### Reglas de Negocio Aplicables

| Código Regla | Tipo | Origen | Activo | Descripción | Parámetros |
| --- | --- | --- | --- | --- | --- |
| BRECHA_DIARIA_PERSONAL | SOFT | Servicio | Sí | Peso de penalización por diferencia de personal asignado por día y puesto/turno | `{"peso_brecha": 100, "peso_cobertura": 10}` |
| EQUIDAD_FERIADOS | SOFT | Servicio | Sí | Peso de penalización por desigualdad en feriados trabajados anuales | `{"peso": 500}` |
| EQUIDAD_FINDES_MENSUAL | SOFT | Servicio | Sí | Peso de equidad de findes (solo cronograma actual) | `{"peso": 5000}` |
| EQUIDAD_HORAS_MENSUALES | SOFT | Servicio | Sí | Peso de penalización por diferencia de horas en el mes | `{"peso": 50}` |
| LIMITES_SOFT_RULES | SOFT | Servicio | Sí | Límite superior de horas mensuales para dimensionar variables del solver (MAX_HORAS_LIMITE_BASE) | `{"SEMANAS_BASE": 4, "MIN_HORAS_BASE": 108, "MAX_HORAS_LIMITE_BASE": 200, "MAX_ANUAL_LIMITE": 5000, "MAX_SEG_LIMITE_BASE": 50, "MAX_FINDES_LIMITE_BASE": 8}` |
| PENALIZACION_TURNO | SOFT | Servicio | Sí | Penaliza la asignación de un turno específico | `[{"turno": "00-06_Supervisor", "peso": 300, "solo_finde": true}, {"turno": "06-12_Supervisor", "peso": 300, "solo_finde": true}, {"turno": "12-18_Supervisor", "peso": 300, "solo_finde": true}, {"turno": "18-24_Supervisor", "peso": 300, "solo_finde": true}, {"turno": "00-06_Monitorista", "peso": 300, "solo_finde": true}, {"turno": "06-12_Monitorista", "peso": 300, "solo_finde": true}, {"turno": "12-18_Monitorista", "peso": 300, "solo_finde": true}, {"turno": "18-24_Monitorista", "peso": 300, "solo_finde": true}]` |
| MAX_DIAS_CONTINUOS | HARD | Servicio | Sí | Límite máximo de días consecutivos/seguidos de trabajo | `{"max_dias": 5}` |
| MAX_HORAS_MES_CALENDARIO | HARD | Servicio | Sí | Límite máximo estricto de horas a trabajar por mes calendario. JSON: {"max_horas": 144} | `{"max_horas": 120, "modo": "SOFT", "peso_soft": 50000}` |
| MAX_HORAS_SEMANA | HARD | Servicio | Sí | Límite máximo de horas por semana | `{"limite": 30}` |
| MIN_HORAS_MES_CALENDARIO | HARD | Servicio | Sí | Mínimo de horas trabajadas más licencias por mes calendario. | `{"min_horas": 120, "modo": "SOFT", "peso_soft": 50000}` |
| PERSONAL_ASOCIADO | HARD | Servicio | Sí | Siempre les toca turno juntos y franco juntos | `{"parejas": [["VERGARA Nazareno", "TORRES Yesica"], ["OLGUIN ALDECO Jennifer Sofia", "FERNANDEZ Claudia Elizabeth"], ["QUINTANA Felipe Gabriel", "ROMERO Tomas"]]}` |
| UN_TURNO_POR_DIA | HARD | Servicio | Sí | Restriccion universal: una persona no puede tener mas de un turno asignado el mismo dia. No tiene parametros configurables. | `{}` |

### Ajustes Temporales de Servicio

*(Sin ajustes temporales del servicio en este período)*

## 2. Personal y Perfiles

| Nombre | Categoría | Rol | Régimen | Horas Reg. | Cumpleaños | M/P | Puestos |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ALCARAZ Xavier | B | Monitorista | - | - | - | - | Monitorista |
| BARROSO Alan | C | Monitorista | - | - | - | - | Monitorista |
| BRIZUELA Irma | C | Supervisor Suplente | - | - | - | - | Supervisor |
| CANO Avril | C | Monitorista | - | - | - | - | Monitorista |
| ESCUDERO Gabriela | A | Monitorista | - | - | - | - | Monitorista |
| FERNANDEZ Celeste Ivana | A | Monitorista | - | - | - | - | Monitorista |
| FERNANDEZ Claudia Elizabeth | A | Supervisor Suplente | - | - | - | - | Supervisor |
| FERNANDEZ Juan Emir | A | Monitorista | - | - | - | - | Monitorista |
| FLORES Jose Nicolas | B | Monitorista | - | - | - | - | Monitorista |
| FUNEZ Valeria Vanesa | D | Monitorista | - | - | - | - | Monitorista |
| GIMENEZ Adriana | A | Monitorista | - | - | - | - | Monitorista |
| GUERRERO Cesar | C | Monitorista | - | - | - | - | Monitorista |
| LEDESMA PAZ Micaela | B | Monitorista | - | - | - | - | Monitorista |
| MANSILLA Diego | B | Monitorista | - | - | - | - | Monitorista |
| MESSINA Eduardo | B | Monitorista | - | - | - | - | Monitorista |
| MIRANDA Luis | D | Monitorista | - | - | - | - | Monitorista |
| MOCDESE Marcelo Leonel | C | Monitorista | - | - | - | - | Monitorista |
| MUÑOZ Maria Carolina | D | Monitorista | - | - | - | - | Monitorista |
| OJEDA Miriam | B | Administracion | - | - | - | - | Administrativo |
| OLGUIN ALDECO Jennifer Sofia | A | Supervisor Titular | - | - | - | - | Supervisor |
| QUINTANA Felipe Gabriel | A | Supervisor Suplente | - | - | - | - | Supervisor, Monitorista |
| RODRIGUEZ Maximiliano | B | Monitorista | - | - | - | - | Monitorista |
| ROMERO Tomas | A | Supervisor Titular | - | - | - | - | Supervisor |
| RUOCCO MUÑOZ Luis Alfredo | B | Supervisor Suplente | - | - | - | - | Supervisor, Monitorista |
| SANCIO Paola | B | Supervisor Titular | - | - | - | - | Supervisor |
| STEIMBRECHER Yolanda | B | Monitorista | - | - | - | - | Monitorista |
| SUAREZ Carolina | D | Supervisor Titular | - | - | - | - | Supervisor |
| SUÑER Mara Tatiana | C | Monitorista | - | - | - | - | Monitorista |
| TORRES Yesica | C | Supervisor Titular | - | - | - | - | Supervisor |
| VELEZ Facundo | D | Monitorista | - | - | - | - | Monitorista |
| VERGARA Mariano | D | Monitorista | - | - | - | - | Monitorista |
| VERGARA Nazareno | C | Monitorista | - | - | - | - | Monitorista |
| VILLEGAS Angel | A | Monitorista | - | - | - | - | Monitorista |
| VILLEGAS Gaston | C | Monitorista | - | - | - | - | Monitorista |

### Reglas Individuales de Personal

| Profesional | Código Regla | Tipo | Descripción | Parámetros |
| --- | --- | --- | --- | --- |
| ALCARAZ Xavier | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["00-06_Monitorista", "12-18_Monitorista", "18-24_Monitorista", "00-06_Supervisor", "12-18_Supervisor", "18-24_Supervisor", "Administrativo"]}` |
| BARROSO Alan | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["00-06_Monitorista", "06-12_Monitorista", "18-24_Monitorista", "00-06_Supervisor", "06-12_Supervisor", "18-24_Supervisor", "Administrativo"]}` |
| BRIZUELA Irma | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `[{"turnos": ["00-06_Supervisor", "06-12_Supervisor"]}]` |
| CANO Avril | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["00-06_Monitorista", "06-12_Monitorista", "18-24_Monitorista", "00-06_Supervisor", "06-12_Supervisor", "18-24_Supervisor", "Administrativo"]}` |
| ESCUDERO Gabriela | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["06-12_Monitorista", "12-18_Monitorista", "18-24_Monitorista", "06-12_Supervisor", "12-18_Supervisor", "18-24_Supervisor", "Administrativo"]}` |
| ESCUDERO Gabriela | MAX_HORAS_MES_CALENDARIO | HARD | Límite máximo estricto de horas a trabajar por mes calendario. JSON: {"max_horas": 144} | `{"max_horas": 114, "modo": "SOFT", "peso_soft": 50000}` |
| ESCUDERO Gabriela | MIN_HORAS_MES_CALENDARIO | HARD | Mínimo de horas trabajadas más licencias por mes calendario. | `{"min_horas": 114, "modo": "SOFT", "peso_soft": 50000}` |
| FERNANDEZ Celeste Ivana | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["06-12_Monitorista", "12-18_Monitorista", "18-24_Monitorista", "06-12_Supervisor", "12-18_Supervisor", "18-24_Supervisor", "Administrativo"]}` |
| FERNANDEZ Celeste Ivana | MAX_HORAS_MES_CALENDARIO | HARD | Límite máximo estricto de horas a trabajar por mes calendario. JSON: {"max_horas": 144} | `{"max_horas": 114, "modo": "SOFT", "peso_soft": 50000}` |
| FERNANDEZ Celeste Ivana | MIN_HORAS_MES_CALENDARIO | HARD | Mínimo de horas trabajadas más licencias por mes calendario. | `{"min_horas": 114, "modo": "SOFT", "peso_soft": 50000}` |
| FERNANDEZ Claudia Elizabeth | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["06-12_Monitorista", "12-18_Monitorista", "18-24_Monitorista", "06-12_Supervisor", "12-18_Supervisor", "18-24_Supervisor", "Administrativo"]}` |
| FERNANDEZ Claudia Elizabeth | MAX_HORAS_MES_CALENDARIO | HARD | Límite máximo estricto de horas a trabajar por mes calendario. JSON: {"max_horas": 144} | `{"max_horas": 114, "modo": "SOFT", "peso_soft": 50000}` |
| FERNANDEZ Claudia Elizabeth | MIN_HORAS_MES_CALENDARIO | HARD | Mínimo de horas trabajadas más licencias por mes calendario. | `{"min_horas": 114, "modo": "SOFT", "peso_soft": 50000}` |
| FERNANDEZ Juan Emir | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["06-12_Monitorista", "12-18_Monitorista", "18-24_Monitorista", "06-12_Supervisor", "12-18_Supervisor", "18-24_Supervisor", "Administrativo"]}` |
| FERNANDEZ Juan Emir | MAX_HORAS_MES_CALENDARIO | HARD | Límite máximo estricto de horas a trabajar por mes calendario. JSON: {"max_horas": 144} | `{"max_horas": 114, "modo": "SOFT", "peso_soft": 50000}` |
| FERNANDEZ Juan Emir | MIN_HORAS_MES_CALENDARIO | HARD | Mínimo de horas trabajadas más licencias por mes calendario. | `{"min_horas": 114, "modo": "SOFT", "peso_soft": 50000}` |
| FLORES Enzo | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["06-12_Monitorista", "12-18_Monitorista", "18-24_Monitorista", "06-12_Supervisor", "12-18_Supervisor", "18-24_Supervisor", "Administrativo"]}` |
| FLORES Enzo | MAX_HORAS_MES_CALENDARIO | HARD | Límite máximo estricto de horas a trabajar por mes calendario. JSON: {"max_horas": 144} | `{"max_horas": 114, "modo": "SOFT", "peso_soft": 50000}` |
| FLORES Enzo | MIN_HORAS_MES_CALENDARIO | HARD | Mínimo de horas trabajadas más licencias por mes calendario. | `{"min_horas": 114, "modo": "SOFT", "peso_soft": 50000}` |
| FLORES Jose Nicolas | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["00-06_Monitorista", "12-18_Monitorista", "18-24_Monitorista", "00-06_Supervisor", "12-18_Supervisor", "18-24_Supervisor", "Administrativo"]}` |
| FUNEZ Valeria Vanesa | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["00-06_Monitorista", "06-12_Monitorista", "12-18_Monitorista", "00-06_Supervisor", "06-12_Supervisor", "12-18_Supervisor", "Administrativo"]}` |
| GIMENEZ Adriana | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["06-12_Monitorista", "12-18_Monitorista", "18-24_Monitorista", "06-12_Supervisor", "12-18_Supervisor", "18-24_Supervisor", "Administrativo"]}` |
| GUERRERO Cesar | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["00-06_Monitorista", "06-12_Monitorista", "18-24_Monitorista", "00-06_Supervisor", "06-12_Supervisor", "18-24_Supervisor", "Administrativo"]}` |
| GUERRIDO Noelia | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["06-12_Monitorista", "12-18_Monitorista", "18-24_Monitorista", "06-12_Supervisor", "12-18_Supervisor", "18-24_Supervisor", "Administrativo"]}` |
| GUERRIDO Noelia | MAX_HORAS_MES_CALENDARIO | HARD | Límite máximo estricto de horas a trabajar por mes calendario. JSON: {"max_horas": 144} | `{"max_horas": 114, "modo": "SOFT", "peso_soft": 50000}` |
| GUERRIDO Noelia | MIN_HORAS_MES_CALENDARIO | HARD | Mínimo de horas trabajadas más licencias por mes calendario. | `{"min_horas": 114, "modo": "SOFT", "peso_soft": 50000}` |
| KOPRIVSEK Francisco | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["06-12_Monitorista", "12-18_Monitorista", "18-24_Monitorista", "06-12_Supervisor", "12-18_Supervisor", "18-24_Supervisor", "Administrativo"]}` |
| KOPRIVSEK Francisco | MAX_HORAS_MES_CALENDARIO | HARD | Límite máximo estricto de horas a trabajar por mes calendario. JSON: {"max_horas": 144} | `{"max_horas": 114, "modo": "SOFT", "peso_soft": 50000}` |
| KOPRIVSEK Francisco | MIN_HORAS_MES_CALENDARIO | HARD | Mínimo de horas trabajadas más licencias por mes calendario. | `{"min_horas": 114, "modo": "SOFT", "peso_soft": 50000}` |
| LEDESMA PAZ Micaela | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["00-06_Monitorista", "12-18_Monitorista", "18-24_Monitorista", "00-06_Supervisor", "12-18_Supervisor", "18-24_Supervisor", "Administrativo"]}` |
| MANSILLA Diego | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["00-06_Monitorista", "12-18_Monitorista", "18-24_Monitorista", "00-06_Supervisor", "12-18_Supervisor", "18-24_Supervisor", "Administrativo"]}` |
| MESSINA Eduardo | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["00-06_Monitorista", "12-18_Monitorista", "18-24_Monitorista", "00-06_Supervisor", "12-18_Supervisor", "18-24_Supervisor", "Administrativo"]}` |
| MIRANDA Luis | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["00-06_Monitorista", "06-12_Monitorista", "12-18_Monitorista", "00-06_Supervisor", "06-12_Supervisor", "12-18_Supervisor", "Administrativo"]}` |
| MOCDESE Marcelo Leonel | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["00-06_Monitorista", "06-12_Monitorista", "18-24_Monitorista", "00-06_Supervisor", "06-12_Supervisor", "18-24_Supervisor", "Administrativo"]}` |
| MUÑOZ Maria Carolina | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["00-06_Monitorista", "06-12_Monitorista", "12-18_Monitorista", "00-06_Supervisor", "06-12_Supervisor", "12-18_Supervisor", "Administrativo"]}` |
| OJEDA Miriam | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["00-06_Monitorista", "12-18_Monitorista", "18-24_Monitorista", "00-06_Supervisor", "12-18_Supervisor", "18-24_Supervisor"]}` |
| OLGUIN ALDECO Jennifer Sofia | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["06-12_Monitorista", "12-18_Monitorista", "18-24_Monitorista", "06-12_Supervisor", "12-18_Supervisor", "18-24_Supervisor", "Administrativo"]}` |
| OLGUIN ALDECO Jennifer Sofia | MAX_HORAS_MES_CALENDARIO | HARD | Límite máximo estricto de horas a trabajar por mes calendario. JSON: {"max_horas": 144} | `{"max_horas": 114, "modo": "SOFT", "peso_soft": 50000}` |
| OLGUIN ALDECO Jennifer Sofia | MIN_HORAS_MES_CALENDARIO | HARD | Mínimo de horas trabajadas más licencias por mes calendario. | `{"min_horas": 114, "modo": "SOFT", "peso_soft": 50000}` |
| QUINTANA Felipe Gabriel | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["06-12_Monitorista", "12-18_Monitorista", "18-24_Monitorista", "06-12_Supervisor", "12-18_Supervisor", "18-24_Supervisor", "Administrativo"]}` |
| RODRIGUEZ Maximiliano | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["00-06_Monitorista", "12-18_Monitorista", "18-24_Monitorista", "00-06_Supervisor", "12-18_Supervisor", "18-24_Supervisor", "Administrativo"]}` |
| ROMERO Tomas | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["06-12_Monitorista", "12-18_Monitorista", "18-24_Monitorista", "06-12_Supervisor", "12-18_Supervisor", "18-24_Supervisor", "Administrativo"]}` |
| RUOCCO MUÑOZ Luis Alfredo | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["00-06_Monitorista", "12-18_Monitorista", "18-24_Monitorista", "00-06_Supervisor", "12-18_Supervisor", "18-24_Supervisor", "Administrativo"]}` |
| SANCIO Paola | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["00-06_Monitorista", "12-18_Monitorista", "18-24_Monitorista", "00-06_Supervisor", "12-18_Supervisor", "18-24_Supervisor", "Administrativo"]}` |
| STEIMBRECHER Yolanda | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["00-06_Monitorista", "12-18_Monitorista", "18-24_Monitorista", "00-06_Supervisor", "12-18_Supervisor", "18-24_Supervisor", "Administrativo"]}` |
| SUAREZ Carolina | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["00-06_Monitorista", "06-12_Monitorista", "12-18_Monitorista", "00-06_Supervisor", "06-12_Supervisor", "12-18_Supervisor", "Administrativo"]}` |
| SUÑER Mara Tatiana | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["00-06_Monitorista", "06-12_Monitorista", "18-24_Monitorista", "00-06_Supervisor", "06-12_Supervisor", "18-24_Supervisor", "Administrativo"]}` |
| TORRES Yesica | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["00-06_Monitorista", "06-12_Monitorista", "18-24_Monitorista", "00-06_Supervisor", "06-12_Supervisor", "18-24_Supervisor", "Administrativo"]}` |
| VELEZ Facundo | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["00-06_Monitorista", "06-12_Monitorista", "12-18_Monitorista", "00-06_Supervisor", "06-12_Supervisor", "12-18_Supervisor", "Administrativo"]}` |
| VERGARA Mariano | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["00-06_Monitorista", "06-12_Monitorista", "12-18_Monitorista", "00-06_Supervisor", "06-12_Supervisor", "12-18_Supervisor", "Administrativo"]}` |
| VERGARA Nazareno | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["00-06_Monitorista", "06-12_Monitorista", "18-24_Monitorista", "00-06_Supervisor", "06-12_Supervisor", "18-24_Supervisor", "Administrativo"]}` |
| VILLEGAS Angel | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["06-12_Monitorista", "12-18_Monitorista", "18-24_Monitorista", "06-12_Supervisor", "12-18_Supervisor", "18-24_Supervisor", "Administrativo"]}` |
| VILLEGAS Gaston | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `{"turnos": ["00-06_Monitorista", "06-12_Monitorista", "18-24_Monitorista", "00-06_Supervisor", "06-12_Supervisor", "18-24_Supervisor", "Administrativo"]}` |

## 3. Ajustes Personales & Licencias

### Ajustes Temporales de Reglas Personales

| Profesional | Código Regla | Inicio | Fin | Acción | Parámetros |
| --- | --- | --- | --- | --- | --- |
| ESCUDERO Gabriela | MIN_HORAS_MES_CALENDARIO | 2026-06-01 | 2026-06-30 | SOBRESCRIBIR | `{"min_horas": 114}` |
| FERNANDEZ Celeste Ivana | MIN_HORAS_MES_CALENDARIO | 2026-06-01 | 2026-06-30 | SOBRESCRIBIR | `{"min_horas": 114}` |
| FERNANDEZ Claudia Elizabeth | FINDES_COMPLETOS_Y_MEDIOS | 2026-06-01 | 2026-12-31 | SOBRESCRIBIR | `{"por_disponibilidad": {"5": {"completos": 2, "medios": 1}, "4": {"completos": 2, "medios": 0}, "3": {"completos": 1, "medios": 1}, "2": {"completos": 1, "medios": 0}, "1": {"completos": 1, "medios": 0}, "0": {"completos": 0, "medios": 0}}}` |
| FERNANDEZ Claudia Elizabeth | MIN_HORAS_MES_CALENDARIO | 2026-06-01 | 2026-06-30 | SOBRESCRIBIR | `{"min_horas": 114}` |
| FERNANDEZ Juan Emir | MIN_HORAS_MES_CALENDARIO | 2026-06-01 | 2026-06-30 | SOBRESCRIBIR | `{"min_horas": 114}` |
| FLORES Enzo | MIN_HORAS_MES_CALENDARIO | 2026-06-01 | 2026-06-30 | SOBRESCRIBIR | `{"min_horas": 114}` |
| GUERRIDO Noelia | FINDES_COMPLETOS_Y_MEDIOS | 2026-06-01 | 2026-12-31 | SOBRESCRIBIR | `{"por_disponibilidad": {"5": {"completos": 2, "medios": 1}, "4": {"completos": 2, "medios": 0}, "3": {"completos": 1, "medios": 1}, "2": {"completos": 1, "medios": 0}, "1": {"completos": 1, "medios": 0}, "0": {"completos": 0, "medios": 0}}}` |
| GUERRIDO Noelia | MIN_HORAS_MES_CALENDARIO | 2026-06-01 | 2026-06-30 | SOBRESCRIBIR | `{"min_horas": 114}` |
| GUERRIDO Noelia | MIN_HORAS_MES_CALENDARIO | 2026-06-01 | 2026-06-30 | SOBRESCRIBIR | `{"min_horas": 114}` |
| KOPRIVSEK Francisco | MIN_HORAS_MES_CALENDARIO | 2026-06-01 | 2026-06-30 | SOBRESCRIBIR | `{"min_horas": 114}` |
| OLGUIN ALDECO Jennifer Sofia | FINDES_COMPLETOS_Y_MEDIOS | 2026-06-01 | 2026-12-31 | SOBRESCRIBIR | `{"por_disponibilidad": {"5": {"completos": 2, "medios": 1}, "4": {"completos": 2, "medios": 0}, "3": {"completos": 1, "medios": 1}, "2": {"completos": 1, "medios": 0}, "1": {"completos": 1, "medios": 0}, "0": {"completos": 0, "medios": 0}}}` |
| OLGUIN ALDECO Jennifer Sofia | MIN_HORAS_MES_CALENDARIO | 2026-06-01 | 2026-06-30 | SOBRESCRIBIR | `{"min_horas": 114}` |
| RUOCCO MUÑOZ Luis Alfredo | FINDES_COMPLETOS_Y_MEDIOS | 2026-06-01 | 2026-12-31 | SOBRESCRIBIR | `{"por_disponibilidad": {"5": {"completos": 2, "medios": 1}, "4": {"completos": 2, "medios": 0}, "3": {"completos": 1, "medios": 1}, "2": {"completos": 1, "medios": 0}, "1": {"completos": 1, "medios": 0}, "0": {"completos": 0, "medios": 0}}}` |
| SANCIO Paola | FINDES_COMPLETOS_Y_MEDIOS | 2026-06-01 | 2026-12-31 | SOBRESCRIBIR | `{"por_disponibilidad": {"5": {"completos": 2, "medios": 1}, "4": {"completos": 2, "medios": 0}, "3": {"completos": 1, "medios": 1}, "2": {"completos": 1, "medios": 0}, "1": {"completos": 1, "medios": 0}, "0": {"completos": 0, "medios": 0}}}` |

### Licencias Cargadas

*(Sin licencias activas en este período)*

### Asignaciones Fijas / Guardias Aprobadas

| Profesional | Fecha | Turno | Horas | ID Crono | Notas Cronograma |
| --- | --- | --- | --- | --- | --- |
| BARROSO Alan | 2026-06-01 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| ESCUDERO Gabriela | 2026-06-01 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FERNANDEZ Celeste Ivana | 2026-06-01 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FERNANDEZ Claudia Elizabeth | 2026-06-01 | 00-06_Supervisor | 6 | 210 | Generado via CLI |
| FERNANDEZ Juan Emir | 2026-06-01 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FLORES Enzo | 2026-06-01 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| GUERRERO Cesar | 2026-06-01 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| GUERRIDO Noelia | 2026-06-01 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| KOPRIVSEK Francisco | 2026-06-01 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| LEDESMA PAZ Micaela | 2026-06-01 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MESSINA Eduardo | 2026-06-01 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MIRANDA Luis | 2026-06-01 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| MOCDESE Marcelo Leonel | 2026-06-01 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| OJEDA Miriam | 2026-06-01 | Administrativo | 6 | 210 | Generado via CLI |
| QUINTANA Felipe Gabriel | 2026-06-01 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| RODRIGUEZ Maximiliano | 2026-06-01 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| RUOCCO MUÑOZ Luis Alfredo | 2026-06-01 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| SANCIO Paola | 2026-06-01 | 06-12_Supervisor | 6 | 210 | Generado via CLI |
| STEIMBRECHER Yolanda | 2026-06-01 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| SUAREZ Carolina | 2026-06-01 | 18-24_Supervisor | 6 | 210 | Generado via CLI |
| SUÑER Mara Tatiana | 2026-06-01 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| TORRES Yesica | 2026-06-01 | 12-18_Supervisor | 6 | 210 | Generado via CLI |
| VELEZ Facundo | 2026-06-01 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| VERGARA Mariano | 2026-06-01 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| VERGARA Nazareno | 2026-06-01 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| VILLEGAS Gaston | 2026-06-01 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| ALCARAZ Xavier | 2026-06-02 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| BARROSO Alan | 2026-06-02 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| BRIZUELA Irma | 2026-06-02 | 12-18_Supervisor | 6 | 210 | Generado via CLI |
| ESCUDERO Gabriela | 2026-06-02 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FERNANDEZ Celeste Ivana | 2026-06-02 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FERNANDEZ Claudia Elizabeth | 2026-06-02 | 00-06_Supervisor | 6 | 210 | Generado via CLI |
| FERNANDEZ Juan Emir | 2026-06-02 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FLORES Jose Nicolas | 2026-06-02 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| FUNEZ Valeria Vanesa | 2026-06-02 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| GUERRIDO Noelia | 2026-06-02 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| KOPRIVSEK Francisco | 2026-06-02 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| LEDESMA PAZ Micaela | 2026-06-02 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MANSILLA Diego | 2026-06-02 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MESSINA Eduardo | 2026-06-02 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MIRANDA Luis | 2026-06-02 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| MOCDESE Marcelo Leonel | 2026-06-02 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| OJEDA Miriam | 2026-06-02 | Administrativo | 6 | 210 | Generado via CLI |
| OLGUIN ALDECO Jennifer Sofia | 2026-06-02 | 00-06_Supervisor | 6 | 210 | Generado via CLI |
| QUINTANA Felipe Gabriel | 2026-06-02 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| SANCIO Paola | 2026-06-02 | 06-12_Supervisor | 6 | 210 | Generado via CLI |
| STEIMBRECHER Yolanda | 2026-06-02 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| SUAREZ Carolina | 2026-06-02 | 18-24_Supervisor | 6 | 210 | Generado via CLI |
| VERGARA Mariano | 2026-06-02 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| VILLEGAS Gaston | 2026-06-02 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| ALCARAZ Xavier | 2026-06-03 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| BARROSO Alan | 2026-06-03 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| ESCUDERO Gabriela | 2026-06-03 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FERNANDEZ Celeste Ivana | 2026-06-03 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FERNANDEZ Claudia Elizabeth | 2026-06-03 | 00-06_Supervisor | 6 | 210 | Generado via CLI |
| FLORES Enzo | 2026-06-03 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FLORES Jose Nicolas | 2026-06-03 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| FUNEZ Valeria Vanesa | 2026-06-03 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| GUERRIDO Noelia | 2026-06-03 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| MESSINA Eduardo | 2026-06-03 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MIRANDA Luis | 2026-06-03 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| MOCDESE Marcelo Leonel | 2026-06-03 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| MUÑOZ Maria Carolina | 2026-06-03 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| OJEDA Miriam | 2026-06-03 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| QUINTANA Felipe Gabriel | 2026-06-03 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| RODRIGUEZ Maximiliano | 2026-06-03 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| RUOCCO MUÑOZ Luis Alfredo | 2026-06-03 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| SANCIO Paola | 2026-06-03 | 06-12_Supervisor | 6 | 210 | Generado via CLI |
| SUAREZ Carolina | 2026-06-03 | 18-24_Supervisor | 6 | 210 | Generado via CLI |
| SUÑER Mara Tatiana | 2026-06-03 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| TORRES Yesica | 2026-06-03 | 12-18_Supervisor | 6 | 210 | Generado via CLI |
| VERGARA Nazareno | 2026-06-03 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| BRIZUELA Irma | 2026-06-04 | 18-24_Supervisor | 6 | 210 | Generado via CLI |
| ESCUDERO Gabriela | 2026-06-04 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FERNANDEZ Claudia Elizabeth | 2026-06-04 | 00-06_Supervisor | 6 | 210 | Generado via CLI |
| FERNANDEZ Juan Emir | 2026-06-04 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FLORES Jose Nicolas | 2026-06-04 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| FUNEZ Valeria Vanesa | 2026-06-04 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| GUERRERO Cesar | 2026-06-04 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| GUERRIDO Noelia | 2026-06-04 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| KOPRIVSEK Francisco | 2026-06-04 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| LEDESMA PAZ Micaela | 2026-06-04 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MANSILLA Diego | 2026-06-04 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MESSINA Eduardo | 2026-06-04 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MIRANDA Luis | 2026-06-04 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| MUÑOZ Maria Carolina | 2026-06-04 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| OJEDA Miriam | 2026-06-04 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| RODRIGUEZ Maximiliano | 2026-06-04 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| RUOCCO MUÑOZ Luis Alfredo | 2026-06-04 | 06-12_Supervisor | 6 | 210 | Generado via CLI |
| STEIMBRECHER Yolanda | 2026-06-04 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| SUÑER Mara Tatiana | 2026-06-04 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| TORRES Yesica | 2026-06-04 | 12-18_Supervisor | 6 | 210 | Generado via CLI |
| VERGARA Mariano | 2026-06-04 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| VERGARA Nazareno | 2026-06-04 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| VILLEGAS Gaston | 2026-06-04 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| ALCARAZ Xavier | 2026-06-05 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| BARROSO Alan | 2026-06-05 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| BRIZUELA Irma | 2026-06-05 | 18-24_Supervisor | 6 | 210 | Generado via CLI |
| FERNANDEZ Celeste Ivana | 2026-06-05 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FERNANDEZ Claudia Elizabeth | 2026-06-05 | 00-06_Supervisor | 6 | 210 | Generado via CLI |
| FERNANDEZ Juan Emir | 2026-06-05 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FLORES Enzo | 2026-06-05 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FUNEZ Valeria Vanesa | 2026-06-05 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| GUERRERO Cesar | 2026-06-05 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| GUERRIDO Noelia | 2026-06-05 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| KOPRIVSEK Francisco | 2026-06-05 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| LEDESMA PAZ Micaela | 2026-06-05 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MANSILLA Diego | 2026-06-05 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MESSINA Eduardo | 2026-06-05 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MIRANDA Luis | 2026-06-05 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| MUÑOZ Maria Carolina | 2026-06-05 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| OJEDA Miriam | 2026-06-05 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| OLGUIN ALDECO Jennifer Sofia | 2026-06-05 | 00-06_Supervisor | 6 | 210 | Generado via CLI |
| SANCIO Paola | 2026-06-05 | 06-12_Supervisor | 6 | 210 | Generado via CLI |
| TORRES Yesica | 2026-06-05 | 12-18_Supervisor | 6 | 210 | Generado via CLI |
| VELEZ Facundo | 2026-06-05 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| VERGARA Nazareno | 2026-06-05 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| VILLEGAS Gaston | 2026-06-05 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| ALCARAZ Xavier | 2026-06-06 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| BRIZUELA Irma | 2026-06-06 | 12-18_Supervisor | 6 | 210 | Generado via CLI |
| GUERRERO Cesar | 2026-06-06 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| MANSILLA Diego | 2026-06-06 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MOCDESE Marcelo Leonel | 2026-06-06 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| MUÑOZ Maria Carolina | 2026-06-06 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| OLGUIN ALDECO Jennifer Sofia | 2026-06-06 | 00-06_Supervisor | 6 | 210 | Generado via CLI |
| QUINTANA Felipe Gabriel | 2026-06-06 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| RODRIGUEZ Maximiliano | 2026-06-06 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| RUOCCO MUÑOZ Luis Alfredo | 2026-06-06 | 06-12_Supervisor | 6 | 210 | Generado via CLI |
| STEIMBRECHER Yolanda | 2026-06-06 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| SUAREZ Carolina | 2026-06-06 | 18-24_Supervisor | 6 | 210 | Generado via CLI |
| SUÑER Mara Tatiana | 2026-06-06 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| VELEZ Facundo | 2026-06-06 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| VERGARA Mariano | 2026-06-06 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| VILLEGAS Gaston | 2026-06-06 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| ALCARAZ Xavier | 2026-06-07 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| BRIZUELA Irma | 2026-06-07 | 12-18_Supervisor | 6 | 210 | Generado via CLI |
| FLORES Jose Nicolas | 2026-06-07 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| GUERRERO Cesar | 2026-06-07 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| MANSILLA Diego | 2026-06-07 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MOCDESE Marcelo Leonel | 2026-06-07 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| MUÑOZ Maria Carolina | 2026-06-07 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| OLGUIN ALDECO Jennifer Sofia | 2026-06-07 | 00-06_Supervisor | 6 | 210 | Generado via CLI |
| QUINTANA Felipe Gabriel | 2026-06-07 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| RODRIGUEZ Maximiliano | 2026-06-07 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| RUOCCO MUÑOZ Luis Alfredo | 2026-06-07 | 06-12_Supervisor | 6 | 210 | Generado via CLI |
| STEIMBRECHER Yolanda | 2026-06-07 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| SUAREZ Carolina | 2026-06-07 | 18-24_Supervisor | 6 | 210 | Generado via CLI |
| SUÑER Mara Tatiana | 2026-06-07 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| VELEZ Facundo | 2026-06-07 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| VERGARA Mariano | 2026-06-07 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| ALCARAZ Xavier | 2026-06-08 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| BARROSO Alan | 2026-06-08 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| ESCUDERO Gabriela | 2026-06-08 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FERNANDEZ Celeste Ivana | 2026-06-08 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FERNANDEZ Claudia Elizabeth | 2026-06-08 | 00-06_Supervisor | 6 | 210 | Generado via CLI |
| FERNANDEZ Juan Emir | 2026-06-08 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FLORES Enzo | 2026-06-08 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FLORES Jose Nicolas | 2026-06-08 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| FUNEZ Valeria Vanesa | 2026-06-08 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| GUERRIDO Noelia | 2026-06-08 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| KOPRIVSEK Francisco | 2026-06-08 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| MESSINA Eduardo | 2026-06-08 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MIRANDA Luis | 2026-06-08 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| QUINTANA Felipe Gabriel | 2026-06-08 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| RUOCCO MUÑOZ Luis Alfredo | 2026-06-08 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| SANCIO Paola | 2026-06-08 | 06-12_Supervisor | 6 | 210 | Generado via CLI |
| STEIMBRECHER Yolanda | 2026-06-08 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| SUAREZ Carolina | 2026-06-08 | 18-24_Supervisor | 6 | 210 | Generado via CLI |
| SUÑER Mara Tatiana | 2026-06-08 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| TORRES Yesica | 2026-06-08 | 12-18_Supervisor | 6 | 210 | Generado via CLI |
| VELEZ Facundo | 2026-06-08 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| VERGARA Nazareno | 2026-06-08 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| BRIZUELA Irma | 2026-06-09 | 18-24_Supervisor | 6 | 210 | Generado via CLI |
| FERNANDEZ Celeste Ivana | 2026-06-09 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FERNANDEZ Juan Emir | 2026-06-09 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FLORES Enzo | 2026-06-09 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FLORES Jose Nicolas | 2026-06-09 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| KOPRIVSEK Francisco | 2026-06-09 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| LEDESMA PAZ Micaela | 2026-06-09 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MANSILLA Diego | 2026-06-09 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MESSINA Eduardo | 2026-06-09 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MIRANDA Luis | 2026-06-09 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| MOCDESE Marcelo Leonel | 2026-06-09 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| MUÑOZ Maria Carolina | 2026-06-09 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| OLGUIN ALDECO Jennifer Sofia | 2026-06-09 | 00-06_Supervisor | 6 | 210 | Generado via CLI |
| QUINTANA Felipe Gabriel | 2026-06-09 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| RODRIGUEZ Maximiliano | 2026-06-09 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| SANCIO Paola | 2026-06-09 | 06-12_Supervisor | 6 | 210 | Generado via CLI |
| STEIMBRECHER Yolanda | 2026-06-09 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| SUÑER Mara Tatiana | 2026-06-09 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| TORRES Yesica | 2026-06-09 | 12-18_Supervisor | 6 | 210 | Generado via CLI |
| VERGARA Mariano | 2026-06-09 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| VERGARA Nazareno | 2026-06-09 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| BRIZUELA Irma | 2026-06-10 | 12-18_Supervisor | 6 | 210 | Generado via CLI |
| ESCUDERO Gabriela | 2026-06-10 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FERNANDEZ Claudia Elizabeth | 2026-06-10 | 00-06_Supervisor | 6 | 210 | Generado via CLI |
| FERNANDEZ Juan Emir | 2026-06-10 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FLORES Enzo | 2026-06-10 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FLORES Jose Nicolas | 2026-06-10 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| FUNEZ Valeria Vanesa | 2026-06-10 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| GUERRERO Cesar | 2026-06-10 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| GUERRIDO Noelia | 2026-06-10 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| KOPRIVSEK Francisco | 2026-06-10 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| LEDESMA PAZ Micaela | 2026-06-10 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MESSINA Eduardo | 2026-06-10 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MIRANDA Luis | 2026-06-10 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| MOCDESE Marcelo Leonel | 2026-06-10 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| MUÑOZ Maria Carolina | 2026-06-10 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| OJEDA Miriam | 2026-06-10 | Administrativo | 6 | 210 | Generado via CLI |
| OLGUIN ALDECO Jennifer Sofia | 2026-06-10 | 00-06_Supervisor | 6 | 210 | Generado via CLI |
| RUOCCO MUÑOZ Luis Alfredo | 2026-06-10 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| SANCIO Paola | 2026-06-10 | 06-12_Supervisor | 6 | 210 | Generado via CLI |
| STEIMBRECHER Yolanda | 2026-06-10 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| SUAREZ Carolina | 2026-06-10 | 18-24_Supervisor | 6 | 210 | Generado via CLI |
| VERGARA Mariano | 2026-06-10 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| VILLEGAS Gaston | 2026-06-10 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| ALCARAZ Xavier | 2026-06-11 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| BARROSO Alan | 2026-06-11 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| BRIZUELA Irma | 2026-06-11 | 18-24_Supervisor | 6 | 210 | Generado via CLI |
| ESCUDERO Gabriela | 2026-06-11 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FERNANDEZ Celeste Ivana | 2026-06-11 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FERNANDEZ Juan Emir | 2026-06-11 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FUNEZ Valeria Vanesa | 2026-06-11 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| GUERRERO Cesar | 2026-06-11 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| KOPRIVSEK Francisco | 2026-06-11 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| LEDESMA PAZ Micaela | 2026-06-11 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MANSILLA Diego | 2026-06-11 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MOCDESE Marcelo Leonel | 2026-06-11 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| MUÑOZ Maria Carolina | 2026-06-11 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| OJEDA Miriam | 2026-06-11 | Administrativo | 6 | 210 | Generado via CLI |
| OLGUIN ALDECO Jennifer Sofia | 2026-06-11 | 00-06_Supervisor | 6 | 210 | Generado via CLI |
| RODRIGUEZ Maximiliano | 2026-06-11 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| RUOCCO MUÑOZ Luis Alfredo | 2026-06-11 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| SANCIO Paola | 2026-06-11 | 06-12_Supervisor | 6 | 210 | Generado via CLI |
| SUÑER Mara Tatiana | 2026-06-11 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| TORRES Yesica | 2026-06-11 | 12-18_Supervisor | 6 | 210 | Generado via CLI |
| VELEZ Facundo | 2026-06-11 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| VERGARA Mariano | 2026-06-11 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| VERGARA Nazareno | 2026-06-11 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| BARROSO Alan | 2026-06-12 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| BRIZUELA Irma | 2026-06-12 | 12-18_Supervisor | 6 | 210 | Generado via CLI |
| ESCUDERO Gabriela | 2026-06-12 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FERNANDEZ Celeste Ivana | 2026-06-12 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FERNANDEZ Juan Emir | 2026-06-12 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FLORES Enzo | 2026-06-12 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FUNEZ Valeria Vanesa | 2026-06-12 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| GUERRERO Cesar | 2026-06-12 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| LEDESMA PAZ Micaela | 2026-06-12 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MANSILLA Diego | 2026-06-12 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MESSINA Eduardo | 2026-06-12 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MOCDESE Marcelo Leonel | 2026-06-12 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| OLGUIN ALDECO Jennifer Sofia | 2026-06-12 | 00-06_Supervisor | 6 | 210 | Generado via CLI |
| QUINTANA Felipe Gabriel | 2026-06-12 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| RODRIGUEZ Maximiliano | 2026-06-12 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| SANCIO Paola | 2026-06-12 | 06-12_Supervisor | 6 | 210 | Generado via CLI |
| STEIMBRECHER Yolanda | 2026-06-12 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| SUAREZ Carolina | 2026-06-12 | 18-24_Supervisor | 6 | 210 | Generado via CLI |
| SUÑER Mara Tatiana | 2026-06-12 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| VELEZ Facundo | 2026-06-12 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| VERGARA Mariano | 2026-06-12 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| VILLEGAS Gaston | 2026-06-12 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| ALCARAZ Xavier | 2026-06-13 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| BARROSO Alan | 2026-06-13 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| FERNANDEZ Claudia Elizabeth | 2026-06-13 | 00-06_Supervisor | 6 | 210 | Generado via CLI |
| FLORES Jose Nicolas | 2026-06-13 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| GUERRIDO Noelia | 2026-06-13 | 00-06_Supervisor | 6 | 210 | Generado via CLI |
| MANSILLA Diego | 2026-06-13 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MESSINA Eduardo | 2026-06-13 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MIRANDA Luis | 2026-06-13 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| MUÑOZ Maria Carolina | 2026-06-13 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| OJEDA Miriam | 2026-06-13 | Administrativo | 6 | 210 | Generado via CLI |
| RODRIGUEZ Maximiliano | 2026-06-13 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| RUOCCO MUÑOZ Luis Alfredo | 2026-06-13 | 06-12_Supervisor | 6 | 210 | Generado via CLI |
| SUAREZ Carolina | 2026-06-13 | 18-24_Supervisor | 6 | 210 | Generado via CLI |
| TORRES Yesica | 2026-06-13 | 12-18_Supervisor | 6 | 210 | Generado via CLI |
| VELEZ Facundo | 2026-06-13 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| VERGARA Mariano | 2026-06-13 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| VERGARA Nazareno | 2026-06-13 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| VILLEGAS Gaston | 2026-06-13 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| ALCARAZ Xavier | 2026-06-14 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| BARROSO Alan | 2026-06-14 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| FERNANDEZ Claudia Elizabeth | 2026-06-14 | 00-06_Supervisor | 6 | 210 | Generado via CLI |
| FLORES Jose Nicolas | 2026-06-14 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| FUNEZ Valeria Vanesa | 2026-06-14 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| GUERRIDO Noelia | 2026-06-14 | 00-06_Supervisor | 6 | 210 | Generado via CLI |
| LEDESMA PAZ Micaela | 2026-06-14 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MANSILLA Diego | 2026-06-14 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MUÑOZ Maria Carolina | 2026-06-14 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| OJEDA Miriam | 2026-06-14 | Administrativo | 6 | 210 | Generado via CLI |
| QUINTANA Felipe Gabriel | 2026-06-14 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| RODRIGUEZ Maximiliano | 2026-06-14 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| RUOCCO MUÑOZ Luis Alfredo | 2026-06-14 | 06-12_Supervisor | 6 | 210 | Generado via CLI |
| SUAREZ Carolina | 2026-06-14 | 18-24_Supervisor | 6 | 210 | Generado via CLI |
| SUÑER Mara Tatiana | 2026-06-14 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| TORRES Yesica | 2026-06-14 | 12-18_Supervisor | 6 | 210 | Generado via CLI |
| VELEZ Facundo | 2026-06-14 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| VERGARA Nazareno | 2026-06-14 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| BRIZUELA Irma | 2026-06-15 | 12-18_Supervisor | 6 | 210 | Generado via CLI |
| ESCUDERO Gabriela | 2026-06-15 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FERNANDEZ Celeste Ivana | 2026-06-15 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FERNANDEZ Juan Emir | 2026-06-15 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FLORES Enzo | 2026-06-15 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FLORES Jose Nicolas | 2026-06-15 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| FUNEZ Valeria Vanesa | 2026-06-15 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| GUERRERO Cesar | 2026-06-15 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| KOPRIVSEK Francisco | 2026-06-15 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| MESSINA Eduardo | 2026-06-15 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MOCDESE Marcelo Leonel | 2026-06-15 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| MUÑOZ Maria Carolina | 2026-06-15 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| OJEDA Miriam | 2026-06-15 | Administrativo | 6 | 210 | Generado via CLI |
| OLGUIN ALDECO Jennifer Sofia | 2026-06-15 | 00-06_Supervisor | 6 | 210 | Generado via CLI |
| QUINTANA Felipe Gabriel | 2026-06-15 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| RODRIGUEZ Maximiliano | 2026-06-15 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| RUOCCO MUÑOZ Luis Alfredo | 2026-06-15 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| SANCIO Paola | 2026-06-15 | 06-12_Supervisor | 6 | 210 | Generado via CLI |
| STEIMBRECHER Yolanda | 2026-06-15 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| SUAREZ Carolina | 2026-06-15 | 18-24_Supervisor | 6 | 210 | Generado via CLI |
| SUÑER Mara Tatiana | 2026-06-15 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| VERGARA Mariano | 2026-06-15 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| ALCARAZ Xavier | 2026-06-16 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| BARROSO Alan | 2026-06-16 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| ESCUDERO Gabriela | 2026-06-16 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FERNANDEZ Claudia Elizabeth | 2026-06-16 | 00-06_Supervisor | 6 | 210 | Generado via CLI |
| FERNANDEZ Juan Emir | 2026-06-16 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FLORES Enzo | 2026-06-16 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| GUERRERO Cesar | 2026-06-16 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| GUERRIDO Noelia | 2026-06-16 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| KOPRIVSEK Francisco | 2026-06-16 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| LEDESMA PAZ Micaela | 2026-06-16 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MANSILLA Diego | 2026-06-16 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MESSINA Eduardo | 2026-06-16 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MIRANDA Luis | 2026-06-16 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| MUÑOZ Maria Carolina | 2026-06-16 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| OLGUIN ALDECO Jennifer Sofia | 2026-06-16 | 00-06_Supervisor | 6 | 210 | Generado via CLI |
| QUINTANA Felipe Gabriel | 2026-06-16 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| SANCIO Paola | 2026-06-16 | 06-12_Supervisor | 6 | 210 | Generado via CLI |
| STEIMBRECHER Yolanda | 2026-06-16 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| SUAREZ Carolina | 2026-06-16 | 18-24_Supervisor | 6 | 210 | Generado via CLI |
| TORRES Yesica | 2026-06-16 | 12-18_Supervisor | 6 | 210 | Generado via CLI |
| VERGARA Mariano | 2026-06-16 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| VERGARA Nazareno | 2026-06-16 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| VILLEGAS Gaston | 2026-06-16 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| ALCARAZ Xavier | 2026-06-17 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| BARROSO Alan | 2026-06-17 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| BRIZUELA Irma | 2026-06-17 | 18-24_Supervisor | 6 | 210 | Generado via CLI |
| FERNANDEZ Celeste Ivana | 2026-06-17 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FERNANDEZ Juan Emir | 2026-06-17 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FLORES Enzo | 2026-06-17 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FLORES Jose Nicolas | 2026-06-17 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| KOPRIVSEK Francisco | 2026-06-17 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| MESSINA Eduardo | 2026-06-17 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MIRANDA Luis | 2026-06-17 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| MOCDESE Marcelo Leonel | 2026-06-17 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| MUÑOZ Maria Carolina | 2026-06-17 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| OJEDA Miriam | 2026-06-17 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| OLGUIN ALDECO Jennifer Sofia | 2026-06-17 | 00-06_Supervisor | 6 | 210 | Generado via CLI |
| RODRIGUEZ Maximiliano | 2026-06-17 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| RUOCCO MUÑOZ Luis Alfredo | 2026-06-17 | 06-12_Supervisor | 6 | 210 | Generado via CLI |
| STEIMBRECHER Yolanda | 2026-06-17 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| SUÑER Mara Tatiana | 2026-06-17 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| TORRES Yesica | 2026-06-17 | 12-18_Supervisor | 6 | 210 | Generado via CLI |
| VELEZ Facundo | 2026-06-17 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| VERGARA Mariano | 2026-06-17 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| VERGARA Nazareno | 2026-06-17 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| VILLEGAS Gaston | 2026-06-17 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| BARROSO Alan | 2026-06-18 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| ESCUDERO Gabriela | 2026-06-18 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FERNANDEZ Celeste Ivana | 2026-06-18 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FERNANDEZ Juan Emir | 2026-06-18 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FLORES Enzo | 2026-06-18 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FLORES Jose Nicolas | 2026-06-18 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| FUNEZ Valeria Vanesa | 2026-06-18 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| GUERRERO Cesar | 2026-06-18 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| KOPRIVSEK Francisco | 2026-06-18 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| LEDESMA PAZ Micaela | 2026-06-18 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MANSILLA Diego | 2026-06-18 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MIRANDA Luis | 2026-06-18 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| MOCDESE Marcelo Leonel | 2026-06-18 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| OLGUIN ALDECO Jennifer Sofia | 2026-06-18 | 00-06_Supervisor | 6 | 210 | Generado via CLI |
| QUINTANA Felipe Gabriel | 2026-06-18 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| RODRIGUEZ Maximiliano | 2026-06-18 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| RUOCCO MUÑOZ Luis Alfredo | 2026-06-18 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| SANCIO Paola | 2026-06-18 | 06-12_Supervisor | 6 | 210 | Generado via CLI |
| SUAREZ Carolina | 2026-06-18 | 18-24_Supervisor | 6 | 210 | Generado via CLI |
| TORRES Yesica | 2026-06-18 | 12-18_Supervisor | 6 | 210 | Generado via CLI |
| VELEZ Facundo | 2026-06-18 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| VERGARA Nazareno | 2026-06-18 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| VILLEGAS Gaston | 2026-06-18 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| ALCARAZ Xavier | 2026-06-19 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| BRIZUELA Irma | 2026-06-19 | 12-18_Supervisor | 6 | 210 | Generado via CLI |
| ESCUDERO Gabriela | 2026-06-19 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FERNANDEZ Celeste Ivana | 2026-06-19 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FERNANDEZ Claudia Elizabeth | 2026-06-19 | 00-06_Supervisor | 6 | 210 | Generado via CLI |
| FERNANDEZ Juan Emir | 2026-06-19 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FLORES Enzo | 2026-06-19 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FUNEZ Valeria Vanesa | 2026-06-19 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| GUERRERO Cesar | 2026-06-19 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| GUERRIDO Noelia | 2026-06-19 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| MANSILLA Diego | 2026-06-19 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MOCDESE Marcelo Leonel | 2026-06-19 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| MUÑOZ Maria Carolina | 2026-06-19 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| OJEDA Miriam | 2026-06-19 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| OLGUIN ALDECO Jennifer Sofia | 2026-06-19 | 00-06_Supervisor | 6 | 210 | Generado via CLI |
| QUINTANA Felipe Gabriel | 2026-06-19 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| RODRIGUEZ Maximiliano | 2026-06-19 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| RUOCCO MUÑOZ Luis Alfredo | 2026-06-19 | 06-12_Supervisor | 6 | 210 | Generado via CLI |
| SUAREZ Carolina | 2026-06-19 | 18-24_Supervisor | 6 | 210 | Generado via CLI |
| SUÑER Mara Tatiana | 2026-06-19 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| VELEZ Facundo | 2026-06-19 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| VILLEGAS Gaston | 2026-06-19 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| ALCARAZ Xavier | 2026-06-20 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| BARROSO Alan | 2026-06-20 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| BRIZUELA Irma | 2026-06-20 | 18-24_Supervisor | 6 | 210 | Generado via CLI |
| FERNANDEZ Claudia Elizabeth | 2026-06-20 | 00-06_Supervisor | 6 | 210 | Generado via CLI |
| FLORES Jose Nicolas | 2026-06-20 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| FUNEZ Valeria Vanesa | 2026-06-20 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| GUERRIDO Noelia | 2026-06-20 | 00-06_Supervisor | 6 | 210 | Generado via CLI |
| LEDESMA PAZ Micaela | 2026-06-20 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MANSILLA Diego | 2026-06-20 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MIRANDA Luis | 2026-06-20 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| OJEDA Miriam | 2026-06-20 | Administrativo | 6 | 210 | Generado via CLI |
| SANCIO Paola | 2026-06-20 | 06-12_Supervisor | 6 | 210 | Generado via CLI |
| STEIMBRECHER Yolanda | 2026-06-20 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| TORRES Yesica | 2026-06-20 | 12-18_Supervisor | 6 | 210 | Generado via CLI |
| VELEZ Facundo | 2026-06-20 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| VERGARA Mariano | 2026-06-20 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| VERGARA Nazareno | 2026-06-20 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| VILLEGAS Gaston | 2026-06-20 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| ALCARAZ Xavier | 2026-06-21 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| BRIZUELA Irma | 2026-06-21 | 18-24_Supervisor | 6 | 210 | Generado via CLI |
| FERNANDEZ Claudia Elizabeth | 2026-06-21 | 00-06_Supervisor | 6 | 210 | Generado via CLI |
| FLORES Jose Nicolas | 2026-06-21 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| FUNEZ Valeria Vanesa | 2026-06-21 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| GUERRERO Cesar | 2026-06-21 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| GUERRIDO Noelia | 2026-06-21 | 00-06_Supervisor | 6 | 210 | Generado via CLI |
| LEDESMA PAZ Micaela | 2026-06-21 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MESSINA Eduardo | 2026-06-21 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MIRANDA Luis | 2026-06-21 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| MOCDESE Marcelo Leonel | 2026-06-21 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| OJEDA Miriam | 2026-06-21 | Administrativo | 6 | 210 | Generado via CLI |
| SANCIO Paola | 2026-06-21 | 06-12_Supervisor | 6 | 210 | Generado via CLI |
| STEIMBRECHER Yolanda | 2026-06-21 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| TORRES Yesica | 2026-06-21 | 12-18_Supervisor | 6 | 210 | Generado via CLI |
| VELEZ Facundo | 2026-06-21 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| VERGARA Mariano | 2026-06-21 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| VERGARA Nazareno | 2026-06-21 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| ALCARAZ Xavier | 2026-06-22 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| BARROSO Alan | 2026-06-22 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| ESCUDERO Gabriela | 2026-06-22 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FERNANDEZ Celeste Ivana | 2026-06-22 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FERNANDEZ Claudia Elizabeth | 2026-06-22 | 00-06_Supervisor | 6 | 210 | Generado via CLI |
| FERNANDEZ Juan Emir | 2026-06-22 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FLORES Enzo | 2026-06-22 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FLORES Jose Nicolas | 2026-06-22 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| FUNEZ Valeria Vanesa | 2026-06-22 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| GUERRERO Cesar | 2026-06-22 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| GUERRIDO Noelia | 2026-06-22 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| KOPRIVSEK Francisco | 2026-06-22 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| LEDESMA PAZ Micaela | 2026-06-22 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MANSILLA Diego | 2026-06-22 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MESSINA Eduardo | 2026-06-22 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MIRANDA Luis | 2026-06-22 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| MUÑOZ Maria Carolina | 2026-06-22 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| RUOCCO MUÑOZ Luis Alfredo | 2026-06-22 | 06-12_Supervisor | 6 | 210 | Generado via CLI |
| SUAREZ Carolina | 2026-06-22 | 18-24_Supervisor | 6 | 210 | Generado via CLI |
| SUÑER Mara Tatiana | 2026-06-22 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| TORRES Yesica | 2026-06-22 | 12-18_Supervisor | 6 | 210 | Generado via CLI |
| VERGARA Mariano | 2026-06-22 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| VERGARA Nazareno | 2026-06-22 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| VILLEGAS Gaston | 2026-06-22 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| BRIZUELA Irma | 2026-06-23 | 18-24_Supervisor | 6 | 210 | Generado via CLI |
| ESCUDERO Gabriela | 2026-06-23 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FERNANDEZ Celeste Ivana | 2026-06-23 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FERNANDEZ Juan Emir | 2026-06-23 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FLORES Enzo | 2026-06-23 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FLORES Jose Nicolas | 2026-06-23 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| KOPRIVSEK Francisco | 2026-06-23 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| MANSILLA Diego | 2026-06-23 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MESSINA Eduardo | 2026-06-23 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MIRANDA Luis | 2026-06-23 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| MOCDESE Marcelo Leonel | 2026-06-23 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| OLGUIN ALDECO Jennifer Sofia | 2026-06-23 | 00-06_Supervisor | 6 | 210 | Generado via CLI |
| QUINTANA Felipe Gabriel | 2026-06-23 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| RODRIGUEZ Maximiliano | 2026-06-23 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| RUOCCO MUÑOZ Luis Alfredo | 2026-06-23 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| SANCIO Paola | 2026-06-23 | 06-12_Supervisor | 6 | 210 | Generado via CLI |
| STEIMBRECHER Yolanda | 2026-06-23 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| TORRES Yesica | 2026-06-23 | 12-18_Supervisor | 6 | 210 | Generado via CLI |
| VELEZ Facundo | 2026-06-23 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| VERGARA Mariano | 2026-06-23 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| VERGARA Nazareno | 2026-06-23 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| VILLEGAS Gaston | 2026-06-23 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| ALCARAZ Xavier | 2026-06-24 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| BARROSO Alan | 2026-06-24 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| BRIZUELA Irma | 2026-06-24 | 12-18_Supervisor | 6 | 210 | Generado via CLI |
| ESCUDERO Gabriela | 2026-06-24 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FERNANDEZ Celeste Ivana | 2026-06-24 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FERNANDEZ Claudia Elizabeth | 2026-06-24 | 00-06_Supervisor | 6 | 210 | Generado via CLI |
| FLORES Enzo | 2026-06-24 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FLORES Jose Nicolas | 2026-06-24 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| FUNEZ Valeria Vanesa | 2026-06-24 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| GUERRERO Cesar | 2026-06-24 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| GUERRIDO Noelia | 2026-06-24 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| KOPRIVSEK Francisco | 2026-06-24 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| LEDESMA PAZ Micaela | 2026-06-24 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MANSILLA Diego | 2026-06-24 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| OJEDA Miriam | 2026-06-24 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| OLGUIN ALDECO Jennifer Sofia | 2026-06-24 | 00-06_Supervisor | 6 | 210 | Generado via CLI |
| QUINTANA Felipe Gabriel | 2026-06-24 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| RODRIGUEZ Maximiliano | 2026-06-24 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| RUOCCO MUÑOZ Luis Alfredo | 2026-06-24 | 06-12_Supervisor | 6 | 210 | Generado via CLI |
| STEIMBRECHER Yolanda | 2026-06-24 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| SUAREZ Carolina | 2026-06-24 | 18-24_Supervisor | 6 | 210 | Generado via CLI |
| SUÑER Mara Tatiana | 2026-06-24 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| VELEZ Facundo | 2026-06-24 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| VERGARA Mariano | 2026-06-24 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| VILLEGAS Gaston | 2026-06-24 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| ALCARAZ Xavier | 2026-06-25 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| BARROSO Alan | 2026-06-25 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| BRIZUELA Irma | 2026-06-25 | 12-18_Supervisor | 6 | 210 | Generado via CLI |
| ESCUDERO Gabriela | 2026-06-25 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FERNANDEZ Celeste Ivana | 2026-06-25 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FERNANDEZ Claudia Elizabeth | 2026-06-25 | 00-06_Supervisor | 6 | 210 | Generado via CLI |
| FERNANDEZ Juan Emir | 2026-06-25 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FLORES Enzo | 2026-06-25 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FUNEZ Valeria Vanesa | 2026-06-25 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| GUERRERO Cesar | 2026-06-25 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| GUERRIDO Noelia | 2026-06-25 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| KOPRIVSEK Francisco | 2026-06-25 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| LEDESMA PAZ Micaela | 2026-06-25 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MANSILLA Diego | 2026-06-25 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MOCDESE Marcelo Leonel | 2026-06-25 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| MUÑOZ Maria Carolina | 2026-06-25 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| OJEDA Miriam | 2026-06-25 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| OLGUIN ALDECO Jennifer Sofia | 2026-06-25 | 00-06_Supervisor | 6 | 210 | Generado via CLI |
| QUINTANA Felipe Gabriel | 2026-06-25 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| RODRIGUEZ Maximiliano | 2026-06-25 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| SANCIO Paola | 2026-06-25 | 06-12_Supervisor | 6 | 210 | Generado via CLI |
| SUAREZ Carolina | 2026-06-25 | 18-24_Supervisor | 6 | 210 | Generado via CLI |
| SUÑER Mara Tatiana | 2026-06-25 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| VELEZ Facundo | 2026-06-25 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| VILLEGAS Gaston | 2026-06-25 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| ALCARAZ Xavier | 2026-06-26 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| BARROSO Alan | 2026-06-26 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| ESCUDERO Gabriela | 2026-06-26 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FERNANDEZ Celeste Ivana | 2026-06-26 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FERNANDEZ Claudia Elizabeth | 2026-06-26 | 00-06_Supervisor | 6 | 210 | Generado via CLI |
| FERNANDEZ Juan Emir | 2026-06-26 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FLORES Enzo | 2026-06-26 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FLORES Jose Nicolas | 2026-06-26 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| GUERRERO Cesar | 2026-06-26 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| GUERRIDO Noelia | 2026-06-26 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| KOPRIVSEK Francisco | 2026-06-26 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| MANSILLA Diego | 2026-06-26 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MESSINA Eduardo | 2026-06-26 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MIRANDA Luis | 2026-06-26 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| MUÑOZ Maria Carolina | 2026-06-26 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| RUOCCO MUÑOZ Luis Alfredo | 2026-06-26 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| SANCIO Paola | 2026-06-26 | 06-12_Supervisor | 6 | 210 | Generado via CLI |
| STEIMBRECHER Yolanda | 2026-06-26 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| SUAREZ Carolina | 2026-06-26 | 18-24_Supervisor | 6 | 210 | Generado via CLI |
| TORRES Yesica | 2026-06-26 | 12-18_Supervisor | 6 | 210 | Generado via CLI |
| VELEZ Facundo | 2026-06-26 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| VERGARA Mariano | 2026-06-26 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| VERGARA Nazareno | 2026-06-26 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| VILLEGAS Gaston | 2026-06-26 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| BRIZUELA Irma | 2026-06-27 | 18-24_Supervisor | 6 | 210 | Generado via CLI |
| FUNEZ Valeria Vanesa | 2026-06-27 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| GUERRERO Cesar | 2026-06-27 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| LEDESMA PAZ Micaela | 2026-06-27 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MESSINA Eduardo | 2026-06-27 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MIRANDA Luis | 2026-06-27 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| MOCDESE Marcelo Leonel | 2026-06-27 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| MUÑOZ Maria Carolina | 2026-06-27 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| OJEDA Miriam | 2026-06-27 | Administrativo | 6 | 210 | Generado via CLI |
| OLGUIN ALDECO Jennifer Sofia | 2026-06-27 | 00-06_Supervisor | 6 | 210 | Generado via CLI |
| QUINTANA Felipe Gabriel | 2026-06-27 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| RODRIGUEZ Maximiliano | 2026-06-27 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| SANCIO Paola | 2026-06-27 | 06-12_Supervisor | 6 | 210 | Generado via CLI |
| STEIMBRECHER Yolanda | 2026-06-27 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| SUÑER Mara Tatiana | 2026-06-27 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| TORRES Yesica | 2026-06-27 | 12-18_Supervisor | 6 | 210 | Generado via CLI |
| VERGARA Nazareno | 2026-06-27 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| BARROSO Alan | 2026-06-28 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| BRIZUELA Irma | 2026-06-28 | 18-24_Supervisor | 6 | 210 | Generado via CLI |
| FUNEZ Valeria Vanesa | 2026-06-28 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| LEDESMA PAZ Micaela | 2026-06-28 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MESSINA Eduardo | 2026-06-28 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MIRANDA Luis | 2026-06-28 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| MOCDESE Marcelo Leonel | 2026-06-28 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| MUÑOZ Maria Carolina | 2026-06-28 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| OJEDA Miriam | 2026-06-28 | Administrativo | 6 | 210 | Generado via CLI |
| OLGUIN ALDECO Jennifer Sofia | 2026-06-28 | 00-06_Supervisor | 6 | 210 | Generado via CLI |
| QUINTANA Felipe Gabriel | 2026-06-28 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| RODRIGUEZ Maximiliano | 2026-06-28 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| SANCIO Paola | 2026-06-28 | 06-12_Supervisor | 6 | 210 | Generado via CLI |
| STEIMBRECHER Yolanda | 2026-06-28 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| SUÑER Mara Tatiana | 2026-06-28 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| TORRES Yesica | 2026-06-28 | 12-18_Supervisor | 6 | 210 | Generado via CLI |
| VERGARA Nazareno | 2026-06-28 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| ALCARAZ Xavier | 2026-06-29 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| BARROSO Alan | 2026-06-29 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| ESCUDERO Gabriela | 2026-06-29 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FERNANDEZ Celeste Ivana | 2026-06-29 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FERNANDEZ Claudia Elizabeth | 2026-06-29 | 00-06_Supervisor | 6 | 210 | Generado via CLI |
| FERNANDEZ Juan Emir | 2026-06-29 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FLORES Enzo | 2026-06-29 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FLORES Jose Nicolas | 2026-06-29 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| FUNEZ Valeria Vanesa | 2026-06-29 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| GUERRERO Cesar | 2026-06-29 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| GUERRIDO Noelia | 2026-06-29 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| KOPRIVSEK Francisco | 2026-06-29 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| LEDESMA PAZ Micaela | 2026-06-29 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MANSILLA Diego | 2026-06-29 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MESSINA Eduardo | 2026-06-29 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MIRANDA Luis | 2026-06-29 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| MOCDESE Marcelo Leonel | 2026-06-29 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| OJEDA Miriam | 2026-06-29 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| QUINTANA Felipe Gabriel | 2026-06-29 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| RUOCCO MUÑOZ Luis Alfredo | 2026-06-29 | 06-12_Supervisor | 6 | 210 | Generado via CLI |
| SUAREZ Carolina | 2026-06-29 | 18-24_Supervisor | 6 | 210 | Generado via CLI |
| SUÑER Mara Tatiana | 2026-06-29 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| TORRES Yesica | 2026-06-29 | 12-18_Supervisor | 6 | 210 | Generado via CLI |
| VELEZ Facundo | 2026-06-29 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| VERGARA Nazareno | 2026-06-29 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| VILLEGAS Gaston | 2026-06-29 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| ALCARAZ Xavier | 2026-06-30 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| BARROSO Alan | 2026-06-30 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| BRIZUELA Irma | 2026-06-30 | 12-18_Supervisor | 6 | 210 | Generado via CLI |
| ESCUDERO Gabriela | 2026-06-30 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FERNANDEZ Celeste Ivana | 2026-06-30 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FERNANDEZ Claudia Elizabeth | 2026-06-30 | 00-06_Supervisor | 6 | 210 | Generado via CLI |
| FLORES Enzo | 2026-06-30 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| FLORES Jose Nicolas | 2026-06-30 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| GUERRERO Cesar | 2026-06-30 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| GUERRIDO Noelia | 2026-06-30 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| KOPRIVSEK Francisco | 2026-06-30 | 00-06_Monitorista | 6 | 210 | Generado via CLI |
| LEDESMA PAZ Micaela | 2026-06-30 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| MOCDESE Marcelo Leonel | 2026-06-30 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| MUÑOZ Maria Carolina | 2026-06-30 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| OJEDA Miriam | 2026-06-30 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| OLGUIN ALDECO Jennifer Sofia | 2026-06-30 | 00-06_Supervisor | 6 | 210 | Generado via CLI |
| QUINTANA Felipe Gabriel | 2026-06-30 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| RODRIGUEZ Maximiliano | 2026-06-30 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| RUOCCO MUÑOZ Luis Alfredo | 2026-06-30 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| SANCIO Paola | 2026-06-30 | 06-12_Supervisor | 6 | 210 | Generado via CLI |
| STEIMBRECHER Yolanda | 2026-06-30 | 06-12_Monitorista | 6 | 210 | Generado via CLI |
| SUAREZ Carolina | 2026-06-30 | 18-24_Supervisor | 6 | 210 | Generado via CLI |
| SUÑER Mara Tatiana | 2026-06-30 | 12-18_Monitorista | 6 | 210 | Generado via CLI |
| VELEZ Facundo | 2026-06-30 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| VERGARA Mariano | 2026-06-30 | 18-24_Monitorista | 6 | 210 | Generado via CLI |
| VILLEGAS Gaston | 2026-06-30 | 12-18_Monitorista | 6 | 210 | Generado via CLI |

## 4. Demanda y Oferta de Turnos

### Demanda Base (Vacantes Requeridas)

| Puesto | Tipo Día | Hora Inicio | Hora Fin | Mínimo | Máximo | Días Habilitados |
| --- | --- | --- | --- | --- | --- | --- |
| Administrativo | Semana | 06:00 | 12:00 | 0 | 1 | - |
| Monitorista | Finde_Feriado | 00:00 | 06:00 | 2 | 6 | - |
| Monitorista | Finde_Feriado | 06:00 | 12:00 | 2 | 7 | - |
| Monitorista | Finde_Feriado | 12:00 | 18:00 | 2 | 7 | - |
| Monitorista | Finde_Feriado | 18:00 | 23:59 | 2 | 7 | - |
| Monitorista | Semana | 00:00 | 06:00 | 2 | 6 | - |
| Monitorista | Semana | 06:00 | 12:00 | 2 | 7 | - |
| Monitorista | Semana | 12:00 | 18:00 | 2 | 7 | - |
| Monitorista | Semana | 18:00 | 23:59 | 2 | 7 | - |
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


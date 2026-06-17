# Reporte de Auditoría de Configuración

- **Servicio:** Kinesiologia Critica (ID: 1)
- **Organización:** Organización Principal
- **Período a Auditar:** 2026-06
- **Fecha Generación:** 2026-05-30 21:04:11

## 1. Resumen Servicio & Reglas Activas

### Reglas de Negocio Aplicables

| Código Regla | Tipo | Origen | Activo | Descripción | Parámetros |
| --- | --- | --- | --- | --- | --- |
| BONUS_COMBO_FINDE | SOFT | Servicio | Sí | Premio por trabajar Sabado y Domingo juntos | `{"peso": 15}` |
| BONUS_PREFERENCIAS | SOFT | Servicio | Sí | Premio por cumplir preferencias individuales | `{"peso": 300}` |
| BONUS_SEG_PUNTOS | SOFT | Servicio | Sí | Premio por cada día de seguimiento individual | `{"peso": 5}` |
| BONUS_SEG_TOTAL | SOFT | Servicio | Sí | Premio por completar semanas de seguimiento | `{"peso": 150}` |
| LIMITES_SOFT_RULES | SOFT | Servicio | Sí | Límites base para dimensionar el solver (Semanas_Base, Min_Horas, Max_Horas_Limite, etc) | `{"SEMANAS_BASE": 4, "MIN_HORAS_BASE": 120, "MAX_HORAS_LIMITE_BASE": 144, "MAX_ANUAL_LIMITE": 5000, "MAX_SEG_LIMITE_BASE": 50, "MAX_FINDES_LIMITE_BASE": 8}` |
| PESO_BRECHA_ANUAL | SOFT | Servicio | Sí | Peso de penalización por diferencia de horas anuales | `{"peso": 100}` |
| PESO_BRECHA_MENSUAL | SOFT | Servicio | Sí | Peso de penalización por diferencia de horas en el mes | `{"peso": 50}` |
| PESO_BRECHA_SEG | SOFT | Servicio | Sí | Peso de penalización por diferencia de seguimientos | `{"peso": 100}` |
| PESO_EQUIDAD_FL3 | SOFT | Servicio | Sí | Peso de penalización por desigualdad en findes largos de 3 días | `{"peso": 500}` |
| PESO_EQUIDAD_FL4 | SOFT | Servicio | Sí | Peso de penalización por desigualdad en findes largos de 4 días | `{"peso": 500}` |
| PESO_INCONSISTENCIA | SOFT | Servicio | Sí | Penalización por cambiar de tipo de turno (ej: UTI a UCO) en la semana | `{"peso": 100}` |
| PESO_MIX_HORARIO | SOFT | Servicio | Sí | Penalización por mezclar mañana y tarde en la misma semana | `{"peso": 500}` |
| DESCANSO_ENTRE_TURNOS | HARD | Servicio | Sí | Horas mínimas de descanso entre el fin de un turno y el comienzo del siguiente. JSON: {"horas": 12} | `{"por_turno": {"Dia_UTI": 24, "Dia_UCO": 24, "Noche": 36, "Mañana_UTI": 24, "Mañana_UCO": 24, "Mañana_especial": 0, "Tarde_UTI": 12, "Tarde_UCO": 12, "Tarde_especial": 12}}` |
| MAX_HORAS_MES_CALENDARIO | HARD | Servicio | Sí | Límite máximo estricto de horas a trabajar por mes calendario. JSON: {"max_horas": 144} | `{"max_horas": 144}` |
| MAX_HORAS_SEMANA | HARD | Servicio | Sí | Límite máximo de horas por semana | `{"limite": 42}` |
| MAX_TURNOS | HARD | Servicio | Sí | Limite maximo de un grupo de turnos por semana o mes. JSON: [{"turnos": ["Dia_UTI", "Noche"], "max_por_mes": 1}] | `[{"turno": "Noche", "max_por_semana": 2}]` |
| MIN_HORAS_MES_CALENDARIO | HARD | Servicio | Sí | Mínimo de horas trabajadas más licencias por mes calendario. | `{"min_horas": 120}` |

### Ajustes Temporales de Servicio

*(Sin ajustes temporales del servicio en este período)*

## 2. Personal y Perfiles

| Nombre | Categoría | Rol | Régimen | Horas Reg. | Cumpleaños | M/P | Puestos |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Lic. Camargo N. | GENERAL | Rotativo | - | - | - | - | UTI, UCO, General |
| Lic. Coniglio | GENERAL | Rotativo | - | - | - | - | UTI, UCO, General |
| Lic. Espinosa | GENERAL | Rotativo | - | - | - | - | UTI, UCO, General |
| Lic. Flores | GENERAL | Rotativo | - | - | - | - | UTI, UCO, General |
| Lic. Franco | UTI | Coordinador | - | - | - | - | UTI |
| Lic. Garcia | UTI | Jefe | - | - | - | - | UTI |
| Lic. Giaccoppo | GENERAL | Rotativo | - | - | - | - | UTI, UCO, General |
| Lic. Guardia | GENERAL | Rotativo | - | - | - | - | UTI, UCO, General |
| Lic. Guzman | GENERAL | Rotativo | - | - | - | - | UTI, UCO, General |
| Lic. Juarez | GENERAL | Nocturno | - | - | - | - | UTI, UCO, General |
| Lic. Leonforte | GENERAL | Rotativo | - | - | - | - | UTI, UCO, General |
| Lic. Marino | GENERAL | Rotativo | - | - | - | - | UTI, UCO, General |
| Lic. Mesa | GENERAL | Rotativo | - | - | - | - | UTI, UCO, General |
| Lic. Moyano | UTI | Coordinador | - | - | - | - | UTI |
| Lic. Sosa | GENERAL | Rotativo | MNT | - | - | - | UTI, UCO, General |
| Lic. Syriani | GENERAL | Rotativo | - | - | - | - | UTI, UCO, General |
| Lic. Toledo | UCO | Coordinador | - | - | - | - | UCO |
| Lic. Vander | GENERAL | Rotativo | - | - | - | - | UTI, UCO, General |
| Lic. Vivas | GENERAL | Rotativo | - | - | - | - | UTI, UCO, General |
| Lic. Welch | GENERAL | Rotativo | - | - | - | - | UTI, UCO, General |

### Reglas Individuales de Personal

| Profesional | Código Regla | Tipo | Descripción | Parámetros |
| --- | --- | --- | --- | --- |
| Lic. Camargo N. | ASIGNACION_FIJA | HARD | Fuerza a la persona a un turno específico en días específicos | `[{"Dia": "Lunes", "Turno": "Tarde_especial", "Tipo": "Especial", "Horas": 6}, {"Dia": "Miercoles", "Turno": "Tarde", "Tipo": "Asistencial", "Horas": 6}, {"Dia": "Viernes", "Turno": "Tarde", "Tipo": "Asistencial", "Horas": 6}]` |
| Lic. Camargo N. | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `[{"turnos": ["Mañana_UTI", "Mañana_UCO"], "dias": [0, 1, 2, 3, 4, 5, 6]}]` |
| Lic. Camargo N. | TURNOS_PREFERENCIALES | SOFT | Preferencias individuales de turnos y días | `[{"Dia": "Domingo", "Turno": "Dia", "Tipo": "Asistencial", "Horas": 12}]` |
| Lic. Coniglio | ASIGNACION_FIJA | HARD | Fuerza a la persona a un turno específico en días específicos | `[{"Dia": "Miercoles", "Turno": "Mañana_especial", "Tipo": "Especial", "Horas": 6}, {"Dia": "Miercoles", "Turno": "Tarde_especial", "Tipo": "Especial", "Horas": 6}]` |
| Lic. Espinosa | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `[{"turnos": ["Mañana_especial", "Tarde_especial"], "dias": [0, 1, 2, 3, 4, 5, 6]}]` |
| Lic. Flores | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `[{"turnos": ["Mañana_especial", "Tarde_especial"], "dias": [0, 1, 2, 3, 4, 5, 6]}]` |
| Lic. Franco | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `[{"turnos": ["Mañana_UCO", "Tarde_UCO", "Dia_UCO", "Mañana_especial", "Tarde_especial", "Noche"], "dias": [0, 1, 2, 3, 4, 5, 6]}]` |
| Lic. Garcia | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `[{"turnos": ["Mañana_UCO", "Tarde_UCO", "Dia_UCO", "Mañana_especial", "Tarde_especial"], "dias": [0, 1, 2, 3, 4, 5, 6]}]` |
| Lic. Giaccoppo | ASIGNACION_FIJA | HARD | Fuerza a la persona a un turno específico en días específicos | `[{"Dia": "Lunes", "Turno": "Tarde_especial", "Tipo": "Especial", "Horas": 6}]` |
| Lic. Guardia | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `[{"turnos": ["Mañana_especial", "Tarde_especial"], "dias": [0, 1, 2, 3, 4, 5, 6]}]` |
| Lic. Guzman | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `[{"turnos": ["Mañana_especial", "Tarde_especial"], "dias": [0, 1, 2, 3, 4, 5, 6]}]` |
| Lic. Juarez | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `[{"turnos": ["Mañana_especial", "Tarde_especial", "Mañana_UTI", "Mañana_UCO", "Tarde_UTI", "Tarde_UCO"], "dias": [0, 1, 2, 3, 4, 5, 6]}]` |
| Lic. Leonforte | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `[{"turnos": ["Mañana_especial", "Tarde_especial"], "dias": [0, 1, 2, 3, 4, 5, 6]}]` |
| Lic. Marino | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `[{"turnos": ["Mañana_especial", "Tarde_especial"], "dias": [0, 1, 2, 3, 4, 5, 6]}]` |
| Lic. Mesa | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `[{"turnos": ["Mañana_especial", "Tarde_especial"], "dias": [0, 1, 2, 3, 4, 5, 6]}]` |
| Lic. Moyano | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `[{"turnos": ["Mañana_UCO", "Tarde_UCO", "Dia_UCO", "Mañana_especial", "Tarde_especial", "Noche"], "dias": [0, 1, 2, 3, 4, 5, 6]}]` |
| Lic. Sosa | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `[{"turnos": ["Mañana_especial", "Tarde_especial"], "dias": [0, 1, 2, 3, 4, 5, 6]}]` |
| Lic. Syriani | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `[{"turnos": ["Mañana_especial", "Tarde_especial"], "dias": [0, 1, 2, 3, 4, 5, 6]}]` |
| Lic. Toledo | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `[{"turnos": ["Mañana_UTI", "Tarde_UTI", "Noche", "Dia_UTI", "Mañana_especial", "Tarde_especial"], "dias": [0, 1, 2, 3, 4, 5, 6]}]` |
| Lic. Vander | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `[{"turnos": ["Mañana_especial", "Tarde_especial"], "dias": [0, 1, 2, 3, 4, 5, 6]}]` |
| Lic. Vivas | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `[{"turnos": ["Mañana_especial", "Tarde_especial"], "dias": [0, 1, 2, 3, 4, 5, 6]}]` |
| Lic. Welch | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `[{"turnos": ["Mañana_especial", "Tarde_especial"], "dias": [0, 1, 2, 3, 4, 5, 6]}]` |

## 3. Ajustes Personales & Licencias

### Ajustes Temporales de Reglas Personales

*(Sin ajustes temporales de reglas de personal para este período)*

### Licencias Cargadas

*(Sin licencias activas en este período)*

### Asignaciones Fijas / Guardias Aprobadas

*(Sin guardias aprobadas / asignaciones previas para este período)*

## 4. Demanda y Oferta de Turnos

### Demanda Base (Vacantes Requeridas)

| Puesto | Tipo Día | Hora Inicio | Hora Fin | Mínimo | Máximo | Días Habilitados |
| --- | --- | --- | --- | --- | --- | --- |
| General | Finde_Feriado | 20:00 | 08:00 | 2 | 2 | - |
| General | Semana | 20:00 | 08:00 | 2 | 2 | - |
| UCO | Finde_Feriado | 08:00 | 20:00 | 1 | 1 | - |
| UCO | Semana | 08:00 | 14:00 | 2 | 2 | - |
| UCO | Semana | 14:00 | 20:00 | 1 | 1 | - |
| UTI | Finde_Feriado | 08:00 | 20:00 | 2 | 2 | - |
| UTI | Semana | 08:00 | 14:00 | 5 | 5 | - |
| UTI | Semana | 14:00 | 20:00 | 4 | 4 | - |

### Ajustes Temporales de Demanda

*(Sin ajustes de demanda activos en este período)*

### Oferta de Turnos Configurada

| Turno | Hora Inicio | Horas | Días Semana | Puesto | Orden |
| --- | --- | --- | --- | --- | --- |
| Mañana_UTI | 08:00 | 6 | 0,1,2,3,4 | UTI | 1 |
| Mañana_UCO | 08:00 | 6 | 0,1,2,3,4 | UCO | 2 |
| Mañana_especial | 08:00 | 6 | 0,1,2,3,4,5,6 | Especial | 3 |
| Dia_UTI | 08:00 | 12 | 0,1,2,3,4,5,6 | UTI | 4 |
| Dia_UCO | 08:00 | 12 | 0,1,2,3,4,5,6 | UCO | 5 |
| Tarde_UTI | 14:00 | 6 | 0,1,2,3,4 | UTI | 6 |
| Tarde_UCO | 14:00 | 6 | 0,1,2,3,4 | UCO | 7 |
| Tarde_especial | 14:00 | 6 | 0,1,2,3,4,5,6 | Especial | 8 |
| Noche | 20:00 | 12 | 0,1,2,3,4,5,6 | General | 9 |

### Ajustes Temporales de Turnos / Vacantes

*(Sin ajustes temporales de turnos activos en este período)*


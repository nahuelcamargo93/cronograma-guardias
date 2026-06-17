# Reporte de Auditoría de Configuración

- **Servicio:** Area Medica UTI (ID: 3)
- **Organización:** Organización Principal
- **Período a Auditar:** 2026-07
- **Fecha Generación:** 2026-06-17 14:28:52

## 1. Resumen Servicio & Reglas Activas

### Reglas de Negocio Aplicables

| Código Regla | Tipo | Origen | Activo | Descripción | Parámetros |
| --- | --- | --- | --- | --- | --- |
| FRANCOS_FIN_MES | SOFT | Servicio | Sí | Asegura la cantidad de francos en la última semana del mes si esta es incompleta (tiene 4 o 5 días). | `{"por_dias": {"5": 2, "4": 1}, "peso": 5000}` |
| PENALIZACION_PUESTO_NO_PREFERIDO | SOFT | Servicio | Sí | Penaliza cuando una persona es asignada a un turno de un puesto que NO es su puesto primario (segun personal_puestos.es_primario). Peso default: 500. JSON: {"peso": 500} | `{"peso": 20000, "priorizar_categoria": "desc"}` |
| PENALIZACION_TURNO | SOFT | Servicio | Sí | Penaliza la asignación de un turno específico | `[{"turno": "D_Planta", "peso": 4000}, {"turno": "N_Planta", "peso": 5000}, {"turno": "D_Residente", "peso": 4000}, {"turno": "N_Residente", "peso": 100000}]` |
| PESO_BRECHA_DIARIA_PERSONAL | SOFT | Servicio | Sí | Peso de penalización por diferencia de personal asignado por día y puesto/turno | `{"peso_brecha": 5000, "peso_cobertura": 10}` |
| CREDITO_HORARIO_LICENCIA | HARD | Servicio | Sí | Define cuántas horas se acreditan por semana de licencia para el cálculo de topes. | `{"horas_por_semana": 36}` |
| CUMPLEANOS_LIBRE | HARD | Servicio | Sí | El profesional tiene franco obligatorio el día de su cumpleaños | `{}` |
| DESCANSO_ENTRE_TURNOS | HARD | Servicio | Sí | Horas mínimas de descanso entre el fin de un turno y el comienzo del siguiente. JSON: {"horas": 12} | `{"por_turno": {"G_Planta": 48, "D_Planta": 12, "N_Planta": 36, "G_Residente": 48, "D_Residente": 12, "N_Residente": 36}}` |
| DIA_MADRE_PADRE_LIBRE | HARD | Servicio | Sí | El profesional tiene franco obligatorio el día de la madre o del padre según corresponda | `{}` |
| EXACTO_FINDE_Y_DIA | HARD | Servicio | Sí | Unified rule | `{"dia_semana": "Viernes", "findes_por_disponibilidad": {"5": 2, "4": 2, "3": 2, "2": 1, "1": 1, "0": 0}, "dias_por_disponibilidad": {"5": 2, "4": 1, "3": 0, "2": 1, "1": 0, "0": 0}, "modo": "SOFT", "peso_soft": 1000000}` |
| FIN_LICENCIA | HARD | Servicio | Sí | Obliga a trabajar el día inmediatamente posterior al fin de una licencia (LAR/LPP). | `{}` |
| MAX_DIAS_CONTINUOS | HARD | Servicio | Sí | Límite máximo de días consecutivos/seguidos de trabajo | `{"max_dias": 2}` |
| MAX_HORAS_MES_CALENDARIO | HARD | Servicio | Sí | Límite máximo estricto de horas a trabajar por mes calendario. JSON: {"max_horas": 144} | `{"max_horas": 198}` |
| MAX_HORAS_SEMANA | HARD | Servicio | Sí | Límite máximo de horas por semana | `{"limite": 60}` |
| MAX_NOCHE_VS_DIA | HARD | Servicio | Sí | El total de personal en turnos de noche no puede superar al total en turnos de día. | `{}` |
| MIN_HORAS_MES_CALENDARIO | HARD | Servicio | Sí | Mínimo de horas trabajadas más licencias por mes calendario. | `{"min_horas": 185, "modo": "HARD"}` |
| PERSONAL_DISOCIADO | HARD | Servicio | Sí | Parejas de personal que NO deben coincidir en la misma franja horaria. | `{"parejas": [["Aguilera, Graciela", "Garcia Rodriguez, Maria Eugenia"]]}` |
| PERSONAL_EXTRA_FUERA_MINIMO | HARD | Servicio | Sí | El personal indicado no cuenta para el cupo minimo pero si ocupa lugar en el maximo. | `{"nombres": ["Baracat, Denisse", "Moya, Pedro", "Mora, Sergio Enrique"]}` |
| UN_TURNO_POR_DIA | HARD | Servicio | Sí | Restriccion universal: una persona no puede tener mas de un turno asignado el mismo dia. No tiene parametros configurables. | `{}` |

### Ajustes Temporales de Servicio

| Código Regla | Inicio | Fin | Acción | Activo | Parámetros |
| --- | --- | --- | --- | --- | --- |
| DESCANSO_ENTRE_TURNOS | 2026-07-08 | 2026-07-12 | SOBRESCRIBIR | Sí | `{"por_turno": {"G_Planta": 24, "D_Planta": 12, "N_Planta": 24, "G_Residente": 24, "D_Residente": 12, "N_Residente": 24}}` |

## 2. Personal y Perfiles

| Nombre | Categoría | Rol | Régimen | Horas Reg. | Cumpleaños | M/P | Puestos |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Aguilera, Graciela | - | Planta | - | - | - | - | Planta |
| Arce, Carolina | 1 | Residente | - | - | - | - | Planta, Residente |
| Arias, Guillermina | - | Planta | - | - | 1990-06-01 | - | Planta |
| Baracat, Denisse | - | Planta | - | - | - | - | Planta |
| Barloa, Matías Damián | - | Planta | - | - | - | - | Planta |
| Biscarra, Joaquín Martin | 2 | Residente | - | - | - | - | Planta, Residente |
| Diaz Villafañe Morales, Abigail | - | Planta | - | - | - | - | Planta |
| Garcia Rodriguez, Maria Eugenia | - | Planta | - | - | - | - | Planta |
| Godoy, Maria | - | Planta | - | - | - | - | Planta |
| Matricadi, Wendy Ailen | 4 | Residente | - | - | - | - | Planta, Residente |
| Mora, Sergio Enrique | - | Planta | - | - | - | Padre | Planta |
| Motta, Mayra Belen | - | Planta | - | - | - | - | Planta |
| Moya, Pedro | - | Planta | - | - | - | Padre | Planta |
| Murillo, Santiago | - | Planta | - | - | - | Padre | Planta |
| Navarro Suarez, Gabriela Belén | - | Planta | - | - | - | - | Planta |
| Nesteruk, María Silvia | - | Planta | - | - | - | - | Planta |
| Noriega, Claudio Martín | - | Planta | - | - | - | Padre | Planta |
| Núñez, Florencia Natalia | 4 | Residente | - | - | - | - | Planta, Residente |
| Pacheco, Celeste | 1 | Residente | - | - | - | - | Planta, Residente |
| Palermo, Agustín | 4 | Residente | - | - | - | Padre | Planta, Residente |
| Pregot, Analia Mariana | - | Planta | - | - | - | - | Planta |
| Quintero, Anabela Belen | - | Planta | - | - | - | - | Planta |
| Quiroga Sassu, Maria Macarena | - | Planta | - | - | - | - | Planta |
| Silva, Martín Enrique | - | Planta | - | - | - | Padre | Planta |
| Sánchez Reinoso, Ana Belén | - | Planta | - | - | - | - | Planta |
| Villegas Oliva, Maria Belén | 3 | Residente | - | - | - | - | Planta, Residente |
| Zeballos, Valeria Alejandra | - | Planta | - | - | - | - | Planta |

### Reglas Individuales de Personal

| Profesional | Código Regla | Tipo | Descripción | Parámetros |
| --- | --- | --- | --- | --- |
| Aguilera, Graciela | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `[{"turnos": ["G_Planta"], "dias": [0, 1, 2, 3, 4, 5, 6]}]` |
| Aguilera, Graciela | MAX_HORAS_MES_CALENDARIO | HARD | Límite máximo estricto de horas a trabajar por mes calendario. JSON: {"max_horas": 144} | `{"max_horas": 150}` |
| Aguilera, Graciela | MAX_TURNOS | HARD | Limite maximo de un grupo de turnos por semana o mes. JSON: [{"turnos": ["Dia_UTI", "Noche"], "max_por_mes": 1}] | `[{"turno": "N_Planta", "max_por_semana": 1}]` |
| Aguilera, Graciela | MIN_HORAS_MES_CALENDARIO | HARD | Mínimo de horas trabajadas más licencias por mes calendario. | `{"min_horas": 133}` |
| Aguilera, Graciela | PENALIZACION_TURNO | SOFT | Penaliza la asignación de un turno específico | `[{"turno": "N_Planta", "peso": 40000, "solo_semana": true}, {"turno": "N_Planta", "peso": 16000, "solo_finde": true}]` |
| Arce, Carolina | MAX_TURNOS | HARD | Limite maximo de un grupo de turnos por semana o mes. JSON: [{"turnos": ["Dia_UTI", "Noche"], "max_por_mes": 1}] | `[{"turnos": ["D_Planta", "N_Planta"], "max_por_mes": 1}]` |
| Arias, Guillermina | MAX_TURNOS | HARD | Limite maximo de un grupo de turnos por semana o mes. JSON: [{"turnos": ["Dia_UTI", "Noche"], "max_por_mes": 1}] | `[{"turnos": ["D_Planta", "N_Planta"], "max_por_mes": 1}]` |
| Baracat, Denisse | MAX_TURNOS | HARD | Limite maximo de un grupo de turnos por semana o mes. JSON: [{"turnos": ["Dia_UTI", "Noche"], "max_por_mes": 1}] | `[{"turnos": ["D_Planta", "N_Planta"], "max_por_mes": 1}]` |
| Barloa, Matías Damián | EXACTO_FINDE_Y_DIA | HARD | Unified rule | `{"suspendida": true}` |
| Barloa, Matías Damián | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `[{"turnos": ["G_Planta"], "dias": [0, 1, 2, 3, 4, 5, 6]}]` |
| Barloa, Matías Damián | MAX_HORAS_MES_CALENDARIO | HARD | Límite máximo estricto de horas a trabajar por mes calendario. JSON: {"max_horas": 144} | `{"max_horas": 24}` |
| Barloa, Matías Damián | MIN_HORAS_MES_CALENDARIO | HARD | Mínimo de horas trabajadas más licencias por mes calendario. | `{"min_horas": 0}` |
| Barloa, Matías Damián | SOLO_ASIGNACIONES_FIJAS | HARD | El profesional solo realiza guardias asignadas mediante ASIGNACION_FIJA y no se le asignan turnos libres. | `{}` |
| Biscarra, Joaquín Martin | MAX_TURNOS | HARD | Limite maximo de un grupo de turnos por semana o mes. JSON: [{"turnos": ["Dia_UTI", "Noche"], "max_por_mes": 1}] | `[{"turnos": ["D_Planta", "N_Planta"], "max_por_mes": 1}]` |
| Diaz Villafañe Morales, Abigail | MAX_TURNOS | HARD | Limite maximo de un grupo de turnos por semana o mes. JSON: [{"turnos": ["Dia_UTI", "Noche"], "max_por_mes": 1}] | `[{"turnos": ["D_Planta", "N_Planta"], "max_por_mes": 1}]` |
| Garcia Rodriguez, Maria Eugenia | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `[{"turnos": ["G_Planta"], "dias": [0, 1, 2, 3, 4, 5, 6]}]` |
| Garcia Rodriguez, Maria Eugenia | MAX_HORAS_MES_CALENDARIO | HARD | Límite máximo estricto de horas a trabajar por mes calendario. JSON: {"max_horas": 144} | `{"max_horas": 150}` |
| Garcia Rodriguez, Maria Eugenia | MAX_TURNOS | HARD | Limite maximo de un grupo de turnos por semana o mes. JSON: [{"turnos": ["Dia_UTI", "Noche"], "max_por_mes": 1}] | `[{"turno": "N_Planta", "max_por_semana": 1}]` |
| Garcia Rodriguez, Maria Eugenia | MIN_HORAS_MES_CALENDARIO | HARD | Mínimo de horas trabajadas más licencias por mes calendario. | `{"min_horas": 133}` |
| Garcia Rodriguez, Maria Eugenia | PENALIZACION_TURNO | SOFT | Penaliza la asignación de un turno específico | `[{"turno": "N_Planta", "peso": 40000, "solo_semana": true}, {"turno": "N_Planta", "peso": 40000, "solo_finde": true}]` |
| Godoy, Maria | EXACTO_FINDE_Y_DIA | HARD | Unified rule | `{"suspendida": true}` |
| Godoy, Maria | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `[{"turnos": ["G_Planta"], "dias": [0, 1, 2, 3, 4, 5, 6]}]` |
| Godoy, Maria | MAX_HORAS_MES_CALENDARIO | HARD | Límite máximo estricto de horas a trabajar por mes calendario. JSON: {"max_horas": 144} | `{"max_horas": 24}` |
| Godoy, Maria | MIN_HORAS_MES_CALENDARIO | HARD | Mínimo de horas trabajadas más licencias por mes calendario. | `{"min_horas": 0}` |
| Godoy, Maria | SOLO_ASIGNACIONES_FIJAS | HARD | El profesional solo realiza guardias asignadas mediante ASIGNACION_FIJA y no se le asignan turnos libres. | `{}` |
| Kolarik, Jorge Luis | MAX_TURNOS | HARD | Limite maximo de un grupo de turnos por semana o mes. JSON: [{"turnos": ["Dia_UTI", "Noche"], "max_por_mes": 1}] | `[{"turnos": ["D_Planta", "N_Planta"], "max_por_mes": 1}]` |
| Matricadi, Wendy Ailen | MAX_TURNOS | HARD | Limite maximo de un grupo de turnos por semana o mes. JSON: [{"turnos": ["Dia_UTI", "Noche"], "max_por_mes": 1}] | `[{"turnos": ["D_Planta", "N_Planta"], "max_por_mes": 1}]` |
| Mora, Sergio Enrique | MAX_TURNOS | HARD | Limite maximo de un grupo de turnos por semana o mes. JSON: [{"turnos": ["Dia_UTI", "Noche"], "max_por_mes": 1}] | `[{"turnos": ["D_Planta", "N_Planta"], "max_por_mes": 1}]` |
| Mora, Sergio Enrique | SOLO_ASIGNACIONES_FIJAS | HARD | El profesional solo realiza guardias asignadas mediante ASIGNACION_FIJA y no se le asignan turnos libres. | `{}` |
| Motta, Mayra Belen | MAX_TURNOS | HARD | Limite maximo de un grupo de turnos por semana o mes. JSON: [{"turnos": ["Dia_UTI", "Noche"], "max_por_mes": 1}] | `[{"turnos": ["D_Planta", "N_Planta"], "max_por_mes": 1}]` |
| Moya, Pedro | MAX_TURNOS | HARD | Limite maximo de un grupo de turnos por semana o mes. JSON: [{"turnos": ["Dia_UTI", "Noche"], "max_por_mes": 1}] | `[{"turnos": ["D_Planta", "N_Planta"], "max_por_mes": 1}]` |
| Murillo, Santiago | MAX_HORAS_MES_CALENDARIO | HARD | Límite máximo estricto de horas a trabajar por mes calendario. JSON: {"max_horas": 144} | `{"max_horas": 134}` |
| Murillo, Santiago | MAX_TURNOS | HARD | Limite maximo de un grupo de turnos por semana o mes. JSON: [{"turnos": ["Dia_UTI", "Noche"], "max_por_mes": 1}] | `[{"turnos": ["D_Planta", "N_Planta"], "max_por_mes": 1}]` |
| Murillo, Santiago | MIN_HORAS_MES_CALENDARIO | HARD | Mínimo de horas trabajadas más licencias por mes calendario. | `{"min_horas": 95}` |
| Navarro Suarez, Gabriela Belén | MAX_TURNOS | HARD | Limite maximo de un grupo de turnos por semana o mes. JSON: [{"turnos": ["Dia_UTI", "Noche"], "max_por_mes": 1}] | `[{"turnos": ["D_Planta", "N_Planta"], "max_por_mes": 1}]` |
| Nesteruk, María Silvia | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `[{"turnos": ["D_Planta", "N_Planta"], "dias": [0, 1, 2, 3, 4, 5, 6]}]` |
| Noriega, Claudio Martín | MAX_TURNOS | HARD | Limite maximo de un grupo de turnos por semana o mes. JSON: [{"turnos": ["Dia_UTI", "Noche"], "max_por_mes": 1}] | `[{"turnos": ["D_Planta", "N_Planta"], "max_por_mes": 1}]` |
| Núñez, Florencia Natalia | MAX_TURNOS | HARD | Limite maximo de un grupo de turnos por semana o mes. JSON: [{"turnos": ["Dia_UTI", "Noche"], "max_por_mes": 1}] | `[{"turnos": ["D_Planta", "N_Planta"], "max_por_mes": 1}]` |
| Pacheco, Celeste | MAX_TURNOS | HARD | Limite maximo de un grupo de turnos por semana o mes. JSON: [{"turnos": ["Dia_UTI", "Noche"], "max_por_mes": 1}] | `[{"turnos": ["D_Planta", "N_Planta"], "max_por_mes": 1}]` |
| Palermo, Agustín | MAX_TURNOS | HARD | Limite maximo de un grupo de turnos por semana o mes. JSON: [{"turnos": ["Dia_UTI", "Noche"], "max_por_mes": 1}] | `[{"turnos": ["D_Planta", "N_Planta"], "max_por_mes": 1}]` |
| Pregot, Analia Mariana | MAX_TURNOS | HARD | Limite maximo de un grupo de turnos por semana o mes. JSON: [{"turnos": ["Dia_UTI", "Noche"], "max_por_mes": 1}] | `[{"turnos": ["D_Planta", "N_Planta"], "max_por_mes": 1}]` |
| Quintero, Anabela Belen | EXACTO_FINDE_Y_DIA | HARD | Unified rule | `{"suspendida": true}` |
| Quintero, Anabela Belen | MAX_HORAS_MES_CALENDARIO | HARD | Límite máximo estricto de horas a trabajar por mes calendario. JSON: {"max_horas": 144} | `{"max_horas": 48}` |
| Quintero, Anabela Belen | MAX_TURNOS | HARD | Limite maximo de un grupo de turnos por semana o mes. JSON: [{"turnos": ["Dia_UTI", "Noche"], "max_por_mes": 1}] | `[{"turnos": ["D_Planta", "N_Planta"], "max_por_mes": 1}]` |
| Quintero, Anabela Belen | MIN_HORAS_MES_CALENDARIO | HARD | Mínimo de horas trabajadas más licencias por mes calendario. | `{"min_horas": 0}` |
| Quintero, Anabela Belen | SOLO_ASIGNACIONES_FIJAS | HARD | El profesional solo realiza guardias asignadas mediante ASIGNACION_FIJA y no se le asignan turnos libres. | `{}` |
| Quiroga Sassu, Maria Macarena | MAX_TURNOS | HARD | Limite maximo de un grupo de turnos por semana o mes. JSON: [{"turnos": ["Dia_UTI", "Noche"], "max_por_mes": 1}] | `[{"turnos": ["D_Planta", "N_Planta"], "max_por_mes": 1}]` |
| Silva, Martín Enrique | MAX_TURNOS | HARD | Limite maximo de un grupo de turnos por semana o mes. JSON: [{"turnos": ["Dia_UTI", "Noche"], "max_por_mes": 1}] | `[{"turnos": ["D_Planta", "N_Planta"], "max_por_mes": 1}]` |
| Sánchez Reinoso, Ana Belén | MAX_TURNOS | HARD | Limite maximo de un grupo de turnos por semana o mes. JSON: [{"turnos": ["Dia_UTI", "Noche"], "max_por_mes": 1}] | `[{"turnos": ["D_Planta", "N_Planta"], "max_por_mes": 1}]` |
| Villegas Oliva, Maria Belén | MAX_TURNOS | HARD | Limite maximo de un grupo de turnos por semana o mes. JSON: [{"turnos": ["Dia_UTI", "Noche"], "max_por_mes": 1}] | `[{"turnos": ["D_Planta", "N_Planta"], "max_por_mes": 2}]` |
| Zeballos, Valeria Alejandra | MAX_TURNOS | HARD | Limite maximo de un grupo de turnos por semana o mes. JSON: [{"turnos": ["Dia_UTI", "Noche"], "max_por_mes": 1}] | `[{"turnos": ["D_Planta", "N_Planta"], "max_por_mes": 1}]` |

## 3. Ajustes Personales & Licencias

### Ajustes Temporales de Reglas Personales

| Profesional | Código Regla | Inicio | Fin | Acción | Parámetros |
| --- | --- | --- | --- | --- | --- |
| Aguilera, Graciela | EXACTO_FINDE_Y_DIA | 2026-06-01 | 2026-12-31 | SOBRESCRIBIR | `{"dia_semana": "Viernes", "findes_por_disponibilidad": {"5": 2, "4": 2, "3": 2, "2": 1, "1": 1, "0": 0}, "dias_por_disponibilidad": {"5": 2, "4": 2, "3": 2, "2": 1, "1": 0, "0": 0}, "modo": "HARD", "peso_soft": 100000}` |
| Aguilera, Graciela | ASIGNACION_FIJA | 2026-07-09 | 2026-07-09 | SOBRESCRIBIR | `[{"Fecha": "2026-07-09", "Turno": "N_Planta"}]` |
| Aguilera, Graciela | ASIGNACION_FIJA | 2026-07-12 | 2026-07-12 | SOBRESCRIBIR | `[{"Fecha": "2026-07-12", "Turno": "D_Planta"}]` |
| Arias, Guillermina | FRANCO_FORZADO | 2026-07-08 | 2026-07-12 | SOBRESCRIBIR | `{}` |
| Biscarra, Joaquín Martin | MAX_HORAS_MES_CALENDARIO | 2026-07-01 | 2026-07-31 | SOBRESCRIBIR | `{"max_horas": 170}` |
| Biscarra, Joaquín Martin | MIN_HORAS_MES_CALENDARIO | 2026-07-01 | 2026-07-31 | SOBRESCRIBIR | `{"min_horas": 145}` |
| Diaz Villafañe Morales, Abigail | ASIGNACION_FIJA | 2026-07-11 | 2026-07-11 | SOBRESCRIBIR | `[{"Fecha": "2026-07-11", "Turno": "G_Planta"}]` |
| Garcia Rodriguez, Maria Eugenia | EXACTO_FINDE_Y_DIA | 2026-06-01 | 2026-12-31 | SOBRESCRIBIR | `{"dia_semana": "Viernes", "findes_por_disponibilidad": {"5": 2, "4": 2, "3": 2, "2": 1, "1": 1, "0": 0}, "dias_por_disponibilidad": {"5": 2, "4": 2, "3": 2, "2": 1, "1": 0, "0": 0}, "modo": "SOFT", "peso_soft": 100000}` |
| Garcia Rodriguez, Maria Eugenia | FRANCO_FORZADO | 2026-07-09 | 2026-07-11 | SOBRESCRIBIR | `{}` |
| Garcia Rodriguez, Maria Eugenia | ASIGNACION_FIJA | 2026-07-12 | 2026-07-12 | SOBRESCRIBIR | `[{"Fecha": "2026-07-12", "Turno": "N_Planta"}]` |
| Garcia Rodriguez, Maria Eugenia | ASIGNACION_FIJA | 2026-07-14 | 2026-07-14 | SOBRESCRIBIR | `[{"Fecha": "2026-07-14", "Turno": "D_Planta"}]` |
| Matricadi, Wendy Ailen | MAX_HORAS_MES_CALENDARIO | 2026-07-01 | 2026-07-31 | SOBRESCRIBIR | `{"max_horas": 170}` |
| Matricadi, Wendy Ailen | MIN_HORAS_MES_CALENDARIO | 2026-07-01 | 2026-07-31 | SOBRESCRIBIR | `{"min_horas": 145}` |
| Matricadi, Wendy Ailen | FRANCO_FORZADO | 2026-07-09 | 2026-07-12 | SOBRESCRIBIR | `{}` |
| Mora, Sergio Enrique | ASIGNACION_FIJA | 2026-07-02 | 2026-07-02 | SOBRESCRIBIR | `[{"Fecha": "2026-07-02", "Turno": "G_Planta"}]` |
| Mora, Sergio Enrique | ASIGNACION_FIJA | 2026-07-06 | 2026-07-06 | SOBRESCRIBIR | `[{"Fecha": "2026-07-06", "Turno": "G_Planta"}]` |
| Mora, Sergio Enrique | FRANCO_FORZADO | 2026-07-08 | 2026-07-12 | SOBRESCRIBIR | `{}` |
| Mora, Sergio Enrique | ASIGNACION_FIJA | 2026-07-20 | 2026-07-20 | SOBRESCRIBIR | `[{"Fecha": "2026-07-20", "Turno": "G_Planta"}]` |
| Mora, Sergio Enrique | ASIGNACION_FIJA | 2026-07-25 | 2026-07-25 | SOBRESCRIBIR | `[{"Fecha": "2026-07-025", "Turno": "G_Planta"}]` |
| Mora, Sergio Enrique | ASIGNACION_FIJA | 2026-07-28 | 2026-07-28 | SOBRESCRIBIR | `[{"Fecha": "2026-07-28", "Turno": "G_Planta"}]` |
| Mora, Sergio Enrique | ASIGNACION_FIJA | 2026-07-31 | 2026-07-31 | SOBRESCRIBIR | `[{"Fecha": "2026-07-31", "Turno": "G_Planta"}]` |
| Murillo, Santiago | FRANCO_FORZADO | 2026-07-02 | 2026-07-05 | SOBRESCRIBIR | `{}` |
| Murillo, Santiago | ASIGNACION_FIJA | 2026-07-11 | 2026-07-11 | SOBRESCRIBIR | `[{"Fecha": "2026-07-11", "Turno": "G_Planta"}]` |
| Nesteruk, María Silvia | FRANCO_FORZADO | 2026-07-08 | 2026-07-12 | SOBRESCRIBIR | `{}` |
| Noriega, Claudio Martín | FRANCO_FORZADO | 2026-07-09 | 2026-07-10 | SOBRESCRIBIR | `{}` |
| Núñez, Florencia Natalia | MAX_HORAS_MES_CALENDARIO | 2026-07-01 | 2026-07-31 | SOBRESCRIBIR | `{"max_horas": 170}` |
| Núñez, Florencia Natalia | MIN_HORAS_MES_CALENDARIO | 2026-07-01 | 2026-07-31 | SOBRESCRIBIR | `{"min_horas": 145}` |
| Palermo, Agustín | MAX_HORAS_MES_CALENDARIO | 2026-07-01 | 2026-07-31 | SOBRESCRIBIR | `{"max_horas": 170}` |
| Palermo, Agustín | MIN_HORAS_MES_CALENDARIO | 2026-07-01 | 2026-07-31 | SOBRESCRIBIR | `{"min_horas": 145}` |
| Palermo, Agustín | ASIGNACION_FIJA | 2026-07-09 | 2026-07-09 | SOBRESCRIBIR | `{}` |
| Palermo, Agustín | FRANCO_FORZADO | 2026-07-09 | 2026-07-12 | SOBRESCRIBIR | `{}` |
| Pregot, Analia Mariana | FRANCO FORZADO | 2026-07-03 | 2026-07-03 | SOBRESCRIBIR | `{}` |
| Pregot, Analia Mariana | FRANCO FORZADO | 2026-07-05 | 2026-07-05 | SOBRESCRIBIR | `{}` |
| Pregot, Analia Mariana | FRANCO_FORZADO | 2026-07-08 | 2026-07-11 | SOBRESCRIBIR | `{}` |
| Pregot, Analia Mariana | FRANCO FORZADO | 2026-07-23 | 2026-07-27 | SOBRESCRIBIR | `{}` |
| Pregot, Analia Mariana | FRANCO FORZADO | 2026-07-31 | 2026-07-31 | SOBRESCRIBIR | `{}` |
| Quiroga Sassu, Maria Macarena | FRANCO_FORZADO | 2026-07-09 | 2026-07-12 | SOBRESCRIBIR | `{}` |
| Silva, Martín Enrique | FRANCO_FORZADO | 2026-07-08 | 2026-07-12 | SOBRESCRIBIR | `{}` |
| Sánchez Reinoso, Ana Belén | ASIGNACION_FIJA | 2026-07-10 | 2026-07-10 | SOBRESCRIBIR | `[{"Fecha": "2026-07-10", "Turno": "G_Planta"}]` |
| Villegas Oliva, Maria Belén | MAX_HORAS_MES_CALENDARIO | 2026-07-01 | 2026-07-31 | SOBRESCRIBIR | `{"max_horas": 170}` |
| Villegas Oliva, Maria Belén | MIN_HORAS_MES_CALENDARIO | 2026-07-01 | 2026-07-31 | SOBRESCRIBIR | `{"min_horas": 145}` |
| Villegas Oliva, Maria Belén | FRANCO_FORZADO | 2026-07-10 | 2026-07-12 | SOBRESCRIBIR | `{}` |
| Zeballos, Valeria Alejandra | FRANCO_FORZADO | 2026-07-09 | 2026-07-12 | SOBRESCRIBIR | `{}` |

### Licencias Cargadas

| Profesional | Tipo | Inicio | Fin | Detalle |
| --- | --- | --- | --- | --- |
| Aguilera, Graciela | LPP | 2026-06-22 | 2026-07-05 | - |
| Biscarra, Joaquín Martin | LAR | 2026-07-13 | 2026-07-19 | - |
| Kolarik, Jorge Luis | LM | 2026-06-01 | 2026-12-31 | - |
| Mora, Sergio Enrique | LAR | 2026-07-13 | 2026-07-19 | - |
| Moya, Pedro | LAR | 2026-06-29 | 2026-07-12 | - |
| Murillo, Santiago | LAR | 2026-07-04 | 2026-07-10 | - |
| Murillo, Santiago | LPP | 2026-07-13 | 2026-07-19 | - |
| Navarro Suarez, Gabriela Belén | LAR | 2026-06-29 | 2026-07-07 | - |
| Silva, Martín Enrique | LAR | 2026-07-06 | 2026-07-19 | - |
| Sánchez Reinoso, Ana Belén | LPP | 2026-07-11 | 2026-07-24 | - |

### Asignaciones Fijas / Guardias Aprobadas

*(Sin guardias aprobadas / asignaciones previas para este período)*

## 4. Demanda y Oferta de Turnos

### Demanda Base (Vacantes Requeridas)

| Puesto | Tipo Día | Hora Inicio | Hora Fin | Mínimo | Máximo | Días Habilitados |
| --- | --- | --- | --- | --- | --- | --- |
| Planta | Finde_Feriado | 08:00 | 20:00 | 3 | 6 | - |
| Planta | Finde_Feriado | 20:00 | 08:00 | 3 | 6 | - |
| Planta | Semana | 08:00 | 20:00 | 3 | 6 | - |
| Planta | Semana | 20:00 | 08:00 | 3 | 6 | - |
| Residente | Finde_Feriado | 08:00 | 20:00 | 1 | 3 | - |
| Residente | Finde_Feriado | 20:00 | 08:00 | 1 | 3 | - |
| Residente | Semana | 08:00 | 20:00 | 1 | 3 | - |
| Residente | Semana | 20:00 | 08:00 | 1 | 3 | - |

### Ajustes Temporales de Demanda

*(Sin ajustes de demanda activos en este período)*

### Oferta de Turnos Configurada

| Turno | Hora Inicio | Horas | Días Semana | Puesto | Orden |
| --- | --- | --- | --- | --- | --- |
| G_Planta | 08:00 | 24 | 0,1,2,3,4,5,6 | Planta | 1 |
| G_Residente | 08:00 | 24 | 0,1,2,3,4,5,6 | Residente | 1 |
| D_Planta | 08:00 | 12 | 0,1,2,3,4,5,6 | Planta | 2 |
| D_Residente | 08:00 | 12 | 0,1,2,3,4,5,6 | Residente | 2 |
| N_Planta | 20:00 | 12 | 0,1,2,3,4,5,6 | Planta | 3 |
| N_Residente | 20:00 | 12 | 5,6 | Residente | 3 |

### Ajustes Temporales de Turnos / Vacantes

*(Sin ajustes temporales de turnos activos en este período)*


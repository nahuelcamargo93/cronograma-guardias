# Reporte de Auditoría de Configuración

- **Servicio:** Enfermeria UTI (ID: 2)
- **Organización:** Organización Principal
- **Período a Auditar:** 2026-07
- **Fecha Generación:** 2026-06-07 13:43:11

## 1. Resumen Servicio & Reglas Activas

### Reglas de Negocio Aplicables

| Código Regla | Tipo | Origen | Activo | Descripción | Parámetros |
| --- | --- | --- | --- | --- | --- |
| LIMITES_SOFT_RULES | SOFT | Servicio | Sí | Límite superior de horas mensuales para dimensionar variables del solver (MAX_HORAS_LIMITE_BASE) | `{"MAX_HORAS_LIMITE_BASE": 150}` |
| PENALIZACION_TURNO_AUSENTE | SOFT | Servicio | Sí | Penaliza si una persona no tiene al menos una semana de un tipo específico en el mes | `{"peso": 5000}` |
| PESO_BRECHA_DIARIA_PERSONAL | SOFT | Servicio | Sí | Peso de penalización por diferencia de personal asignado por día y puesto/turno | `{"peso_brecha": 5000, "peso_cobertura": 10}` |
| PESO_EQUIDAD_FERIADOS | SOFT | Servicio | Sí | Peso de penalización por desigualdad en feriados trabajados anuales | `{"peso": 1500}` |
| DESCANSO_ENTRE_TURNOS | HARD | Servicio | Sí | Horas mínimas de descanso entre el fin de un turno y el comienzo del siguiente. JSON: {"horas": 12} | `{"por_turno": {"M": 12, "T": 12, "TN": 12, "N": 12, "TNN": 12, "MT": 12}}` |
| DIA_MADRE_PADRE_LIBRE | HARD | Servicio | Sí | El profesional tiene franco obligatorio el día de la madre o del padre según corresponda | `{"activo": true}` |
| ESQUEMA_SEMANAL_ENFERMERIA | HARD | Servicio | Sí | Esquema semanal fijo para Enfermería Servicio 2 (4 turnos de 6h y 1 de 12h condicional a semana activa) | `{"excluidos": ["POLETTI NATALIA"], "modo": "HARD", "turnos": ["MT", "TNN"], "cantidad": 1}` |
| EXCLUIR_TURNOS | HARD | Servicio | Sí | Prohibición explícita de ciertos turnos para una persona | `[{"turnos": ["TNN", "MT"], "dias": [5, 6]}]` |
| FINDE_POST_LICENCIA | HARD | Servicio | Sí | El primer fin de semana después de volver de una licencia debe trabajarse. JSON: {"configuracion": "completo"} | `{"configuracion": "completo"}` |
| FIN_LICENCIA | HARD | Servicio | Sí | Obliga a trabajar el día inmediatamente posterior al fin de una licencia (LAR/LPP). | `{}` |
| MAX_DIAS_CONTINUOS | HARD | Servicio | Sí | Límite máximo de días consecutivos/seguidos de trabajo | `{"max_dias": 6}` |
| MAX_FERIADOS_ANUAL | HARD | Servicio | Sí | Límite máximo estricto de feriados trabajados al año. | `{"max_feriados": 10}` |
| MAX_FRANCOS_CONTINUOS | HARD | Servicio | Sí | Límite máximo de francos seguidos (consecutivos) permitidos. JSON: {"max_francos": 3, "modo": "HARD", "peso_soft": 10000} | `{"max_francos": 3, "modo": "SOFT", "peso_soft": 10000}` |
| MAX_FRANCOS_SEMANA | HARD | Servicio | Sí | Límite máximo de francos por semana calendario | `{"limite": 3, "modo": "SOFT", "peso_soft": 10000}` |
| MAX_HORAS_MES_CALENDARIO | HARD | Servicio | Sí | Límite máximo estricto de horas a trabajar por mes calendario. JSON: {"max_horas": 144} | `{"max_horas": 146}` |
| MAX_HORAS_SEMANA | HARD | Servicio | Sí | Límite máximo de horas por semana | `{"limite": 36}` |
| MEZCLA_SEMANAL_DURA | HARD | Servicio | Sí | Prohíbe mezclar familias de turno (M, T, TN, N) en una misma semana | `{}` |
| MIN_HORAS_MES_CALENDARIO | HARD | Servicio | Sí | Mínimo de horas trabajadas más licencias por mes calendario. | `{"min_horas": 140, "minimo": 140}` |
| NO_REPETIR_TURNO_CONSECUTIVO | HARD | Servicio | Sí | Prohíbe repetir el mismo tipo de turno semanal en semanas consecutivas | `{}` |
| UN_TURNO_POR_DIA | HARD | Servicio | Sí | Restriccion universal: una persona no puede tener mas de un turno asignado el mismo dia. No tiene parametros configurables. | `{}` |

### Ajustes Temporales de Servicio

| Código Regla | Inicio | Fin | Acción | Activo | Parámetros |
| --- | --- | --- | --- | --- | --- |
| EXCLUIR_TURNOS | 2026-07-04 | 2026-07-07 | SUSPENDER | Sí | `{}` |

## 2. Personal y Perfiles

| Nombre | Categoría | Rol | Régimen | Horas Reg. | Cumpleaños | M/P | Puestos |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ABELENDA GRISELL | - | Rotativo | CCTHRC | - | 1971-08-19 | - | UTI |
| ALBELO TANIA | - | Rotativo | MNT | - | 1995-10-13 | - | UTI |
| ALCARAZ ELIANA | - | Rotativo | CCTHRC | - | 1989-10-24 | - | UTI |
| ALCARAZ FRANCISO | - | Rotativo | CS | - | 1985-05-25 | - | UTI |
| ANDREOLI LUCIANA | - | Rotativo | CS | - | 1985-06-01 | - | UTI |
| ARCE DANIEL | - | Rotativo | CCTHRC | - | 1986-06-30 | Padre | UTI |
| ASTUDILLO MELINA | - | Rotativo | MNT | - | 1993-01-28 | - | UTI |
| BARROSO ERICA | - | Rotativo | CCTHRC | - | 1980-03-06 | - | UTI |
| BASCUR ALEJANDRA | - | Rotativo | CCT | - | 1991-02-03 | - | UTI |
| BORIA MAYRA | - | Rotativo | MNT | - | 1991-12-10 | - | UTI |
| CALDERON MARIA JOSE | - | Rotativo | MNT | - | 1992-05-30 | - | UTI |
| CAMPOS PRISCILA | - | Rotativo | CS | - | 1989-03-27 | - | UTI |
| CARRERAS FLAVIA | - | Rotativo | CS | - | 1991-10-11 | - | UTI |
| CASTRO LUCIANO | - | Rotativo | CCTHRC | - | 1997-06-27 | - | UTI |
| CHIRINO CAROLINA | - | Rotativo | MNT | - | 1991-08-26 | - | UTI |
| CORIA LUCIANO | - | Rotativo | MNT | - | 2002-12-05 | - | UTI |
| CORSO ARTURO | - | Rotativo | MNT | - | 1982-04-06 | Padre | UTI |
| DOMINGUEZ VERONICA | - | Rotativo | CCTHRC | - | 1993-09-23 | - | UTI |
| DURAN JAZMIN | - | Rotativo | MNT | - | 2003-05-05 | - | UTI |
| ECHENIQUE ROCIO | - | Rotativo | CCTHRC | - | 1999-03-25 | - | UTI |
| ESCALANTE CARLA | - | Rotativo | MNT | - | 1990-07-29 | - | UTI |
| ESCUDERO SERGIO | - | Rotativo | CS | - | 1990-09-30 | Padre | UTI |
| FERNANDEZ PAOLA | - | Rotativo | CCTHRC | - | 1997-08-08 | - | UTI |
| FERNANDEZ YESICA | - | Rotativo | CCTHRC | - | 1984-05-01 | - | UTI |
| GIMENEZ KAREN | - | Rotativo | MNT | - | 1999-03-01 | - | UTI |
| GOMES STHEFANIA | - | Rotativo | MNT | - | 1994-10-20 | - | UTI |
| GOMEZ LOURDES | - | Rotativo | CCTHRC | - | 1991-01-24 | - | UTI |
| GRABOVIECKI FERNANDA | - | Rotativo | CCTHRC | - | 1996-07-29 | - | UTI |
| GUIÑAZU KARINA | - | Rotativo | CS | - | 1992-03-09 | - | UTI |
| LUCERO MATIAS | - | Rotativo | CCTHRC | - | 1996-06-13 | - | UTI |
| MAÑE LORENA | - | Rotativo | MNT | - | 1993-01-26 | - | UTI |
| MEDINA LAURA | - | Rotativo | CCTHRC | - | 1993-09-24 | - | UTI |
| MIRANDA LUCIANA | - | Rotativo | CCTHRC | - | 1986-02-17 | - | UTI |
| MIRANDA YANINA | - | Rotativo | CS | - | 1987-04-06 | - | UTI |
| MONDONE PAULA | - | Rotativo | CS | - | 1990-07-19 | - | UTI |
| NIEVAS CARLA | - | Rotativo | MNT | - | 1996-06-20 | - | UTI |
| OLGUIN LUCIA | - | Rotativo | MNT | - | 1994-10-01 | - | UTI |
| ORTIZ LAURA | - | Rotativo | CS | - | 1993-05-21 | - | UTI |
| PALACIOS FACUNDO | - | Rotativo | CS | - | 1989-09-20 | Padre | UTI |
| PALANA GRACIELA | - | Rotativo | CCTHRC | - | 1973-05-23 | - | UTI |
| PEREIRA CRISTINA | - | Rotativo | CS | - | 1992-10-07 | - | UTI |
| POLETTI NATALIA | - | Rotativo | CS | - | 1980-01-15 | - | UTI |
| QUEVEDO CELESTE | - | Rotativo | CS | - | 1984-05-18 | - | UTI |
| RINALDINI IVANA | - | Rotativo | CCTHRC | - | 1990-11-17 | - | UTI |
| ROJAS JULIANA | - | Rotativo | CS | - | - | - | UTI |
| SOSA NAHUEL | - | Rotativo | - | - | 2001-03-31 | - | UTI |
| SUAREZ JESICA | - | Rotativo | CCTHRC | - | 1996-01-27 | - | UTI |
| TULA DAIANA | - | Rotativo | CCTHRC | - | 1989-07-19 | - | UTI |
| VELEZ DANIEL | - | Rotativo | CS | - | 1978-12-20 | Padre | UTI |
| VELIZ LIONEL | - | Rotativo | MNT | - | 2002-02-01 | - | UTI |
| VERA JULIETA | - | Rotativo | CCTHRC | - | 1992-02-15 | - | UTI |

### Reglas Individuales de Personal

| Profesional | Código Regla | Tipo | Descripción | Parámetros |
| --- | --- | --- | --- | --- |
| POLETTI NATALIA | EXCLUIR_TURNOS | HARD | Prohibición explícita de ciertos turnos para una persona | `[{"turnos": ["M", "T", "TN", "N"], "dias": [0, 1, 2, 3, 4, 5, 6]}]` |
| POLETTI NATALIA | MAX_DIAS_CONTINUOS | HARD | Límite máximo de días consecutivos/seguidos de trabajo | `{"max_dias": 3}` |
| POLETTI NATALIA | MAX_FRANCOS_CONTINUOS | HARD | Límite máximo de francos seguidos (consecutivos) permitidos. JSON: {"max_francos": 3, "modo": "HARD", "peso_soft": 10000} | `{"suspendida": true}` |
| POLETTI NATALIA | MAX_FRANCOS_SEMANA | HARD | Límite máximo de francos por semana calendario | `{"suspendida": true}` |

## 3. Ajustes Personales & Licencias

### Ajustes Temporales de Reglas Personales

| Profesional | Código Regla | Inicio | Fin | Acción | Parámetros |
| --- | --- | --- | --- | --- | --- |
| ABELENDA GRISELL | FRANCO_FORZADO | 2026-07-02 | 2026-07-02 | SOBRESCRIBIR | `{}` |
| ALBELO TANIA | FRANCO_FORZADO | 2026-07-04 | 2026-07-07 | SOBRESCRIBIR | `{}` |
| ALCARAZ ELIANA | FRANCO_FORZADO | 2026-07-04 | 2026-07-07 | SOBRESCRIBIR | `{}` |
| ALCARAZ FRANCISO | FRANCO_FORZADO | 2026-07-04 | 2026-07-07 | SOBRESCRIBIR | `{}` |
| ASTUDILLO MELINA | FRANCO_FORZADO | 2026-07-09 | 2026-07-12 | SOBRESCRIBIR | `{}` |
| BASCUR ALEJANDRA | FRANCO_FORZADO | 2026-07-31 | 2026-07-31 | SOBRESCRIBIR | `{}` |
| BORIA MAYRA | EXCLUIR_TURNOS | 2026-06-01 | 2026-12-31 | SOBRESCRIBIR | `[{"turnos": ["T", "MT"], "dias": [1]}, {"turnos": ["TNN", "MT"], "dias": [5, 6]}]` |
| CALDERON MARIA JOSE | FRANCO_FORZADO | 2026-07-16 | 2026-07-19 | SOBRESCRIBIR | `{}` |
| CORSO ARTURO | FRANCO_FORZADO | 2026-07-18 | 2026-07-21 | SOBRESCRIBIR | `{}` |
| DURAN JAZMIN | FRANCO_FORZADO | 2026-07-04 | 2026-07-07 | SOBRESCRIBIR | `{}` |
| ESCALANTE CARLA | FRANCO_FORZADO | 2026-07-29 | 2026-07-29 | SOBRESCRIBIR | `{}` |
| ESCUDERO SERGIO | FRANCO_FORZADO | 2026-07-04 | 2026-07-04 | SOBRESCRIBIR | `{}` |
| FERNANDEZ YESICA | EXCLUIR_TURNOS | 2026-06-01 | 2026-12-31 | SOBRESCRIBIR | `[{"turnos": ["T", "MT"], "dias": [1]}, {"turnos": ["TNN", "MT"], "dias": [5, 6]}]` |
| FERNANDEZ YESICA | FRANCO_FORZADO | 2026-07-04 | 2026-07-07 | SOBRESCRIBIR | `{}` |
| GOMES STHEFANIA | FRANCO_FORZADO | 2026-07-04 | 2026-07-07 | SOBRESCRIBIR | `{}` |
| GOMEZ LOURDES | FRANCO_FORZADO | 2026-07-04 | 2026-07-07 | SOBRESCRIBIR | `{}` |
| GRABOVIECKI FERNANDA | FRANCO_FORZADO | 2026-07-29 | 2026-07-29 | SOBRESCRIBIR | `{}` |
| GUIÑAZU KARINA | FRANCO_FORZADO | 2026-07-04 | 2026-07-07 | SOBRESCRIBIR | `{}` |
| MEDINA LAURA | FRANCO_FORZADO | 2026-07-04 | 2026-07-07 | SOBRESCRIBIR | `{}` |
| MONDONE PAULA | FRANCO_FORZADO | 2026-07-18 | 2026-07-21 | SOBRESCRIBIR | `{}` |
| OLGUIN LUCIA | EXCLUIR_TURNOS | 2026-06-01 | 2026-12-31 | SOBRESCRIBIR | `[{"turnos": ["T", "MT"], "dias": [1]}, {"turnos": ["TNN", "MT"], "dias": [5, 6]}]` |
| OLGUIN LUCIA | FRANCO_FORZADO | 2026-07-04 | 2026-07-07 | SOBRESCRIBIR | `{}` |
| ORTIZ LAURA | FRANCO_FORZADO | 2026-07-04 | 2026-07-07 | SOBRESCRIBIR | `{}` |
| PEREIRA CRISTINA | FRANCO_FORZADO | 2026-07-04 | 2026-07-07 | SOBRESCRIBIR | `{}` |
| QUEVEDO CELESTE | FRANCO_FORZADO | 2026-07-08 | 2026-07-09 | SOBRESCRIBIR | `{}` |
| QUEVEDO CELESTE | FRACNO_FORZADO | 2026-07-18 | 2026-07-21 | SOBRESCRIBIR | `{}` |
| ROJAS JULIANA | FRANCO_FORZADO | 2026-07-09 | 2026-07-12 | SOBRESCRIBIR | `{}` |
| SOSA NAHUEL | FRANCO_FORZADO | 2026-07-20 | 2026-07-20 | SOBRESCRIBIR | `{}` |
| SUAREZ JESICA | FRANCO_FORZADO | 2026-07-04 | 2026-07-07 | SOBRESCRIBIR | `{}` |
| TULA DAIANA | FRANCO_FORZADO | 2026-07-04 | 2026-07-07 | SOBRESCRIBIR | `{}` |

### Licencias Cargadas

| Profesional | Tipo | Inicio | Fin | Detalle |
| --- | --- | --- | --- | --- |
| BASCUR ALEJANDRA | LPP | 2026-06-27 | 2026-07-14 | - |
| CASTRO LUCIANO | LPP | 2026-06-27 | 2026-07-14 | - |
| ECHENIQUE ROCIO | LPP | 2026-06-27 | 2026-07-14 | - |
| GUIÑAZU KARINA | LPP | 2026-06-27 | 2026-07-14 | - |
| IRAZABAL MARIANGELES | LM | 2026-06-01 | 2026-12-31 | - |
| MIRANDA LUCIANA | LPP | 2026-06-27 | 2026-07-14 | - |
| VERA JULIETA | LPP | 2026-06-27 | 2026-07-14 | - |

### Asignaciones Fijas / Guardias Aprobadas

*(Sin guardias aprobadas / asignaciones previas para este período)*

## 4. Demanda y Oferta de Turnos

### Demanda Base (Vacantes Requeridas)

| Puesto | Tipo Día | Hora Inicio | Hora Fin | Mínimo | Máximo | Días Habilitados |
| --- | --- | --- | --- | --- | --- | --- |
| UTI | Finde_Feriado | 06:00 | 12:00 | 7 | 9 | - |
| UTI | Finde_Feriado | 12:00 | 18:00 | 9 | 11 | - |
| UTI | Finde_Feriado | 18:00 | 00:00 | 7 | 9 | - |
| UTI | Finde_Feriado | 23:59 | 05:59 | 7 | 8 | - |
| UTI | Semana | 06:00 | 12:00 | 8 | 10 | - |
| UTI | Semana | 12:00 | 18:00 | 10 | 12 | - |
| UTI | Semana | 18:00 | 00:00 | 8 | 10 | - |
| UTI | Semana | 23:59 | 05:59 | 7 | 8 | - |

### Ajustes Temporales de Demanda

*(Sin ajustes de demanda activos en este período)*

### Oferta de Turnos Configurada

| Turno | Hora Inicio | Horas | Días Semana | Puesto | Orden |
| --- | --- | --- | --- | --- | --- |
| M | 06:00 | 6 | 0,1,2,3,4,5,6 | UTI | 1 |
| T | 12:00 | 6 | 0,1,2,3,4,5,6 | UTI | 2 |
| TN | 18:00 | 6 | 0,1,2,3,4,5,6 | UTI | 3 |
| N | 23:59 | 6 | 0,1,2,3,4,5,6 | UTI | 4 |
| TNN | 18:00 | 12 | 0,1,2,3,4,5,6 | UTI | 5 |
| MT | 06:00 | 12 | 0,1,2,3,4,5,6 | UTI | 6 |

### Ajustes Temporales de Turnos / Vacantes

*(Sin ajustes temporales de turnos activos en este período)*


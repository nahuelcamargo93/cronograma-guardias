# Reporte de Auditoría de Configuración

- **Servicio:** Enfermeria UTI (ID: 2)
- **Organización:** Organización Principal
- **Período a Auditar:** 2026-06
- **Fecha Generación:** 2026-05-30 21:38:59

## 1. Resumen Servicio & Reglas Activas

### Reglas de Negocio Aplicables

| Código Regla | Tipo | Origen | Activo | Descripción | Parámetros |
| --- | --- | --- | --- | --- | --- |
| FINDE_LARGO_REGLAMENTARIO_ESTRICTO | SOFT | Servicio | Sí | Finde largo obligatorio que debe caer dentro del mes | `{"suspendida": false, "cantidad": 1}` |
| LIMITES_SOFT_RULES | SOFT | Servicio | Sí | Límites base para dimensionar el solver (Semanas_Base, Min_Horas, Max_Horas_Limite, etc) | `{"SEMANAS_BASE": 4, "MIN_HORAS_BASE": 108, "MAX_HORAS_LIMITE_BASE": 200, "MAX_ANUAL_LIMITE": 5000, "MAX_SEG_LIMITE_BASE": 50, "MAX_FINDES_LIMITE_BASE": 8}` |
| PENALIZACION_TURNO | SOFT | Servicio | Sí | Penaliza la asignación de un turno específico | `[{"turno": "MT", "peso": 500}, {"turno": "TNN", "peso": 500}]` |
| PENALIZACION_TURNO_AUSENTE | SOFT | Servicio | Sí | Penaliza si una persona no tiene al menos una semana de un tipo específico en el mes | `{"peso": 5000}` |
| PESO_BRECHA_DIARIA_PERSONAL | SOFT | Servicio | Sí | Peso de penalización por diferencia de personal asignado por día y puesto/turno | `{"peso_brecha": 100, "peso_cobertura": 10}` |
| PESO_EQUIDAD_FERIADOS | SOFT | Servicio | Sí | Peso de penalización por desigualdad en feriados trabajados anuales | `{"peso": 500}` |
| PESO_EQUIDAD_FINDES_ANUAL | SOFT | Servicio | Sí | Peso de equidad de findes (historico anual) | `{"peso": 500}` |
| PESO_INCONSISTENCIA | SOFT | Servicio | Sí | Penalización por cambiar de tipo de turno (ej: UTI a UCO) en la semana | `{"peso": 500}` |
| PESO_MIX_HORARIO | SOFT | Servicio | Sí | Penalización por mezclar mañana y tarde en la misma semana | `{"peso": 50000}` |
| DESCANSO_ENTRE_TURNOS | HARD | Servicio | Sí | Horas mínimas de descanso entre el fin de un turno y el comienzo del siguiente. JSON: {"horas": 12} | `{"por_turno": {"M": 12, "T": 12, "TN": 12, "N": 12, "TNN": 12, "MT": 12}}` |
| DIA_MADRE_PADRE_LIBRE | HARD | Servicio | Sí | El profesional tiene franco obligatorio el día de la madre o del padre según corresponda | `{"activo": true}` |
| FINDES_COMPLETOS_Y_MEDIOS | HARD | Servicio | Sí | Asegura la cantidad exacta de fines de semana completos y medios trabajados según la disponibilidad. | `{"por_disponibilidad": {"5": {"completos": 3, "medios": 1}, "4": {"completos": 2, "medios": 1}, "3": {"completos": 1, "medios": 1}, "2": {"completos": 1, "medios": 0}, "1": {"completos": 1, "medios": 0}, "0": {"completos": 0, "medios": 0}}}` |
| FIN_LICENCIA | HARD | Servicio | Sí | Obliga a trabajar el día inmediatamente posterior al fin de una licencia (LAR/LPP). | `{}` |
| MAX_HORAS_MES_CALENDARIO | HARD | Servicio | Sí | Límite máximo estricto de horas a trabajar por mes calendario. JSON: {"max_horas": 144} | `{"max_horas": 146}` |
| MAX_HORAS_SEMANA | HARD | Servicio | Sí | Límite máximo de horas por semana | `{"limite": 36}` |
| MEZCLA_SEMANAL_DURA | HARD | Servicio | Sí | Prohíbe mezclar familias de turno (M, T, TN, N) en una misma semana | `{}` |
| MIN_HORAS_MES_CALENDARIO | HARD | Servicio | Sí | Mínimo de horas trabajadas más licencias por mes calendario. | `{"min_horas": 140, "minimo": 140}` |

### Ajustes Temporales de Servicio

*(Sin ajustes temporales del servicio en este período)*

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
| POLETTI NATALIA | PENALIZACION_TURNO_AUSENTE | SOFT | Penaliza si una persona no tiene al menos una semana de un tipo específico en el mes | `{"suspendida": true}` |

## 3. Ajustes Personales & Licencias

### Ajustes Temporales de Reglas Personales

*(Sin ajustes temporales de reglas de personal para este período)*

### Licencias Cargadas

| Profesional | Tipo | Inicio | Fin | Detalle |
| --- | --- | --- | --- | --- |
| ALCARAZ ELIANA | LPP | 2026-06-01 | 2026-06-14 | - |
| ALCARAZ FRANCISO | LPP | 2026-05-18 | 2026-06-01 | - |
| ASTUDILLO MELINA | LPP | 2026-06-10 | 2026-06-12 | - |
| BASCUR ALEJANDRA | LPP | 2026-06-27 | 2026-07-13 | - |
| CAMPOS PRISCILA | LPP | 2026-06-13 | 2026-06-29 | - |
| CARRERAS FLAVIA | LPP | 2026-06-01 | 2026-06-14 | - |
| CASTRO LUCIANO | LPP | 2026-06-27 | 2026-07-13 | - |
| DOMINGUEZ VERONICA | LPP | 2026-06-13 | 2026-06-29 | - |
| ECHENIQUE ROCIO | LPP | 2026-06-27 | 2026-07-13 | - |
| GOMEZ LOURDES | LPP | 2026-06-01 | 2026-06-14 | - |
| GUIÑAZU KARINA | LPP | 2026-06-27 | 2026-07-13 | - |
| IRAZABAL MARIANGELES | LM | 2026-06-01 | 2026-12-31 | - |
| LUCERO MATIAS | LPP | 2026-06-13 | 2026-06-29 | - |
| MAÑE LORENA | LPP | 2026-06-17 | 2026-06-19 | - |
| MIRANDA LUCIANA | LPP | 2026-06-27 | 2026-07-13 | - |
| MIRANDA YANINA | LPP | 2026-05-18 | 2026-06-01 | - |
| MONDONE PAULA | LPP | 2026-06-01 | 2026-06-14 | - |
| NIEVAS CARLA | LPP | 2026-06-24 | 2026-06-26 | - |
| PALANA GRACIELA | LPP | 2026-06-13 | 2026-06-29 | - |
| PEREIRA CRISTINA | LPP | 2026-06-13 | 2026-06-29 | - |
| POLETTI NATALIA | LPP | 2026-05-18 | 2026-06-01 | - |
| QUEVEDO CELESTE | LPP | 2026-05-18 | 2026-06-01 | - |
| RINALDINI IVANA | LPP | 2026-06-01 | 2026-06-14 | - |
| SUAREZ JESICA | LPP | 2026-06-13 | 2026-06-29 | - |
| VERA JULIETA | LPP | 2026-06-27 | 2026-07-13 | - |

### Asignaciones Fijas / Guardias Aprobadas

| Profesional | Fecha | Turno | Horas | ID Crono | Notas Cronograma |
| --- | --- | --- | --- | --- | --- |
| ABELENDA GRISELL | 2026-06-01 | MT | 12 | 128 | Historial de Enfermeria importado |
| ASTUDILLO MELINA | 2026-06-01 | M | 6 | 128 | Historial de Enfermeria importado |
| BARROSO ERICA | 2026-06-01 | MT | 12 | 128 | Historial de Enfermeria importado |
| BASCUR ALEJANDRA | 2026-06-01 | TNN | 12 | 128 | Historial de Enfermeria importado |
| CALDERON MARIA JOSE | 2026-06-01 | M | 6 | 128 | Historial de Enfermeria importado |
| CAMPOS PRISCILA | 2026-06-01 | TNN | 12 | 128 | Historial de Enfermeria importado |
| CASTRO LUCIANO | 2026-06-01 | T | 6 | 128 | Historial de Enfermeria importado |
| CHIRINO CAROLINA | 2026-06-01 | MT | 12 | 128 | Historial de Enfermeria importado |
| CORIA LUCIANO | 2026-06-01 | TN | 6 | 128 | Historial de Enfermeria importado |
| CORSO ARTURO | 2026-06-01 | T | 6 | 128 | Historial de Enfermeria importado |
| DOMINGUEZ VERONICA | 2026-06-01 | N | 6 | 128 | Historial de Enfermeria importado |
| DURAN JAZMIN | 2026-06-01 | TN | 6 | 128 | Historial de Enfermeria importado |
| ECHENIQUE ROCIO | 2026-06-01 | N | 6 | 128 | Historial de Enfermeria importado |
| ESCALANTE CARLA | 2026-06-01 | T | 6 | 128 | Historial de Enfermeria importado |
| ESCUDERO SERGIO | 2026-06-01 | TNN | 12 | 128 | Historial de Enfermeria importado |
| FERNANDEZ PAOLA | 2026-06-01 | N | 6 | 128 | Historial de Enfermeria importado |
| GOMES STHEFANIA | 2026-06-01 | N | 6 | 128 | Historial de Enfermeria importado |
| MAÑE LORENA | 2026-06-01 | TN | 6 | 128 | Historial de Enfermeria importado |
| MEDINA LAURA | 2026-06-01 | N | 6 | 128 | Historial de Enfermeria importado |
| OLGUIN LUCIA | 2026-06-01 | N | 6 | 128 | Historial de Enfermeria importado |
| ORTIZ LAURA | 2026-06-01 | T | 6 | 128 | Historial de Enfermeria importado |
| PALACIOS FACUNDO | 2026-06-01 | TN | 6 | 128 | Historial de Enfermeria importado |
| PALANA GRACIELA | 2026-06-01 | M | 6 | 128 | Historial de Enfermeria importado |
| PEREIRA CRISTINA | 2026-06-01 | MT | 12 | 128 | Historial de Enfermeria importado |
| ROJAS JULIANA | 2026-06-01 | MT | 12 | 128 | Historial de Enfermeria importado |
| SOSA NAHUEL | 2026-06-01 | TN | 6 | 128 | Historial de Enfermeria importado |
| SUAREZ JESICA | 2026-06-01 | TNN | 12 | 128 | Historial de Enfermeria importado |
| TULA DAIANA | 2026-06-01 | T | 6 | 128 | Historial de Enfermeria importado |
| VELEZ DANIEL | 2026-06-01 | TN | 6 | 128 | Historial de Enfermeria importado |
| VERA JULIETA | 2026-06-01 | M | 6 | 128 | Historial de Enfermeria importado |
| ABELENDA GRISELL | 2026-06-02 | M | 6 | 128 | Historial de Enfermeria importado |
| ALBELO TANIA | 2026-06-02 | T | 6 | 128 | Historial de Enfermeria importado |
| ALCARAZ FRANCISO | 2026-06-02 | TN | 6 | 128 | Historial de Enfermeria importado |
| ANDREOLI LUCIANA | 2026-06-02 | M | 6 | 128 | Historial de Enfermeria importado |
| ARCE DANIEL | 2026-06-02 | TN | 6 | 128 | Historial de Enfermeria importado |
| ASTUDILLO MELINA | 2026-06-02 | M | 6 | 128 | Historial de Enfermeria importado |
| BARROSO ERICA | 2026-06-02 | T | 6 | 128 | Historial de Enfermeria importado |
| BASCUR ALEJANDRA | 2026-06-02 | TN | 6 | 128 | Historial de Enfermeria importado |
| CALDERON MARIA JOSE | 2026-06-02 | M | 6 | 128 | Historial de Enfermeria importado |
| CAMPOS PRISCILA | 2026-06-02 | N | 6 | 128 | Historial de Enfermeria importado |
| CORSO ARTURO | 2026-06-02 | T | 6 | 128 | Historial de Enfermeria importado |
| DOMINGUEZ VERONICA | 2026-06-02 | TNN | 12 | 128 | Historial de Enfermeria importado |
| ECHENIQUE ROCIO | 2026-06-02 | N | 6 | 128 | Historial de Enfermeria importado |
| ESCALANTE CARLA | 2026-06-02 | T | 6 | 128 | Historial de Enfermeria importado |
| ESCUDERO SERGIO | 2026-06-02 | TN | 6 | 128 | Historial de Enfermeria importado |
| FERNANDEZ YESICA | 2026-06-02 | TNN | 12 | 128 | Historial de Enfermeria importado |
| GIMENEZ KAREN | 2026-06-02 | N | 6 | 128 | Historial de Enfermeria importado |
| GOMES STHEFANIA | 2026-06-02 | TN | 6 | 128 | Historial de Enfermeria importado |
| GRABOVIECKI FERNANDA | 2026-06-02 | N | 6 | 128 | Historial de Enfermeria importado |
| GUIÑAZU KARINA | 2026-06-02 | MT | 12 | 128 | Historial de Enfermeria importado |
| MAÑE LORENA | 2026-06-02 | TNN | 12 | 128 | Historial de Enfermeria importado |
| MIRANDA LUCIANA | 2026-06-02 | MT | 12 | 128 | Historial de Enfermeria importado |
| MIRANDA YANINA | 2026-06-02 | M | 6 | 128 | Historial de Enfermeria importado |
| NIEVAS CARLA | 2026-06-02 | M | 6 | 128 | Historial de Enfermeria importado |
| OLGUIN LUCIA | 2026-06-02 | TNN | 12 | 128 | Historial de Enfermeria importado |
| PALACIOS FACUNDO | 2026-06-02 | TNN | 12 | 128 | Historial de Enfermeria importado |
| PALANA GRACIELA | 2026-06-02 | MT | 12 | 128 | Historial de Enfermeria importado |
| PEREIRA CRISTINA | 2026-06-02 | T | 6 | 128 | Historial de Enfermeria importado |
| POLETTI NATALIA | 2026-06-02 | MT | 12 | 128 | Historial de Enfermeria importado |
| QUEVEDO CELESTE | 2026-06-02 | T | 6 | 128 | Historial de Enfermeria importado |
| ROJAS JULIANA | 2026-06-02 | M | 6 | 128 | Historial de Enfermeria importado |
| SUAREZ JESICA | 2026-06-02 | N | 6 | 128 | Historial de Enfermeria importado |
| VELIZ LIONEL | 2026-06-02 | M | 6 | 128 | Historial de Enfermeria importado |
| ABELENDA GRISELL | 2026-06-03 | M | 6 | 128 | Historial de Enfermeria importado |
| ALBELO TANIA | 2026-06-03 | T | 6 | 128 | Historial de Enfermeria importado |
| ALCARAZ FRANCISO | 2026-06-03 | TN | 6 | 128 | Historial de Enfermeria importado |
| ANDREOLI LUCIANA | 2026-06-03 | M | 6 | 128 | Historial de Enfermeria importado |
| ARCE DANIEL | 2026-06-03 | TN | 6 | 128 | Historial de Enfermeria importado |
| ASTUDILLO MELINA | 2026-06-03 | M | 6 | 128 | Historial de Enfermeria importado |
| BARROSO ERICA | 2026-06-03 | T | 6 | 128 | Historial de Enfermeria importado |
| BORIA MAYRA | 2026-06-03 | T | 6 | 128 | Historial de Enfermeria importado |
| CALDERON MARIA JOSE | 2026-06-03 | M | 6 | 128 | Historial de Enfermeria importado |
| CORIA LUCIANO | 2026-06-03 | TNN | 12 | 128 | Historial de Enfermeria importado |
| DOMINGUEZ VERONICA | 2026-06-03 | N | 6 | 128 | Historial de Enfermeria importado |
| DURAN JAZMIN | 2026-06-03 | TNN | 12 | 128 | Historial de Enfermeria importado |
| ESCALANTE CARLA | 2026-06-03 | MT | 12 | 128 | Historial de Enfermeria importado |
| FERNANDEZ YESICA | 2026-06-03 | N | 6 | 128 | Historial de Enfermeria importado |
| GIMENEZ KAREN | 2026-06-03 | TNN | 12 | 128 | Historial de Enfermeria importado |
| GOMES STHEFANIA | 2026-06-03 | TNN | 12 | 128 | Historial de Enfermeria importado |
| GRABOVIECKI FERNANDA | 2026-06-03 | TNN | 12 | 128 | Historial de Enfermeria importado |
| GUIÑAZU KARINA | 2026-06-03 | T | 6 | 128 | Historial de Enfermeria importado |
| LUCERO MATIAS | 2026-06-03 | TN | 6 | 128 | Historial de Enfermeria importado |
| MAÑE LORENA | 2026-06-03 | TN | 6 | 128 | Historial de Enfermeria importado |
| MEDINA LAURA | 2026-06-03 | N | 6 | 128 | Historial de Enfermeria importado |
| MIRANDA LUCIANA | 2026-06-03 | M | 6 | 128 | Historial de Enfermeria importado |
| MIRANDA YANINA | 2026-06-03 | M | 6 | 128 | Historial de Enfermeria importado |
| NIEVAS CARLA | 2026-06-03 | MT | 12 | 128 | Historial de Enfermeria importado |
| PEREIRA CRISTINA | 2026-06-03 | T | 6 | 128 | Historial de Enfermeria importado |
| POLETTI NATALIA | 2026-06-03 | T | 6 | 128 | Historial de Enfermeria importado |
| QUEVEDO CELESTE | 2026-06-03 | MT | 12 | 128 | Historial de Enfermeria importado |
| ROJAS JULIANA | 2026-06-03 | M | 6 | 128 | Historial de Enfermeria importado |
| SOSA NAHUEL | 2026-06-03 | TNN | 12 | 128 | Historial de Enfermeria importado |
| SUAREZ JESICA | 2026-06-03 | N | 6 | 128 | Historial de Enfermeria importado |
| TULA DAIANA | 2026-06-03 | T | 6 | 128 | Historial de Enfermeria importado |
| VELEZ DANIEL | 2026-06-03 | TN | 6 | 128 | Historial de Enfermeria importado |
| VELIZ LIONEL | 2026-06-03 | MT | 12 | 128 | Historial de Enfermeria importado |
| ABELENDA GRISELL | 2026-06-04 | M | 6 | 128 | Historial de Enfermeria importado |
| ALBELO TANIA | 2026-06-04 | T | 6 | 128 | Historial de Enfermeria importado |
| ALCARAZ FRANCISO | 2026-06-04 | TNN | 12 | 128 | Historial de Enfermeria importado |
| ANDREOLI LUCIANA | 2026-06-04 | M | 6 | 128 | Historial de Enfermeria importado |
| ARCE DANIEL | 2026-06-04 | TNN | 12 | 128 | Historial de Enfermeria importado |
| ASTUDILLO MELINA | 2026-06-04 | MT | 12 | 128 | Historial de Enfermeria importado |
| BARROSO ERICA | 2026-06-04 | T | 6 | 128 | Historial de Enfermeria importado |
| BORIA MAYRA | 2026-06-04 | MT | 12 | 128 | Historial de Enfermeria importado |
| CASTRO LUCIANO | 2026-06-04 | TN | 6 | 128 | Historial de Enfermeria importado |
| CHIRINO CAROLINA | 2026-06-04 | M | 6 | 128 | Historial de Enfermeria importado |
| CORIA LUCIANO | 2026-06-04 | TN | 6 | 128 | Historial de Enfermeria importado |
| CORSO ARTURO | 2026-06-04 | MT | 12 | 128 | Historial de Enfermeria importado |
| DURAN JAZMIN | 2026-06-04 | TN | 6 | 128 | Historial de Enfermeria importado |
| ESCUDERO SERGIO | 2026-06-04 | TN | 6 | 128 | Historial de Enfermeria importado |
| FERNANDEZ PAOLA | 2026-06-04 | TNN | 12 | 128 | Historial de Enfermeria importado |
| FERNANDEZ YESICA | 2026-06-04 | N | 6 | 128 | Historial de Enfermeria importado |
| GIMENEZ KAREN | 2026-06-04 | N | 6 | 128 | Historial de Enfermeria importado |
| GOMES STHEFANIA | 2026-06-04 | N | 6 | 128 | Historial de Enfermeria importado |
| GRABOVIECKI FERNANDA | 2026-06-04 | N | 6 | 128 | Historial de Enfermeria importado |
| GUIÑAZU KARINA | 2026-06-04 | T | 6 | 128 | Historial de Enfermeria importado |
| LUCERO MATIAS | 2026-06-04 | TN | 6 | 128 | Historial de Enfermeria importado |
| MEDINA LAURA | 2026-06-04 | TNN | 12 | 128 | Historial de Enfermeria importado |
| MIRANDA LUCIANA | 2026-06-04 | M | 6 | 128 | Historial de Enfermeria importado |
| MIRANDA YANINA | 2026-06-04 | MT | 12 | 128 | Historial de Enfermeria importado |
| OLGUIN LUCIA | 2026-06-04 | N | 6 | 128 | Historial de Enfermeria importado |
| ORTIZ LAURA | 2026-06-04 | T | 6 | 128 | Historial de Enfermeria importado |
| QUEVEDO CELESTE | 2026-06-04 | T | 6 | 128 | Historial de Enfermeria importado |
| ROJAS JULIANA | 2026-06-04 | M | 6 | 128 | Historial de Enfermeria importado |
| SOSA NAHUEL | 2026-06-04 | TN | 6 | 128 | Historial de Enfermeria importado |
| TULA DAIANA | 2026-06-04 | MT | 12 | 128 | Historial de Enfermeria importado |
| VELEZ DANIEL | 2026-06-04 | TNN | 12 | 128 | Historial de Enfermeria importado |
| VELIZ LIONEL | 2026-06-04 | M | 6 | 128 | Historial de Enfermeria importado |
| VERA JULIETA | 2026-06-04 | M | 6 | 128 | Historial de Enfermeria importado |
| ALBELO TANIA | 2026-06-05 | MT | 12 | 128 | Historial de Enfermeria importado |
| ANDREOLI LUCIANA | 2026-06-05 | MT | 12 | 128 | Historial de Enfermeria importado |
| ARCE DANIEL | 2026-06-05 | TN | 6 | 128 | Historial de Enfermeria importado |
| ASTUDILLO MELINA | 2026-06-05 | M | 6 | 128 | Historial de Enfermeria importado |
| BASCUR ALEJANDRA | 2026-06-05 | TN | 6 | 128 | Historial de Enfermeria importado |
| BORIA MAYRA | 2026-06-05 | T | 6 | 128 | Historial de Enfermeria importado |
| CALDERON MARIA JOSE | 2026-06-05 | MT | 12 | 128 | Historial de Enfermeria importado |
| CAMPOS PRISCILA | 2026-06-05 | N | 6 | 128 | Historial de Enfermeria importado |
| CASTRO LUCIANO | 2026-06-05 | TNN | 12 | 128 | Historial de Enfermeria importado |
| CHIRINO CAROLINA | 2026-06-05 | M | 6 | 128 | Historial de Enfermeria importado |
| CORIA LUCIANO | 2026-06-05 | TN | 6 | 128 | Historial de Enfermeria importado |
| CORSO ARTURO | 2026-06-05 | T | 6 | 128 | Historial de Enfermeria importado |
| DURAN JAZMIN | 2026-06-05 | TN | 6 | 128 | Historial de Enfermeria importado |
| ECHENIQUE ROCIO | 2026-06-05 | TNN | 12 | 128 | Historial de Enfermeria importado |
| ESCUDERO SERGIO | 2026-06-05 | TN | 6 | 128 | Historial de Enfermeria importado |
| FERNANDEZ PAOLA | 2026-06-05 | N | 6 | 128 | Historial de Enfermeria importado |
| GIMENEZ KAREN | 2026-06-05 | N | 6 | 128 | Historial de Enfermeria importado |
| GRABOVIECKI FERNANDA | 2026-06-05 | N | 6 | 128 | Historial de Enfermeria importado |
| LUCERO MATIAS | 2026-06-05 | TNN | 12 | 128 | Historial de Enfermeria importado |
| MEDINA LAURA | 2026-06-05 | N | 6 | 128 | Historial de Enfermeria importado |
| NIEVAS CARLA | 2026-06-05 | M | 6 | 128 | Historial de Enfermeria importado |
| OLGUIN LUCIA | 2026-06-05 | N | 6 | 128 | Historial de Enfermeria importado |
| ORTIZ LAURA | 2026-06-05 | MT | 12 | 128 | Historial de Enfermeria importado |
| PALACIOS FACUNDO | 2026-06-05 | TN | 6 | 128 | Historial de Enfermeria importado |
| PALANA GRACIELA | 2026-06-05 | M | 6 | 128 | Historial de Enfermeria importado |
| POLETTI NATALIA | 2026-06-05 | MT | 12 | 128 | Historial de Enfermeria importado |
| QUEVEDO CELESTE | 2026-06-05 | T | 6 | 128 | Historial de Enfermeria importado |
| SOSA NAHUEL | 2026-06-05 | TN | 6 | 128 | Historial de Enfermeria importado |
| TULA DAIANA | 2026-06-05 | T | 6 | 128 | Historial de Enfermeria importado |
| VELEZ DANIEL | 2026-06-05 | TN | 6 | 128 | Historial de Enfermeria importado |
| VELIZ LIONEL | 2026-06-05 | M | 6 | 128 | Historial de Enfermeria importado |
| VERA JULIETA | 2026-06-05 | MT | 12 | 128 | Historial de Enfermeria importado |
| ALCARAZ FRANCISO | 2026-06-06 | TN | 6 | 128 | Historial de Enfermeria importado |
| BARROSO ERICA | 2026-06-06 | T | 6 | 128 | Historial de Enfermeria importado |
| BASCUR ALEJANDRA | 2026-06-06 | TN | 6 | 128 | Historial de Enfermeria importado |
| BORIA MAYRA | 2026-06-06 | T | 6 | 128 | Historial de Enfermeria importado |
| CALDERON MARIA JOSE | 2026-06-06 | M | 6 | 128 | Historial de Enfermeria importado |
| CAMPOS PRISCILA | 2026-06-06 | N | 6 | 128 | Historial de Enfermeria importado |
| CASTRO LUCIANO | 2026-06-06 | TN | 6 | 128 | Historial de Enfermeria importado |
| CHIRINO CAROLINA | 2026-06-06 | M | 6 | 128 | Historial de Enfermeria importado |
| DOMINGUEZ VERONICA | 2026-06-06 | N | 6 | 128 | Historial de Enfermeria importado |
| ECHENIQUE ROCIO | 2026-06-06 | N | 6 | 128 | Historial de Enfermeria importado |
| ESCALANTE CARLA | 2026-06-06 | T | 6 | 128 | Historial de Enfermeria importado |
| ESCUDERO SERGIO | 2026-06-06 | TN | 6 | 128 | Historial de Enfermeria importado |
| FERNANDEZ PAOLA | 2026-06-06 | N | 6 | 128 | Historial de Enfermeria importado |
| FERNANDEZ YESICA | 2026-06-06 | N | 6 | 128 | Historial de Enfermeria importado |
| GUIÑAZU KARINA | 2026-06-06 | T | 6 | 128 | Historial de Enfermeria importado |
| LUCERO MATIAS | 2026-06-06 | TN | 6 | 128 | Historial de Enfermeria importado |
| MAÑE LORENA | 2026-06-06 | TN | 6 | 128 | Historial de Enfermeria importado |
| MEDINA LAURA | 2026-06-06 | N | 6 | 128 | Historial de Enfermeria importado |
| MIRANDA YANINA | 2026-06-06 | M | 6 | 128 | Historial de Enfermeria importado |
| NIEVAS CARLA | 2026-06-06 | M | 6 | 128 | Historial de Enfermeria importado |
| ORTIZ LAURA | 2026-06-06 | T | 6 | 128 | Historial de Enfermeria importado |
| PALACIOS FACUNDO | 2026-06-06 | TN | 6 | 128 | Historial de Enfermeria importado |
| PALANA GRACIELA | 2026-06-06 | M | 6 | 128 | Historial de Enfermeria importado |
| PEREIRA CRISTINA | 2026-06-06 | T | 6 | 128 | Historial de Enfermeria importado |
| QUEVEDO CELESTE | 2026-06-06 | T | 6 | 128 | Historial de Enfermeria importado |
| SUAREZ JESICA | 2026-06-06 | N | 6 | 128 | Historial de Enfermeria importado |
| TULA DAIANA | 2026-06-06 | T | 6 | 128 | Historial de Enfermeria importado |
| VELEZ DANIEL | 2026-06-06 | TN | 6 | 128 | Historial de Enfermeria importado |
| VELIZ LIONEL | 2026-06-06 | M | 6 | 128 | Historial de Enfermeria importado |
| VERA JULIETA | 2026-06-06 | M | 6 | 128 | Historial de Enfermeria importado |
| ABELENDA GRISELL | 2026-06-07 | M | 6 | 128 | Historial de Enfermeria importado |
| ALBELO TANIA | 2026-06-07 | T | 6 | 128 | Historial de Enfermeria importado |
| ARCE DANIEL | 2026-06-07 | TN | 6 | 128 | Historial de Enfermeria importado |
| BARROSO ERICA | 2026-06-07 | T | 6 | 128 | Historial de Enfermeria importado |
| BASCUR ALEJANDRA | 2026-06-07 | TN | 6 | 128 | Historial de Enfermeria importado |
| BORIA MAYRA | 2026-06-07 | T | 6 | 128 | Historial de Enfermeria importado |
| CAMPOS PRISCILA | 2026-06-07 | N | 6 | 128 | Historial de Enfermeria importado |
| CASTRO LUCIANO | 2026-06-07 | TN | 6 | 128 | Historial de Enfermeria importado |
| CHIRINO CAROLINA | 2026-06-07 | M | 6 | 128 | Historial de Enfermeria importado |
| CORIA LUCIANO | 2026-06-07 | TN | 6 | 128 | Historial de Enfermeria importado |
| CORSO ARTURO | 2026-06-07 | T | 6 | 128 | Historial de Enfermeria importado |
| DOMINGUEZ VERONICA | 2026-06-07 | N | 6 | 128 | Historial de Enfermeria importado |
| ECHENIQUE ROCIO | 2026-06-07 | N | 6 | 128 | Historial de Enfermeria importado |
| ESCALANTE CARLA | 2026-06-07 | T | 6 | 128 | Historial de Enfermeria importado |
| FERNANDEZ PAOLA | 2026-06-07 | N | 6 | 128 | Historial de Enfermeria importado |
| FERNANDEZ YESICA | 2026-06-07 | N | 6 | 128 | Historial de Enfermeria importado |
| GIMENEZ KAREN | 2026-06-07 | N | 6 | 128 | Historial de Enfermeria importado |
| GUIÑAZU KARINA | 2026-06-07 | T | 6 | 128 | Historial de Enfermeria importado |
| LUCERO MATIAS | 2026-06-07 | TN | 6 | 128 | Historial de Enfermeria importado |
| MAÑE LORENA | 2026-06-07 | TN | 6 | 128 | Historial de Enfermeria importado |
| MIRANDA LUCIANA | 2026-06-07 | M | 6 | 128 | Historial de Enfermeria importado |
| MIRANDA YANINA | 2026-06-07 | M | 6 | 128 | Historial de Enfermeria importado |
| NIEVAS CARLA | 2026-06-07 | M | 6 | 128 | Historial de Enfermeria importado |
| ORTIZ LAURA | 2026-06-07 | T | 6 | 128 | Historial de Enfermeria importado |
| PALACIOS FACUNDO | 2026-06-07 | TN | 6 | 128 | Historial de Enfermeria importado |
| PALANA GRACIELA | 2026-06-07 | M | 6 | 128 | Historial de Enfermeria importado |
| PEREIRA CRISTINA | 2026-06-07 | T | 6 | 128 | Historial de Enfermeria importado |
| ROJAS JULIANA | 2026-06-07 | M | 6 | 128 | Historial de Enfermeria importado |
| SOSA NAHUEL | 2026-06-07 | TN | 6 | 128 | Historial de Enfermeria importado |
| SUAREZ JESICA | 2026-06-07 | N | 6 | 128 | Historial de Enfermeria importado |
| ABELENDA GRISELL | 2026-06-08 | TNN | 12 | 128 | Historial de Enfermeria importado |
| ALCARAZ FRANCISO | 2026-06-08 | MT | 12 | 128 | Historial de Enfermeria importado |
| ARCE DANIEL | 2026-06-08 | T | 6 | 128 | Historial de Enfermeria importado |
| BARROSO ERICA | 2026-06-08 | M | 6 | 128 | Historial de Enfermeria importado |
| CASTRO LUCIANO | 2026-06-08 | T | 6 | 128 | Historial de Enfermeria importado |
| CHIRINO CAROLINA | 2026-06-08 | N | 6 | 128 | Historial de Enfermeria importado |
| CORIA LUCIANO | 2026-06-08 | T | 6 | 128 | Historial de Enfermeria importado |
| CORSO ARTURO | 2026-06-08 | M | 6 | 128 | Historial de Enfermeria importado |
| DOMINGUEZ VERONICA | 2026-06-08 | TN | 6 | 128 | Historial de Enfermeria importado |
| ECHENIQUE ROCIO | 2026-06-08 | TN | 6 | 128 | Historial de Enfermeria importado |
| ESCALANTE CARLA | 2026-06-08 | M | 6 | 128 | Historial de Enfermeria importado |
| ESCUDERO SERGIO | 2026-06-08 | T | 6 | 128 | Historial de Enfermeria importado |
| FERNANDEZ YESICA | 2026-06-08 | TNN | 12 | 128 | Historial de Enfermeria importado |
| GIMENEZ KAREN | 2026-06-08 | TN | 6 | 128 | Historial de Enfermeria importado |
| GUIÑAZU KARINA | 2026-06-08 | M | 6 | 128 | Historial de Enfermeria importado |
| MAÑE LORENA | 2026-06-08 | T | 6 | 128 | Historial de Enfermeria importado |
| MEDINA LAURA | 2026-06-08 | TNN | 12 | 128 | Historial de Enfermeria importado |
| MIRANDA LUCIANA | 2026-06-08 | N | 6 | 128 | Historial de Enfermeria importado |
| MIRANDA YANINA | 2026-06-08 | TNN | 12 | 128 | Historial de Enfermeria importado |
| NIEVAS CARLA | 2026-06-08 | N | 6 | 128 | Historial de Enfermeria importado |
| PALACIOS FACUNDO | 2026-06-08 | T | 6 | 128 | Historial de Enfermeria importado |
| PALANA GRACIELA | 2026-06-08 | TNN | 12 | 128 | Historial de Enfermeria importado |
| PEREIRA CRISTINA | 2026-06-08 | MT | 12 | 128 | Historial de Enfermeria importado |
| QUEVEDO CELESTE | 2026-06-08 | M | 6 | 128 | Historial de Enfermeria importado |
| ROJAS JULIANA | 2026-06-08 | M | 6 | 128 | Historial de Enfermeria importado |
| SOSA NAHUEL | 2026-06-08 | T | 6 | 128 | Historial de Enfermeria importado |
| SUAREZ JESICA | 2026-06-08 | TN | 6 | 128 | Historial de Enfermeria importado |
| TULA DAIANA | 2026-06-08 | M | 6 | 128 | Historial de Enfermeria importado |
| VELEZ DANIEL | 2026-06-08 | MT | 12 | 128 | Historial de Enfermeria importado |
| VERA JULIETA | 2026-06-08 | TNN | 12 | 128 | Historial de Enfermeria importado |
| ABELENDA GRISELL | 2026-06-09 | N | 6 | 128 | Historial de Enfermeria importado |
| ALBELO TANIA | 2026-06-09 | M | 6 | 128 | Historial de Enfermeria importado |
| ALCARAZ FRANCISO | 2026-06-09 | T | 6 | 128 | Historial de Enfermeria importado |
| ARCE DANIEL | 2026-06-09 | T | 6 | 128 | Historial de Enfermeria importado |
| BARROSO ERICA | 2026-06-09 | M | 6 | 128 | Historial de Enfermeria importado |
| BASCUR ALEJANDRA | 2026-06-09 | T | 6 | 128 | Historial de Enfermeria importado |
| BORIA MAYRA | 2026-06-09 | M | 6 | 128 | Historial de Enfermeria importado |
| CALDERON MARIA JOSE | 2026-06-09 | N | 6 | 128 | Historial de Enfermeria importado |
| CAMPOS PRISCILA | 2026-06-09 | TNN | 12 | 128 | Historial de Enfermeria importado |
| CORSO ARTURO | 2026-06-09 | MT | 12 | 128 | Historial de Enfermeria importado |
| DOMINGUEZ VERONICA | 2026-06-09 | TNN | 12 | 128 | Historial de Enfermeria importado |
| ECHENIQUE ROCIO | 2026-06-09 | TN | 6 | 128 | Historial de Enfermeria importado |
| ESCALANTE CARLA | 2026-06-09 | M | 6 | 128 | Historial de Enfermeria importado |
| ESCUDERO SERGIO | 2026-06-09 | T | 6 | 128 | Historial de Enfermeria importado |
| FERNANDEZ PAOLA | 2026-06-09 | TN | 6 | 128 | Historial de Enfermeria importado |
| FERNANDEZ YESICA | 2026-06-09 | TN | 6 | 128 | Historial de Enfermeria importado |
| GIMENEZ KAREN | 2026-06-09 | TN | 6 | 128 | Historial de Enfermeria importado |
| GOMES STHEFANIA | 2026-06-09 | TN | 6 | 128 | Historial de Enfermeria importado |
| GUIÑAZU KARINA | 2026-06-09 | M | 6 | 128 | Historial de Enfermeria importado |
| LUCERO MATIAS | 2026-06-09 | T | 6 | 128 | Historial de Enfermeria importado |
| MAÑE LORENA | 2026-06-09 | MT | 12 | 128 | Historial de Enfermeria importado |
| MEDINA LAURA | 2026-06-09 | TN | 6 | 128 | Historial de Enfermeria importado |
| MIRANDA YANINA | 2026-06-09 | N | 6 | 128 | Historial de Enfermeria importado |
| NIEVAS CARLA | 2026-06-09 | TNN | 12 | 128 | Historial de Enfermeria importado |
| ORTIZ LAURA | 2026-06-09 | T | 6 | 128 | Historial de Enfermeria importado |
| PALANA GRACIELA | 2026-06-09 | N | 6 | 128 | Historial de Enfermeria importado |
| QUEVEDO CELESTE | 2026-06-09 | M | 6 | 128 | Historial de Enfermeria importado |
| ROJAS JULIANA | 2026-06-09 | M | 6 | 128 | Historial de Enfermeria importado |
| SUAREZ JESICA | 2026-06-09 | TN | 6 | 128 | Historial de Enfermeria importado |
| TULA DAIANA | 2026-06-09 | MT | 12 | 128 | Historial de Enfermeria importado |
| VELEZ DANIEL | 2026-06-09 | T | 6 | 128 | Historial de Enfermeria importado |
| VELIZ LIONEL | 2026-06-09 | N | 6 | 128 | Historial de Enfermeria importado |
| VERA JULIETA | 2026-06-09 | N | 6 | 128 | Historial de Enfermeria importado |
| ABELENDA GRISELL | 2026-06-10 | N | 6 | 128 | Historial de Enfermeria importado |
| ALBELO TANIA | 2026-06-10 | M | 6 | 128 | Historial de Enfermeria importado |
| ALCARAZ FRANCISO | 2026-06-10 | T | 6 | 128 | Historial de Enfermeria importado |
| ANDREOLI LUCIANA | 2026-06-10 | TNN | 12 | 128 | Historial de Enfermeria importado |
| BORIA MAYRA | 2026-06-10 | MT | 12 | 128 | Historial de Enfermeria importado |
| CALDERON MARIA JOSE | 2026-06-10 | N | 6 | 128 | Historial de Enfermeria importado |
| CAMPOS PRISCILA | 2026-06-10 | TN | 6 | 128 | Historial de Enfermeria importado |
| CASTRO LUCIANO | 2026-06-10 | MT | 12 | 128 | Historial de Enfermeria importado |
| CHIRINO CAROLINA | 2026-06-10 | N | 6 | 128 | Historial de Enfermeria importado |
| CORIA LUCIANO | 2026-06-10 | MT | 12 | 128 | Historial de Enfermeria importado |
| DURAN JAZMIN | 2026-06-10 | MT | 12 | 128 | Historial de Enfermeria importado |
| FERNANDEZ PAOLA | 2026-06-10 | TN | 6 | 128 | Historial de Enfermeria importado |
| FERNANDEZ YESICA | 2026-06-10 | TN | 6 | 128 | Historial de Enfermeria importado |
| GIMENEZ KAREN | 2026-06-10 | TNN | 12 | 128 | Historial de Enfermeria importado |
| GOMES STHEFANIA | 2026-06-10 | TNN | 12 | 128 | Historial de Enfermeria importado |
| GRABOVIECKI FERNANDA | 2026-06-10 | TN | 6 | 128 | Historial de Enfermeria importado |
| LUCERO MATIAS | 2026-06-10 | MT | 12 | 128 | Historial de Enfermeria importado |
| MEDINA LAURA | 2026-06-10 | TN | 6 | 128 | Historial de Enfermeria importado |
| MIRANDA YANINA | 2026-06-10 | N | 6 | 128 | Historial de Enfermeria importado |
| OLGUIN LUCIA | 2026-06-10 | TN | 6 | 128 | Historial de Enfermeria importado |
| ORTIZ LAURA | 2026-06-10 | MT | 12 | 128 | Historial de Enfermeria importado |
| PALACIOS FACUNDO | 2026-06-10 | T | 6 | 128 | Historial de Enfermeria importado |
| PEREIRA CRISTINA | 2026-06-10 | M | 6 | 128 | Historial de Enfermeria importado |
| QUEVEDO CELESTE | 2026-06-10 | MT | 12 | 128 | Historial de Enfermeria importado |
| SOSA NAHUEL | 2026-06-10 | T | 6 | 128 | Historial de Enfermeria importado |
| TULA DAIANA | 2026-06-10 | M | 6 | 128 | Historial de Enfermeria importado |
| VELEZ DANIEL | 2026-06-10 | T | 6 | 128 | Historial de Enfermeria importado |
| VELIZ LIONEL | 2026-06-10 | TNN | 12 | 128 | Historial de Enfermeria importado |
| VERA JULIETA | 2026-06-10 | N | 6 | 128 | Historial de Enfermeria importado |
| ALCARAZ FRANCISO | 2026-06-11 | T | 6 | 128 | Historial de Enfermeria importado |
| ANDREOLI LUCIANA | 2026-06-11 | N | 6 | 128 | Historial de Enfermeria importado |
| BARROSO ERICA | 2026-06-11 | M | 6 | 128 | Historial de Enfermeria importado |
| BASCUR ALEJANDRA | 2026-06-11 | MT | 12 | 128 | Historial de Enfermeria importado |
| BORIA MAYRA | 2026-06-11 | M | 6 | 128 | Historial de Enfermeria importado |
| CAMPOS PRISCILA | 2026-06-11 | TN | 6 | 128 | Historial de Enfermeria importado |
| CASTRO LUCIANO | 2026-06-11 | T | 6 | 128 | Historial de Enfermeria importado |
| CHIRINO CAROLINA | 2026-06-11 | TNN | 12 | 128 | Historial de Enfermeria importado |
| CORIA LUCIANO | 2026-06-11 | T | 6 | 128 | Historial de Enfermeria importado |
| DOMINGUEZ VERONICA | 2026-06-11 | TN | 6 | 128 | Historial de Enfermeria importado |
| DURAN JAZMIN | 2026-06-11 | T | 6 | 128 | Historial de Enfermeria importado |
| ESCALANTE CARLA | 2026-06-11 | MT | 12 | 128 | Historial de Enfermeria importado |
| FERNANDEZ PAOLA | 2026-06-11 | TNN | 12 | 128 | Historial de Enfermeria importado |
| FERNANDEZ YESICA | 2026-06-11 | TN | 6 | 128 | Historial de Enfermeria importado |
| GOMES STHEFANIA | 2026-06-11 | TN | 6 | 128 | Historial de Enfermeria importado |
| GRABOVIECKI FERNANDA | 2026-06-11 | TN | 6 | 128 | Historial de Enfermeria importado |
| GUIÑAZU KARINA | 2026-06-11 | M | 6 | 128 | Historial de Enfermeria importado |
| LUCERO MATIAS | 2026-06-11 | T | 6 | 128 | Historial de Enfermeria importado |
| MAÑE LORENA | 2026-06-11 | T | 6 | 128 | Historial de Enfermeria importado |
| MIRANDA LUCIANA | 2026-06-11 | N | 6 | 128 | Historial de Enfermeria importado |
| OLGUIN LUCIA | 2026-06-11 | TNN | 12 | 128 | Historial de Enfermeria importado |
| ORTIZ LAURA | 2026-06-11 | M | 6 | 128 | Historial de Enfermeria importado |
| PALACIOS FACUNDO | 2026-06-11 | MT | 12 | 128 | Historial de Enfermeria importado |
| PALANA GRACIELA | 2026-06-11 | N | 6 | 128 | Historial de Enfermeria importado |
| PEREIRA CRISTINA | 2026-06-11 | M | 6 | 128 | Historial de Enfermeria importado |
| POLETTI NATALIA | 2026-06-11 | MT | 12 | 128 | Historial de Enfermeria importado |
| ROJAS JULIANA | 2026-06-11 | TNN | 12 | 128 | Historial de Enfermeria importado |
| SOSA NAHUEL | 2026-06-11 | MT | 12 | 128 | Historial de Enfermeria importado |
| SUAREZ JESICA | 2026-06-11 | TNN | 12 | 128 | Historial de Enfermeria importado |
| VELIZ LIONEL | 2026-06-11 | N | 6 | 128 | Historial de Enfermeria importado |
| ABELENDA GRISELL | 2026-06-12 | N | 6 | 128 | Historial de Enfermeria importado |
| ALBELO TANIA | 2026-06-12 | MT | 12 | 128 | Historial de Enfermeria importado |
| ALCARAZ FRANCISO | 2026-06-12 | T | 6 | 128 | Historial de Enfermeria importado |
| ARCE DANIEL | 2026-06-12 | MT | 12 | 128 | Historial de Enfermeria importado |
| BARROSO ERICA | 2026-06-12 | MT | 12 | 128 | Historial de Enfermeria importado |
| BASCUR ALEJANDRA | 2026-06-12 | T | 6 | 128 | Historial de Enfermeria importado |
| BORIA MAYRA | 2026-06-12 | M | 6 | 128 | Historial de Enfermeria importado |
| CALDERON MARIA JOSE | 2026-06-12 | TNN | 12 | 128 | Historial de Enfermeria importado |
| CAMPOS PRISCILA | 2026-06-12 | TN | 6 | 128 | Historial de Enfermeria importado |
| CHIRINO CAROLINA | 2026-06-12 | N | 6 | 128 | Historial de Enfermeria importado |
| CORSO ARTURO | 2026-06-12 | M | 6 | 128 | Historial de Enfermeria importado |
| DOMINGUEZ VERONICA | 2026-06-12 | TN | 6 | 128 | Historial de Enfermeria importado |
| ECHENIQUE ROCIO | 2026-06-12 | TNN | 12 | 128 | Historial de Enfermeria importado |
| ESCALANTE CARLA | 2026-06-12 | M | 6 | 128 | Historial de Enfermeria importado |
| ESCUDERO SERGIO | 2026-06-12 | MT | 12 | 128 | Historial de Enfermeria importado |
| FERNANDEZ PAOLA | 2026-06-12 | TN | 6 | 128 | Historial de Enfermeria importado |
| GRABOVIECKI FERNANDA | 2026-06-12 | TNN | 12 | 128 | Historial de Enfermeria importado |
| GUIÑAZU KARINA | 2026-06-12 | MT | 12 | 128 | Historial de Enfermeria importado |
| LUCERO MATIAS | 2026-06-12 | T | 6 | 128 | Historial de Enfermeria importado |
| MAÑE LORENA | 2026-06-12 | T | 6 | 128 | Historial de Enfermeria importado |
| MIRANDA LUCIANA | 2026-06-12 | TNN | 12 | 128 | Historial de Enfermeria importado |
| NIEVAS CARLA | 2026-06-12 | N | 6 | 128 | Historial de Enfermeria importado |
| OLGUIN LUCIA | 2026-06-12 | TN | 6 | 128 | Historial de Enfermeria importado |
| ORTIZ LAURA | 2026-06-12 | M | 6 | 128 | Historial de Enfermeria importado |
| PALACIOS FACUNDO | 2026-06-12 | T | 6 | 128 | Historial de Enfermeria importado |
| PALANA GRACIELA | 2026-06-12 | TN | 6 | 128 | Historial de Enfermeria importado |
| PEREIRA CRISTINA | 2026-06-12 | M | 6 | 128 | Historial de Enfermeria importado |
| ROJAS JULIANA | 2026-06-12 | N | 6 | 128 | Historial de Enfermeria importado |
| SOSA NAHUEL | 2026-06-12 | T | 6 | 128 | Historial de Enfermeria importado |
| SUAREZ JESICA | 2026-06-12 | TN | 6 | 128 | Historial de Enfermeria importado |
| ABELENDA GRISELL | 2026-06-13 | N | 6 | 128 | Historial de Enfermeria importado |
| ALBELO TANIA | 2026-06-13 | M | 6 | 128 | Historial de Enfermeria importado |
| ANDREOLI LUCIANA | 2026-06-13 | N | 6 | 128 | Historial de Enfermeria importado |
| ARCE DANIEL | 2026-06-13 | T | 6 | 128 | Historial de Enfermeria importado |
| CALDERON MARIA JOSE | 2026-06-13 | N | 6 | 128 | Historial de Enfermeria importado |
| CASTRO LUCIANO | 2026-06-13 | T | 6 | 128 | Historial de Enfermeria importado |
| CORIA LUCIANO | 2026-06-13 | T | 6 | 128 | Historial de Enfermeria importado |
| CORSO ARTURO | 2026-06-13 | M | 6 | 128 | Historial de Enfermeria importado |
| DURAN JAZMIN | 2026-06-13 | T | 6 | 128 | Historial de Enfermeria importado |
| ECHENIQUE ROCIO | 2026-06-13 | TN | 6 | 128 | Historial de Enfermeria importado |
| ESCUDERO SERGIO | 2026-06-13 | T | 6 | 128 | Historial de Enfermeria importado |
| GIMENEZ KAREN | 2026-06-13 | TN | 6 | 128 | Historial de Enfermeria importado |
| GOMES STHEFANIA | 2026-06-13 | TNN | 12 | 128 | Historial de Enfermeria importado |
| GRABOVIECKI FERNANDA | 2026-06-13 | TN | 6 | 128 | Historial de Enfermeria importado |
| GUIÑAZU KARINA | 2026-06-13 | M | 6 | 128 | Historial de Enfermeria importado |
| MEDINA LAURA | 2026-06-13 | TN | 6 | 128 | Historial de Enfermeria importado |
| MIRANDA LUCIANA | 2026-06-13 | N | 6 | 128 | Historial de Enfermeria importado |
| MIRANDA YANINA | 2026-06-13 | N | 6 | 128 | Historial de Enfermeria importado |
| NIEVAS CARLA | 2026-06-13 | N | 6 | 128 | Historial de Enfermeria importado |
| OLGUIN LUCIA | 2026-06-13 | TN | 6 | 128 | Historial de Enfermeria importado |
| POLETTI NATALIA | 2026-06-13 | MT | 12 | 128 | Historial de Enfermeria importado |
| QUEVEDO CELESTE | 2026-06-13 | M | 6 | 128 | Historial de Enfermeria importado |
| SOSA NAHUEL | 2026-06-13 | T | 6 | 128 | Historial de Enfermeria importado |
| TULA DAIANA | 2026-06-13 | M | 6 | 128 | Historial de Enfermeria importado |
| VELEZ DANIEL | 2026-06-13 | M | 6 | 128 | Historial de Enfermeria importado |
| VELIZ LIONEL | 2026-06-13 | N | 6 | 128 | Historial de Enfermeria importado |
| VERA JULIETA | 2026-06-13 | TNN | 12 | 128 | Historial de Enfermeria importado |
| ABELENDA GRISELL | 2026-06-14 | N | 6 | 128 | Historial de Enfermeria importado |
| ALBELO TANIA | 2026-06-14 | M | 6 | 128 | Historial de Enfermeria importado |
| ANDREOLI LUCIANA | 2026-06-14 | TN | 6 | 128 | Historial de Enfermeria importado |
| ARCE DANIEL | 2026-06-14 | T | 6 | 128 | Historial de Enfermeria importado |
| ASTUDILLO MELINA | 2026-06-14 | N | 6 | 128 | Historial de Enfermeria importado |
| BARROSO ERICA | 2026-06-14 | M | 6 | 128 | Historial de Enfermeria importado |
| BASCUR ALEJANDRA | 2026-06-14 | T | 6 | 128 | Historial de Enfermeria importado |
| CALDERON MARIA JOSE | 2026-06-14 | N | 6 | 128 | Historial de Enfermeria importado |
| CASTRO LUCIANO | 2026-06-14 | T | 6 | 128 | Historial de Enfermeria importado |
| CORIA LUCIANO | 2026-06-14 | T | 6 | 128 | Historial de Enfermeria importado |
| CORSO ARTURO | 2026-06-14 | M | 6 | 128 | Historial de Enfermeria importado |
| DURAN JAZMIN | 2026-06-14 | T | 6 | 128 | Historial de Enfermeria importado |
| ECHENIQUE ROCIO | 2026-06-14 | TN | 6 | 128 | Historial de Enfermeria importado |
| ESCUDERO SERGIO | 2026-06-14 | T | 6 | 128 | Historial de Enfermeria importado |
| FERNANDEZ YESICA | 2026-06-14 | TNN | 12 | 128 | Historial de Enfermeria importado |
| GIMENEZ KAREN | 2026-06-14 | TN | 6 | 128 | Historial de Enfermeria importado |
| GOMES STHEFANIA | 2026-06-14 | TN | 6 | 128 | Historial de Enfermeria importado |
| GRABOVIECKI FERNANDA | 2026-06-14 | TN | 6 | 128 | Historial de Enfermeria importado |
| MEDINA LAURA | 2026-06-14 | TN | 6 | 128 | Historial de Enfermeria importado |
| MIRANDA LUCIANA | 2026-06-14 | TNN | 12 | 128 | Historial de Enfermeria importado |
| MIRANDA YANINA | 2026-06-14 | N | 6 | 128 | Historial de Enfermeria importado |
| NIEVAS CARLA | 2026-06-14 | N | 6 | 128 | Historial de Enfermeria importado |
| PALACIOS FACUNDO | 2026-06-14 | M | 6 | 128 | Historial de Enfermeria importado |
| POLETTI NATALIA | 2026-06-14 | MT | 12 | 128 | Historial de Enfermeria importado |
| QUEVEDO CELESTE | 2026-06-14 | M | 6 | 128 | Historial de Enfermeria importado |
| SOSA NAHUEL | 2026-06-14 | T | 6 | 128 | Historial de Enfermeria importado |
| TULA DAIANA | 2026-06-14 | M | 6 | 128 | Historial de Enfermeria importado |
| VELEZ DANIEL | 2026-06-14 | M | 6 | 128 | Historial de Enfermeria importado |
| VELIZ LIONEL | 2026-06-14 | N | 6 | 128 | Historial de Enfermeria importado |
| VERA JULIETA | 2026-06-14 | N | 6 | 128 | Historial de Enfermeria importado |
| ABELENDA GRISELL | 2026-06-15 | TNN | 12 | 128 | Historial de Enfermeria importado |
| ALBELO TANIA | 2026-06-15 | N | 6 | 128 | Historial de Enfermeria importado |
| ALCARAZ ELIANA | 2026-06-15 | TNN | 12 | 128 | Historial de Enfermeria importado |
| ANDREOLI LUCIANA | 2026-06-15 | TN | 6 | 128 | Historial de Enfermeria importado |
| ASTUDILLO MELINA | 2026-06-15 | TN | 6 | 128 | Historial de Enfermeria importado |
| BARROSO ERICA | 2026-06-15 | N | 6 | 128 | Historial de Enfermeria importado |
| BASCUR ALEJANDRA | 2026-06-15 | M | 6 | 128 | Historial de Enfermeria importado |
| CALDERON MARIA JOSE | 2026-06-15 | TNN | 12 | 128 | Historial de Enfermeria importado |
| CARRERAS FLAVIA | 2026-06-15 | MT | 12 | 128 | Historial de Enfermeria importado |
| CASTRO LUCIANO | 2026-06-15 | MT | 12 | 128 | Historial de Enfermeria importado |
| CORIA LUCIANO | 2026-06-15 | M | 6 | 128 | Historial de Enfermeria importado |
| CORSO ARTURO | 2026-06-15 | N | 6 | 128 | Historial de Enfermeria importado |
| DURAN JAZMIN | 2026-06-15 | M | 6 | 128 | Historial de Enfermeria importado |
| ECHENIQUE ROCIO | 2026-06-15 | T | 6 | 128 | Historial de Enfermeria importado |
| ESCUDERO SERGIO | 2026-06-15 | M | 6 | 128 | Historial de Enfermeria importado |
| FERNANDEZ YESICA | 2026-06-15 | T | 6 | 128 | Historial de Enfermeria importado |
| GIMENEZ KAREN | 2026-06-15 | T | 6 | 128 | Historial de Enfermeria importado |
| GOMES STHEFANIA | 2026-06-15 | T | 6 | 128 | Historial de Enfermeria importado |
| GOMEZ LOURDES | 2026-06-15 | N | 6 | 128 | Historial de Enfermeria importado |
| GRABOVIECKI FERNANDA | 2026-06-15 | T | 6 | 128 | Historial de Enfermeria importado |
| MEDINA LAURA | 2026-06-15 | T | 6 | 128 | Historial de Enfermeria importado |
| MIRANDA LUCIANA | 2026-06-15 | TN | 6 | 128 | Historial de Enfermeria importado |
| MIRANDA YANINA | 2026-06-15 | TN | 6 | 128 | Historial de Enfermeria importado |
| MONDONE PAULA | 2026-06-15 | MT | 12 | 128 | Historial de Enfermeria importado |
| OLGUIN LUCIA | 2026-06-15 | MT | 12 | 128 | Historial de Enfermeria importado |
| PALACIOS FACUNDO | 2026-06-15 | M | 6 | 128 | Historial de Enfermeria importado |
| QUEVEDO CELESTE | 2026-06-15 | N | 6 | 128 | Historial de Enfermeria importado |
| RINALDINI IVANA | 2026-06-15 | TN | 6 | 128 | Historial de Enfermeria importado |
| VELIZ LIONEL | 2026-06-15 | TN | 6 | 128 | Historial de Enfermeria importado |
| VERA JULIETA | 2026-06-15 | TNN | 12 | 128 | Historial de Enfermeria importado |
| ALCARAZ ELIANA | 2026-06-16 | N | 6 | 128 | Historial de Enfermeria importado |
| ARCE DANIEL | 2026-06-16 | MT | 12 | 128 | Historial de Enfermeria importado |
| ASTUDILLO MELINA | 2026-06-16 | TNN | 12 | 128 | Historial de Enfermeria importado |
| BARROSO ERICA | 2026-06-16 | TNN | 12 | 128 | Historial de Enfermeria importado |
| BASCUR ALEJANDRA | 2026-06-16 | MT | 12 | 128 | Historial de Enfermeria importado |
| CALDERON MARIA JOSE | 2026-06-16 | TN | 6 | 128 | Historial de Enfermeria importado |
| CARRERAS FLAVIA | 2026-06-16 | T | 6 | 128 | Historial de Enfermeria importado |
| CASTRO LUCIANO | 2026-06-16 | M | 6 | 128 | Historial de Enfermeria importado |
| CORIA LUCIANO | 2026-06-16 | M | 6 | 128 | Historial de Enfermeria importado |
| ECHENIQUE ROCIO | 2026-06-16 | MT | 12 | 128 | Historial de Enfermeria importado |
| FERNANDEZ YESICA | 2026-06-16 | MT | 12 | 128 | Historial de Enfermeria importado |
| GIMENEZ KAREN | 2026-06-16 | MT | 12 | 128 | Historial de Enfermeria importado |
| GOMEZ LOURDES | 2026-06-16 | N | 6 | 128 | Historial de Enfermeria importado |
| GUIÑAZU KARINA | 2026-06-16 | N | 6 | 128 | Historial de Enfermeria importado |
| MEDINA LAURA | 2026-06-16 | T | 6 | 128 | Historial de Enfermeria importado |
| MIRANDA YANINA | 2026-06-16 | TNN | 12 | 128 | Historial de Enfermeria importado |
| MONDONE PAULA | 2026-06-16 | T | 6 | 128 | Historial de Enfermeria importado |
| NIEVAS CARLA | 2026-06-16 | TN | 6 | 128 | Historial de Enfermeria importado |
| OLGUIN LUCIA | 2026-06-16 | T | 6 | 128 | Historial de Enfermeria importado |
| PALACIOS FACUNDO | 2026-06-16 | M | 6 | 128 | Historial de Enfermeria importado |
| QUEVEDO CELESTE | 2026-06-16 | N | 6 | 128 | Historial de Enfermeria importado |
| RINALDINI IVANA | 2026-06-16 | TNN | 12 | 128 | Historial de Enfermeria importado |
| TULA DAIANA | 2026-06-16 | TNN | 12 | 128 | Historial de Enfermeria importado |
| VELEZ DANIEL | 2026-06-16 | MT | 12 | 128 | Historial de Enfermeria importado |
| VELIZ LIONEL | 2026-06-16 | TNN | 12 | 128 | Historial de Enfermeria importado |
| VERA JULIETA | 2026-06-16 | TN | 6 | 128 | Historial de Enfermeria importado |
| ALBELO TANIA | 2026-06-17 | N | 6 | 128 | Historial de Enfermeria importado |
| ALCARAZ ELIANA | 2026-06-17 | N | 6 | 128 | Historial de Enfermeria importado |
| ALCARAZ FRANCISO | 2026-06-17 | M | 6 | 128 | Historial de Enfermeria importado |
| ARCE DANIEL | 2026-06-17 | M | 6 | 128 | Historial de Enfermeria importado |
| ASTUDILLO MELINA | 2026-06-17 | TN | 6 | 128 | Historial de Enfermeria importado |
| BORIA MAYRA | 2026-06-17 | T | 6 | 128 | Historial de Enfermeria importado |
| CARRERAS FLAVIA | 2026-06-17 | T | 6 | 128 | Historial de Enfermeria importado |
| CASTRO LUCIANO | 2026-06-17 | M | 6 | 128 | Historial de Enfermeria importado |
| CHIRINO CAROLINA | 2026-06-17 | TNN | 12 | 128 | Historial de Enfermeria importado |
| CORIA LUCIANO | 2026-06-17 | M | 6 | 128 | Historial de Enfermeria importado |
| CORSO ARTURO | 2026-06-17 | TNN | 12 | 128 | Historial de Enfermeria importado |
| DURAN JAZMIN | 2026-06-17 | MT | 12 | 128 | Historial de Enfermeria importado |
| ECHENIQUE ROCIO | 2026-06-17 | T | 6 | 128 | Historial de Enfermeria importado |
| ESCALANTE CARLA | 2026-06-17 | N | 6 | 128 | Historial de Enfermeria importado |
| ESCUDERO SERGIO | 2026-06-17 | M | 6 | 128 | Historial de Enfermeria importado |
| FERNANDEZ PAOLA | 2026-06-17 | T | 6 | 128 | Historial de Enfermeria importado |
| FERNANDEZ YESICA | 2026-06-17 | T | 6 | 128 | Historial de Enfermeria importado |
| GOMES STHEFANIA | 2026-06-17 | MT | 12 | 128 | Historial de Enfermeria importado |
| GOMEZ LOURDES | 2026-06-17 | TNN | 12 | 128 | Historial de Enfermeria importado |
| GRABOVIECKI FERNANDA | 2026-06-17 | MT | 12 | 128 | Historial de Enfermeria importado |
| NIEVAS CARLA | 2026-06-17 | TNN | 12 | 128 | Historial de Enfermeria importado |
| OLGUIN LUCIA | 2026-06-17 | T | 6 | 128 | Historial de Enfermeria importado |
| ORTIZ LAURA | 2026-06-17 | N | 6 | 128 | Historial de Enfermeria importado |
| PALACIOS FACUNDO | 2026-06-17 | M | 6 | 128 | Historial de Enfermeria importado |
| QUEVEDO CELESTE | 2026-06-17 | TNN | 12 | 128 | Historial de Enfermeria importado |
| RINALDINI IVANA | 2026-06-17 | TN | 6 | 128 | Historial de Enfermeria importado |
| ROJAS JULIANA | 2026-06-17 | TN | 6 | 128 | Historial de Enfermeria importado |
| SOSA NAHUEL | 2026-06-17 | T | 6 | 128 | Historial de Enfermeria importado |
| VELEZ DANIEL | 2026-06-17 | M | 6 | 128 | Historial de Enfermeria importado |
| VERA JULIETA | 2026-06-17 | TN | 6 | 128 | Historial de Enfermeria importado |
| ABELENDA GRISELL | 2026-06-18 | TN | 6 | 128 | Historial de Enfermeria importado |
| ALBELO TANIA | 2026-06-18 | TNN | 12 | 128 | Historial de Enfermeria importado |
| ALCARAZ FRANCISO | 2026-06-18 | M | 6 | 128 | Historial de Enfermeria importado |
| ANDREOLI LUCIANA | 2026-06-18 | TNN | 12 | 128 | Historial de Enfermeria importado |
| ARCE DANIEL | 2026-06-18 | M | 6 | 128 | Historial de Enfermeria importado |
| CALDERON MARIA JOSE | 2026-06-18 | TN | 6 | 128 | Historial de Enfermeria importado |
| CHIRINO CAROLINA | 2026-06-18 | N | 6 | 128 | Historial de Enfermeria importado |
| CORSO ARTURO | 2026-06-18 | N | 6 | 128 | Historial de Enfermeria importado |
| DURAN JAZMIN | 2026-06-18 | M | 6 | 128 | Historial de Enfermeria importado |
| ESCUDERO SERGIO | 2026-06-18 | MT | 12 | 128 | Historial de Enfermeria importado |
| FERNANDEZ PAOLA | 2026-06-18 | MT | 12 | 128 | Historial de Enfermeria importado |
| GIMENEZ KAREN | 2026-06-18 | MT | 12 | 128 | Historial de Enfermeria importado |
| GOMES STHEFANIA | 2026-06-18 | T | 6 | 128 | Historial de Enfermeria importado |
| GRABOVIECKI FERNANDA | 2026-06-18 | T | 6 | 128 | Historial de Enfermeria importado |
| GUIÑAZU KARINA | 2026-06-18 | N | 6 | 128 | Historial de Enfermeria importado |
| MEDINA LAURA | 2026-06-18 | T | 6 | 128 | Historial de Enfermeria importado |
| MIRANDA LUCIANA | 2026-06-18 | TNN | 12 | 128 | Historial de Enfermeria importado |
| MIRANDA YANINA | 2026-06-18 | TN | 6 | 128 | Historial de Enfermeria importado |
| MONDONE PAULA | 2026-06-18 | T | 6 | 128 | Historial de Enfermeria importado |
| NIEVAS CARLA | 2026-06-18 | TN | 6 | 128 | Historial de Enfermeria importado |
| ORTIZ LAURA | 2026-06-18 | TNN | 12 | 128 | Historial de Enfermeria importado |
| PALACIOS FACUNDO | 2026-06-18 | MT | 12 | 128 | Historial de Enfermeria importado |
| POLETTI NATALIA | 2026-06-18 | N | 6 | 128 | Historial de Enfermeria importado |
| ROJAS JULIANA | 2026-06-18 | TN | 6 | 128 | Historial de Enfermeria importado |
| SOSA NAHUEL | 2026-06-18 | MT | 12 | 128 | Historial de Enfermeria importado |
| TULA DAIANA | 2026-06-18 | N | 6 | 128 | Historial de Enfermeria importado |
| VELEZ DANIEL | 2026-06-18 | M | 6 | 128 | Historial de Enfermeria importado |
| VELIZ LIONEL | 2026-06-18 | TN | 6 | 128 | Historial de Enfermeria importado |
| ABELENDA GRISELL | 2026-06-19 | TN | 6 | 128 | Historial de Enfermeria importado |
| ALBELO TANIA | 2026-06-19 | N | 6 | 128 | Historial de Enfermeria importado |
| ALCARAZ ELIANA | 2026-06-19 | N | 6 | 128 | Historial de Enfermeria importado |
| ALCARAZ FRANCISO | 2026-06-19 | MT | 12 | 128 | Historial de Enfermeria importado |
| ANDREOLI LUCIANA | 2026-06-19 | TN | 6 | 128 | Historial de Enfermeria importado |
| ARCE DANIEL | 2026-06-19 | M | 6 | 128 | Historial de Enfermeria importado |
| BARROSO ERICA | 2026-06-19 | T | 6 | 128 | Historial de Enfermeria importado |
| BASCUR ALEJANDRA | 2026-06-19 | M | 6 | 128 | Historial de Enfermeria importado |
| BORIA MAYRA | 2026-06-19 | TNN | 12 | 128 | Historial de Enfermeria importado |
| CALDERON MARIA JOSE | 2026-06-19 | TN | 6 | 128 | Historial de Enfermeria importado |
| CHIRINO CAROLINA | 2026-06-19 | N | 6 | 128 | Historial de Enfermeria importado |
| CORIA LUCIANO | 2026-06-19 | MT | 12 | 128 | Historial de Enfermeria importado |
| CORSO ARTURO | 2026-06-19 | N | 6 | 128 | Historial de Enfermeria importado |
| ESCALANTE CARLA | 2026-06-19 | TNN | 12 | 128 | Historial de Enfermeria importado |
| ESCUDERO SERGIO | 2026-06-19 | M | 6 | 128 | Historial de Enfermeria importado |
| FERNANDEZ PAOLA | 2026-06-19 | T | 6 | 128 | Historial de Enfermeria importado |
| GIMENEZ KAREN | 2026-06-19 | T | 6 | 128 | Historial de Enfermeria importado |
| GOMES STHEFANIA | 2026-06-19 | T | 6 | 128 | Historial de Enfermeria importado |
| GOMEZ LOURDES | 2026-06-19 | N | 6 | 128 | Historial de Enfermeria importado |
| GRABOVIECKI FERNANDA | 2026-06-19 | T | 6 | 128 | Historial de Enfermeria importado |
| GUIÑAZU KARINA | 2026-06-19 | TNN | 12 | 128 | Historial de Enfermeria importado |
| MEDINA LAURA | 2026-06-19 | MT | 12 | 128 | Historial de Enfermeria importado |
| MIRANDA LUCIANA | 2026-06-19 | TN | 6 | 128 | Historial de Enfermeria importado |
| MIRANDA YANINA | 2026-06-19 | TN | 6 | 128 | Historial de Enfermeria importado |
| NIEVAS CARLA | 2026-06-19 | TN | 6 | 128 | Historial de Enfermeria importado |
| PALACIOS FACUNDO | 2026-06-19 | M | 6 | 128 | Historial de Enfermeria importado |
| ROJAS JULIANA | 2026-06-19 | TNN | 12 | 128 | Historial de Enfermeria importado |
| SOSA NAHUEL | 2026-06-19 | M | 6 | 128 | Historial de Enfermeria importado |
| TULA DAIANA | 2026-06-19 | N | 6 | 128 | Historial de Enfermeria importado |
| VELEZ DANIEL | 2026-06-19 | M | 6 | 128 | Historial de Enfermeria importado |
| VELIZ LIONEL | 2026-06-19 | T | 6 | 128 | Historial de Enfermeria importado |
| ABELENDA GRISELL | 2026-06-20 | TN | 6 | 128 | Historial de Enfermeria importado |
| ALCARAZ ELIANA | 2026-06-20 | N | 6 | 128 | Historial de Enfermeria importado |
| ALCARAZ FRANCISO | 2026-06-20 | M | 6 | 128 | Historial de Enfermeria importado |
| ANDREOLI LUCIANA | 2026-06-20 | TN | 6 | 128 | Historial de Enfermeria importado |
| ASTUDILLO MELINA | 2026-06-20 | TN | 6 | 128 | Historial de Enfermeria importado |
| BARROSO ERICA | 2026-06-20 | N | 6 | 128 | Historial de Enfermeria importado |
| BASCUR ALEJANDRA | 2026-06-20 | M | 6 | 128 | Historial de Enfermeria importado |
| BORIA MAYRA | 2026-06-20 | N | 6 | 128 | Historial de Enfermeria importado |
| CARRERAS FLAVIA | 2026-06-20 | M | 6 | 128 | Historial de Enfermeria importado |
| CHIRINO CAROLINA | 2026-06-20 | TN | 6 | 128 | Historial de Enfermeria importado |
| CORIA LUCIANO | 2026-06-20 | M | 6 | 128 | Historial de Enfermeria importado |
| DURAN JAZMIN | 2026-06-20 | M | 6 | 128 | Historial de Enfermeria importado |
| ESCALANTE CARLA | 2026-06-20 | N | 6 | 128 | Historial de Enfermeria importado |
| FERNANDEZ PAOLA | 2026-06-20 | T | 6 | 128 | Historial de Enfermeria importado |
| FERNANDEZ YESICA | 2026-06-20 | T | 6 | 128 | Historial de Enfermeria importado |
| GOMES STHEFANIA | 2026-06-20 | T | 6 | 128 | Historial de Enfermeria importado |
| GOMEZ LOURDES | 2026-06-20 | N | 6 | 128 | Historial de Enfermeria importado |
| GRABOVIECKI FERNANDA | 2026-06-20 | M | 6 | 128 | Historial de Enfermeria importado |
| GUIÑAZU KARINA | 2026-06-20 | N | 6 | 128 | Historial de Enfermeria importado |
| MEDINA LAURA | 2026-06-20 | T | 6 | 128 | Historial de Enfermeria importado |
| MIRANDA LUCIANA | 2026-06-20 | TN | 6 | 128 | Historial de Enfermeria importado |
| MONDONE PAULA | 2026-06-20 | T | 6 | 128 | Historial de Enfermeria importado |
| OLGUIN LUCIA | 2026-06-20 | T | 6 | 128 | Historial de Enfermeria importado |
| ORTIZ LAURA | 2026-06-20 | N | 6 | 128 | Historial de Enfermeria importado |
| POLETTI NATALIA | 2026-06-20 | MT | 12 | 128 | Historial de Enfermeria importado |
| QUEVEDO CELESTE | 2026-06-20 | N | 6 | 128 | Historial de Enfermeria importado |
| RINALDINI IVANA | 2026-06-20 | TNN | 12 | 128 | Historial de Enfermeria importado |
| ROJAS JULIANA | 2026-06-20 | TN | 6 | 128 | Historial de Enfermeria importado |
| SOSA NAHUEL | 2026-06-20 | M | 6 | 128 | Historial de Enfermeria importado |
| TULA DAIANA | 2026-06-20 | N | 6 | 128 | Historial de Enfermeria importado |
| VERA JULIETA | 2026-06-20 | TN | 6 | 128 | Historial de Enfermeria importado |
| ABELENDA GRISELL | 2026-06-21 | TN | 6 | 128 | Historial de Enfermeria importado |
| ALCARAZ ELIANA | 2026-06-21 | N | 6 | 128 | Historial de Enfermeria importado |
| ALCARAZ FRANCISO | 2026-06-21 | M | 6 | 128 | Historial de Enfermeria importado |
| ANDREOLI LUCIANA | 2026-06-21 | TN | 6 | 128 | Historial de Enfermeria importado |
| ASTUDILLO MELINA | 2026-06-21 | TN | 6 | 128 | Historial de Enfermeria importado |
| BARROSO ERICA | 2026-06-21 | N | 6 | 128 | Historial de Enfermeria importado |
| BASCUR ALEJANDRA | 2026-06-21 | M | 6 | 128 | Historial de Enfermeria importado |
| BORIA MAYRA | 2026-06-21 | N | 6 | 128 | Historial de Enfermeria importado |
| CARRERAS FLAVIA | 2026-06-21 | T | 6 | 128 | Historial de Enfermeria importado |
| CASTRO LUCIANO | 2026-06-21 | M | 6 | 128 | Historial de Enfermeria importado |
| CHIRINO CAROLINA | 2026-06-21 | TN | 6 | 128 | Historial de Enfermeria importado |
| CORIA LUCIANO | 2026-06-21 | M | 6 | 128 | Historial de Enfermeria importado |
| DURAN JAZMIN | 2026-06-21 | M | 6 | 128 | Historial de Enfermeria importado |
| ECHENIQUE ROCIO | 2026-06-21 | T | 6 | 128 | Historial de Enfermeria importado |
| ESCALANTE CARLA | 2026-06-21 | N | 6 | 128 | Historial de Enfermeria importado |
| FERNANDEZ YESICA | 2026-06-21 | T | 6 | 128 | Historial de Enfermeria importado |
| GOMEZ LOURDES | 2026-06-21 | N | 6 | 128 | Historial de Enfermeria importado |
| GUIÑAZU KARINA | 2026-06-21 | N | 6 | 128 | Historial de Enfermeria importado |
| MAÑE LORENA | 2026-06-21 | M | 6 | 128 | Historial de Enfermeria importado |
| MEDINA LAURA | 2026-06-21 | T | 6 | 128 | Historial de Enfermeria importado |
| MIRANDA LUCIANA | 2026-06-21 | TN | 6 | 128 | Historial de Enfermeria importado |
| MONDONE PAULA | 2026-06-21 | T | 6 | 128 | Historial de Enfermeria importado |
| OLGUIN LUCIA | 2026-06-21 | T | 6 | 128 | Historial de Enfermeria importado |
| ORTIZ LAURA | 2026-06-21 | N | 6 | 128 | Historial de Enfermeria importado |
| POLETTI NATALIA | 2026-06-21 | MT | 12 | 128 | Historial de Enfermeria importado |
| QUEVEDO CELESTE | 2026-06-21 | N | 6 | 128 | Historial de Enfermeria importado |
| RINALDINI IVANA | 2026-06-21 | TN | 6 | 128 | Historial de Enfermeria importado |
| ROJAS JULIANA | 2026-06-21 | TN | 6 | 128 | Historial de Enfermeria importado |
| SOSA NAHUEL | 2026-06-21 | M | 6 | 128 | Historial de Enfermeria importado |
| TULA DAIANA | 2026-06-21 | N | 6 | 128 | Historial de Enfermeria importado |
| VERA JULIETA | 2026-06-21 | TN | 6 | 128 | Historial de Enfermeria importado |
| ALCARAZ FRANCISO | 2026-06-22 | N | 6 | 128 | Historial de Enfermeria importado |
| ANDREOLI LUCIANA | 2026-06-22 | T | 6 | 128 | Historial de Enfermeria importado |
| ASTUDILLO MELINA | 2026-06-22 | T | 6 | 128 | Historial de Enfermeria importado |
| BARROSO ERICA | 2026-06-22 | TN | 6 | 128 | Historial de Enfermeria importado |
| BASCUR ALEJANDRA | 2026-06-22 | N | 6 | 128 | Historial de Enfermeria importado |
| BORIA MAYRA | 2026-06-22 | TNN | 12 | 128 | Historial de Enfermeria importado |
| CARRERAS FLAVIA | 2026-06-22 | M | 6 | 128 | Historial de Enfermeria importado |
| CASTRO LUCIANO | 2026-06-22 | TNN | 12 | 128 | Historial de Enfermeria importado |
| CHIRINO CAROLINA | 2026-06-22 | T | 6 | 128 | Historial de Enfermeria importado |
| CORIA LUCIANO | 2026-06-22 | TNN | 12 | 128 | Historial de Enfermeria importado |
| DURAN JAZMIN | 2026-06-22 | TNN | 12 | 128 | Historial de Enfermeria importado |
| ECHENIQUE ROCIO | 2026-06-22 | MT | 12 | 128 | Historial de Enfermeria importado |
| ESCALANTE CARLA | 2026-06-22 | TNN | 12 | 128 | Historial de Enfermeria importado |
| FERNANDEZ PAOLA | 2026-06-22 | MT | 12 | 128 | Historial de Enfermeria importado |
| FERNANDEZ YESICA | 2026-06-22 | M | 6 | 128 | Historial de Enfermeria importado |
| GOMES STHEFANIA | 2026-06-22 | M | 6 | 128 | Historial de Enfermeria importado |
| GOMEZ LOURDES | 2026-06-22 | TNN | 12 | 128 | Historial de Enfermeria importado |
| GRABOVIECKI FERNANDA | 2026-06-22 | M | 6 | 128 | Historial de Enfermeria importado |
| MAÑE LORENA | 2026-06-22 | N | 6 | 128 | Historial de Enfermeria importado |
| MEDINA LAURA | 2026-06-22 | M | 6 | 128 | Historial de Enfermeria importado |
| MIRANDA LUCIANA | 2026-06-22 | MT | 12 | 128 | Historial de Enfermeria importado |
| OLGUIN LUCIA | 2026-06-22 | MT | 12 | 128 | Historial de Enfermeria importado |
| ORTIZ LAURA | 2026-06-22 | TN | 6 | 128 | Historial de Enfermeria importado |
| QUEVEDO CELESTE | 2026-06-22 | TN | 6 | 128 | Historial de Enfermeria importado |
| RINALDINI IVANA | 2026-06-22 | T | 6 | 128 | Historial de Enfermeria importado |
| VERA JULIETA | 2026-06-22 | T | 6 | 128 | Historial de Enfermeria importado |
| ABELENDA GRISELL | 2026-06-23 | T | 6 | 128 | Historial de Enfermeria importado |
| ANDREOLI LUCIANA | 2026-06-23 | MT | 12 | 128 | Historial de Enfermeria importado |
| ASTUDILLO MELINA | 2026-06-23 | MT | 12 | 128 | Historial de Enfermeria importado |
| BASCUR ALEJANDRA | 2026-06-23 | TNN | 12 | 128 | Historial de Enfermeria importado |
| BORIA MAYRA | 2026-06-23 | TN | 6 | 128 | Historial de Enfermeria importado |
| CARRERAS FLAVIA | 2026-06-23 | M | 6 | 128 | Historial de Enfermeria importado |
| CASTRO LUCIANO | 2026-06-23 | N | 6 | 128 | Historial de Enfermeria importado |
| CORIA LUCIANO | 2026-06-23 | N | 6 | 128 | Historial de Enfermeria importado |
| DURAN JAZMIN | 2026-06-23 | N | 6 | 128 | Historial de Enfermeria importado |
| ECHENIQUE ROCIO | 2026-06-23 | M | 6 | 128 | Historial de Enfermeria importado |
| ESCALANTE CARLA | 2026-06-23 | TN | 6 | 128 | Historial de Enfermeria importado |
| FERNANDEZ YESICA | 2026-06-23 | MT | 12 | 128 | Historial de Enfermeria importado |
| GIMENEZ KAREN | 2026-06-23 | T | 6 | 128 | Historial de Enfermeria importado |
| GOMES STHEFANIA | 2026-06-23 | MT | 12 | 128 | Historial de Enfermeria importado |
| GRABOVIECKI FERNANDA | 2026-06-23 | MT | 12 | 128 | Historial de Enfermeria importado |
| GUIÑAZU KARINA | 2026-06-23 | TNN | 12 | 128 | Historial de Enfermeria importado |
| MAÑE LORENA | 2026-06-23 | TNN | 12 | 128 | Historial de Enfermeria importado |
| MEDINA LAURA | 2026-06-23 | MT | 12 | 128 | Historial de Enfermeria importado |
| OLGUIN LUCIA | 2026-06-23 | M | 6 | 128 | Historial de Enfermeria importado |
| ORTIZ LAURA | 2026-06-23 | TNN | 12 | 128 | Historial de Enfermeria importado |
| POLETTI NATALIA | 2026-06-23 | TNN | 12 | 128 | Historial de Enfermeria importado |
| QUEVEDO CELESTE | 2026-06-23 | TN | 6 | 128 | Historial de Enfermeria importado |
| RINALDINI IVANA | 2026-06-23 | MT | 12 | 128 | Historial de Enfermeria importado |
| SOSA NAHUEL | 2026-06-23 | N | 6 | 128 | Historial de Enfermeria importado |
| TULA DAIANA | 2026-06-23 | TNN | 12 | 128 | Historial de Enfermeria importado |
| VERA JULIETA | 2026-06-23 | T | 6 | 128 | Historial de Enfermeria importado |
| ABELENDA GRISELL | 2026-06-24 | MT | 12 | 128 | Historial de Enfermeria importado |
| ALBELO TANIA | 2026-06-24 | T | 6 | 128 | Historial de Enfermeria importado |
| ALCARAZ ELIANA | 2026-06-24 | TNN | 12 | 128 | Historial de Enfermeria importado |
| ARCE DANIEL | 2026-06-24 | TNN | 12 | 128 | Historial de Enfermeria importado |
| BARROSO ERICA | 2026-06-24 | TNN | 12 | 128 | Historial de Enfermeria importado |
| CALDERON MARIA JOSE | 2026-06-24 | MT | 12 | 128 | Historial de Enfermeria importado |
| CARRERAS FLAVIA | 2026-06-24 | MT | 12 | 128 | Historial de Enfermeria importado |
| CHIRINO CAROLINA | 2026-06-24 | MT | 12 | 128 | Historial de Enfermeria importado |
| CORSO ARTURO | 2026-06-24 | TN | 6 | 128 | Historial de Enfermeria importado |
| DURAN JAZMIN | 2026-06-24 | N | 6 | 128 | Historial de Enfermeria importado |
| ESCUDERO SERGIO | 2026-06-24 | TNN | 12 | 128 | Historial de Enfermeria importado |
| FERNANDEZ YESICA | 2026-06-24 | M | 6 | 128 | Historial de Enfermeria importado |
| GIMENEZ KAREN | 2026-06-24 | MT | 12 | 128 | Historial de Enfermeria importado |
| GOMES STHEFANIA | 2026-06-24 | M | 6 | 128 | Historial de Enfermeria importado |
| GUIÑAZU KARINA | 2026-06-24 | TN | 6 | 128 | Historial de Enfermeria importado |
| MIRANDA LUCIANA | 2026-06-24 | T | 6 | 128 | Historial de Enfermeria importado |
| MIRANDA YANINA | 2026-06-24 | MT | 12 | 128 | Historial de Enfermeria importado |
| MONDONE PAULA | 2026-06-24 | M | 6 | 128 | Historial de Enfermeria importado |
| PALACIOS FACUNDO | 2026-06-24 | TNN | 12 | 128 | Historial de Enfermeria importado |
| POLETTI NATALIA | 2026-06-24 | TNN | 12 | 128 | Historial de Enfermeria importado |
| ROJAS JULIANA | 2026-06-24 | T | 6 | 128 | Historial de Enfermeria importado |
| SOSA NAHUEL | 2026-06-24 | TNN | 12 | 128 | Historial de Enfermeria importado |
| TULA DAIANA | 2026-06-24 | TN | 6 | 128 | Historial de Enfermeria importado |
| VELEZ DANIEL | 2026-06-24 | TNN | 12 | 128 | Historial de Enfermeria importado |
| VELIZ LIONEL | 2026-06-24 | T | 6 | 128 | Historial de Enfermeria importado |
| ABELENDA GRISELL | 2026-06-25 | T | 6 | 128 | Historial de Enfermeria importado |
| ALBELO TANIA | 2026-06-25 | TN | 6 | 128 | Historial de Enfermeria importado |
| ALCARAZ ELIANA | 2026-06-25 | TN | 6 | 128 | Historial de Enfermeria importado |
| ALCARAZ FRANCISO | 2026-06-25 | TNN | 12 | 128 | Historial de Enfermeria importado |
| ANDREOLI LUCIANA | 2026-06-25 | T | 6 | 128 | Historial de Enfermeria importado |
| ARCE DANIEL | 2026-06-25 | N | 6 | 128 | Historial de Enfermeria importado |
| BARROSO ERICA | 2026-06-25 | TN | 6 | 128 | Historial de Enfermeria importado |
| BASCUR ALEJANDRA | 2026-06-25 | N | 6 | 128 | Historial de Enfermeria importado |
| CALDERON MARIA JOSE | 2026-06-25 | T | 6 | 128 | Historial de Enfermeria importado |
| CASTRO LUCIANO | 2026-06-25 | N | 6 | 128 | Historial de Enfermeria importado |
| CHIRINO CAROLINA | 2026-06-25 | T | 6 | 128 | Historial de Enfermeria importado |
| CORIA LUCIANO | 2026-06-25 | N | 6 | 128 | Historial de Enfermeria importado |
| CORSO ARTURO | 2026-06-25 | TN | 6 | 128 | Historial de Enfermeria importado |
| ECHENIQUE ROCIO | 2026-06-25 | M | 6 | 128 | Historial de Enfermeria importado |
| ESCUDERO SERGIO | 2026-06-25 | N | 6 | 128 | Historial de Enfermeria importado |
| FERNANDEZ PAOLA | 2026-06-25 | M | 6 | 128 | Historial de Enfermeria importado |
| FERNANDEZ YESICA | 2026-06-25 | M | 6 | 128 | Historial de Enfermeria importado |
| GIMENEZ KAREN | 2026-06-25 | M | 6 | 128 | Historial de Enfermeria importado |
| GOMEZ LOURDES | 2026-06-25 | TN | 6 | 128 | Historial de Enfermeria importado |
| GUIÑAZU KARINA | 2026-06-25 | TN | 6 | 128 | Historial de Enfermeria importado |
| MEDINA LAURA | 2026-06-25 | M | 6 | 128 | Historial de Enfermeria importado |
| MIRANDA LUCIANA | 2026-06-25 | T | 6 | 128 | Historial de Enfermeria importado |
| MIRANDA YANINA | 2026-06-25 | T | 6 | 128 | Historial de Enfermeria importado |
| MONDONE PAULA | 2026-06-25 | MT | 12 | 128 | Historial de Enfermeria importado |
| ORTIZ LAURA | 2026-06-25 | TN | 6 | 128 | Historial de Enfermeria importado |
| PALACIOS FACUNDO | 2026-06-25 | N | 6 | 128 | Historial de Enfermeria importado |
| QUEVEDO CELESTE | 2026-06-25 | TNN | 12 | 128 | Historial de Enfermeria importado |
| ROJAS JULIANA | 2026-06-25 | MT | 12 | 128 | Historial de Enfermeria importado |
| SOSA NAHUEL | 2026-06-25 | N | 6 | 128 | Historial de Enfermeria importado |
| TULA DAIANA | 2026-06-25 | TN | 6 | 128 | Historial de Enfermeria importado |
| VELIZ LIONEL | 2026-06-25 | MT | 12 | 128 | Historial de Enfermeria importado |
| VERA JULIETA | 2026-06-25 | MT | 12 | 128 | Historial de Enfermeria importado |
| ABELENDA GRISELL | 2026-06-26 | T | 6 | 128 | Historial de Enfermeria importado |
| ALBELO TANIA | 2026-06-26 | TNN | 12 | 128 | Historial de Enfermeria importado |
| ALCARAZ ELIANA | 2026-06-26 | TN | 6 | 128 | Historial de Enfermeria importado |
| ALCARAZ FRANCISO | 2026-06-26 | N | 6 | 128 | Historial de Enfermeria importado |
| ANDREOLI LUCIANA | 2026-06-26 | T | 6 | 128 | Historial de Enfermeria importado |
| ARCE DANIEL | 2026-06-26 | N | 6 | 128 | Historial de Enfermeria importado |
| ASTUDILLO MELINA | 2026-06-26 | T | 6 | 128 | Historial de Enfermeria importado |
| BARROSO ERICA | 2026-06-26 | TN | 6 | 128 | Historial de Enfermeria importado |
| BASCUR ALEJANDRA | 2026-06-26 | TN | 6 | 128 | Historial de Enfermeria importado |
| BORIA MAYRA | 2026-06-26 | TN | 6 | 128 | Historial de Enfermeria importado |
| CALDERON MARIA JOSE | 2026-06-26 | T | 6 | 128 | Historial de Enfermeria importado |
| CASTRO LUCIANO | 2026-06-26 | TN | 6 | 128 | Historial de Enfermeria importado |
| CHIRINO CAROLINA | 2026-06-26 | T | 6 | 128 | Historial de Enfermeria importado |
| CORIA LUCIANO | 2026-06-26 | N | 6 | 128 | Historial de Enfermeria importado |
| CORSO ARTURO | 2026-06-26 | TNN | 12 | 128 | Historial de Enfermeria importado |
| DURAN JAZMIN | 2026-06-26 | N | 6 | 128 | Historial de Enfermeria importado |
| ECHENIQUE ROCIO | 2026-06-26 | M | 6 | 128 | Historial de Enfermeria importado |
| ESCALANTE CARLA | 2026-06-26 | T | 6 | 128 | Historial de Enfermeria importado |
| FERNANDEZ PAOLA | 2026-06-26 | M | 6 | 128 | Historial de Enfermeria importado |
| GIMENEZ KAREN | 2026-06-26 | M | 6 | 128 | Historial de Enfermeria importado |
| GOMEZ LOURDES | 2026-06-26 | TN | 6 | 128 | Historial de Enfermeria importado |
| GRABOVIECKI FERNANDA | 2026-06-26 | M | 6 | 128 | Historial de Enfermeria importado |
| MAÑE LORENA | 2026-06-26 | N | 6 | 128 | Historial de Enfermeria importado |
| MEDINA LAURA | 2026-06-26 | M | 6 | 128 | Historial de Enfermeria importado |
| MIRANDA LUCIANA | 2026-06-26 | T | 6 | 128 | Historial de Enfermeria importado |
| MIRANDA YANINA | 2026-06-26 | T | 6 | 128 | Historial de Enfermeria importado |
| MONDONE PAULA | 2026-06-26 | M | 6 | 128 | Historial de Enfermeria importado |
| OLGUIN LUCIA | 2026-06-26 | M | 6 | 128 | Historial de Enfermeria importado |
| ORTIZ LAURA | 2026-06-26 | TN | 6 | 128 | Historial de Enfermeria importado |
| QUEVEDO CELESTE | 2026-06-26 | TN | 6 | 128 | Historial de Enfermeria importado |
| RINALDINI IVANA | 2026-06-26 | T | 6 | 128 | Historial de Enfermeria importado |
| ROJAS JULIANA | 2026-06-26 | M | 6 | 128 | Historial de Enfermeria importado |
| SOSA NAHUEL | 2026-06-26 | N | 6 | 128 | Historial de Enfermeria importado |
| TULA DAIANA | 2026-06-26 | TN | 6 | 128 | Historial de Enfermeria importado |
| VELEZ DANIEL | 2026-06-26 | N | 6 | 128 | Historial de Enfermeria importado |
| VELIZ LIONEL | 2026-06-26 | T | 6 | 128 | Historial de Enfermeria importado |
| VERA JULIETA | 2026-06-26 | M | 6 | 128 | Historial de Enfermeria importado |
| ALBELO TANIA | 2026-06-27 | TN | 6 | 128 | Historial de Enfermeria importado |
| ALCARAZ ELIANA | 2026-06-27 | TN | 6 | 128 | Historial de Enfermeria importado |
| ALCARAZ FRANCISO | 2026-06-27 | N | 6 | 128 | Historial de Enfermeria importado |
| ANDREOLI LUCIANA | 2026-06-27 | TNN | 12 | 128 | Historial de Enfermeria importado |
| ARCE DANIEL | 2026-06-27 | N | 6 | 128 | Historial de Enfermeria importado |
| ASTUDILLO MELINA | 2026-06-27 | T | 6 | 128 | Historial de Enfermeria importado |
| CALDERON MARIA JOSE | 2026-06-27 | T | 6 | 128 | Historial de Enfermeria importado |
| CARRERAS FLAVIA | 2026-06-27 | M | 6 | 128 | Historial de Enfermeria importado |
| CORSO ARTURO | 2026-06-27 | TN | 6 | 128 | Historial de Enfermeria importado |
| DURAN JAZMIN | 2026-06-27 | N | 6 | 128 | Historial de Enfermeria importado |
| ESCALANTE CARLA | 2026-06-27 | TN | 6 | 128 | Historial de Enfermeria importado |
| ESCUDERO SERGIO | 2026-06-27 | N | 6 | 128 | Historial de Enfermeria importado |
| FERNANDEZ PAOLA | 2026-06-27 | M | 6 | 128 | Historial de Enfermeria importado |
| GIMENEZ KAREN | 2026-06-27 | M | 6 | 128 | Historial de Enfermeria importado |
| GOMES STHEFANIA | 2026-06-27 | M | 6 | 128 | Historial de Enfermeria importado |
| GOMEZ LOURDES | 2026-06-27 | TN | 6 | 128 | Historial de Enfermeria importado |
| GRABOVIECKI FERNANDA | 2026-06-27 | M | 6 | 128 | Historial de Enfermeria importado |
| MAÑE LORENA | 2026-06-27 | N | 6 | 128 | Historial de Enfermeria importado |
| MIRANDA YANINA | 2026-06-27 | T | 6 | 128 | Historial de Enfermeria importado |
| MONDONE PAULA | 2026-06-27 | M | 6 | 128 | Historial de Enfermeria importado |
| OLGUIN LUCIA | 2026-06-27 | M | 6 | 128 | Historial de Enfermeria importado |
| ORTIZ LAURA | 2026-06-27 | TN | 6 | 128 | Historial de Enfermeria importado |
| PALACIOS FACUNDO | 2026-06-27 | N | 6 | 128 | Historial de Enfermeria importado |
| RINALDINI IVANA | 2026-06-27 | T | 6 | 128 | Historial de Enfermeria importado |
| ROJAS JULIANA | 2026-06-27 | T | 6 | 128 | Historial de Enfermeria importado |
| VELEZ DANIEL | 2026-06-27 | N | 6 | 128 | Historial de Enfermeria importado |
| VELIZ LIONEL | 2026-06-27 | T | 6 | 128 | Historial de Enfermeria importado |
| ALBELO TANIA | 2026-06-28 | TN | 6 | 128 | Historial de Enfermeria importado |
| ALCARAZ ELIANA | 2026-06-28 | TN | 6 | 128 | Historial de Enfermeria importado |
| ALCARAZ FRANCISO | 2026-06-28 | N | 6 | 128 | Historial de Enfermeria importado |
| ARCE DANIEL | 2026-06-28 | N | 6 | 128 | Historial de Enfermeria importado |
| ASTUDILLO MELINA | 2026-06-28 | T | 6 | 128 | Historial de Enfermeria importado |
| BORIA MAYRA | 2026-06-28 | TN | 6 | 128 | Historial de Enfermeria importado |
| CALDERON MARIA JOSE | 2026-06-28 | T | 6 | 128 | Historial de Enfermeria importado |
| CARRERAS FLAVIA | 2026-06-28 | M | 6 | 128 | Historial de Enfermeria importado |
| CHIRINO CAROLINA | 2026-06-28 | T | 6 | 128 | Historial de Enfermeria importado |
| CORSO ARTURO | 2026-06-28 | TN | 6 | 128 | Historial de Enfermeria importado |
| ESCUDERO SERGIO | 2026-06-28 | N | 6 | 128 | Historial de Enfermeria importado |
| FERNANDEZ PAOLA | 2026-06-28 | M | 6 | 128 | Historial de Enfermeria importado |
| GIMENEZ KAREN | 2026-06-28 | M | 6 | 128 | Historial de Enfermeria importado |
| GOMES STHEFANIA | 2026-06-28 | M | 6 | 128 | Historial de Enfermeria importado |
| GOMEZ LOURDES | 2026-06-28 | TN | 6 | 128 | Historial de Enfermeria importado |
| GRABOVIECKI FERNANDA | 2026-06-28 | M | 6 | 128 | Historial de Enfermeria importado |
| MAÑE LORENA | 2026-06-28 | TNN | 12 | 128 | Historial de Enfermeria importado |
| MONDONE PAULA | 2026-06-28 | M | 6 | 128 | Historial de Enfermeria importado |
| NIEVAS CARLA | 2026-06-28 | T | 6 | 128 | Historial de Enfermeria importado |
| OLGUIN LUCIA | 2026-06-28 | M | 6 | 128 | Historial de Enfermeria importado |
| PALACIOS FACUNDO | 2026-06-28 | N | 6 | 128 | Historial de Enfermeria importado |
| POLETTI NATALIA | 2026-06-28 | TNN | 12 | 128 | Historial de Enfermeria importado |
| RINALDINI IVANA | 2026-06-28 | T | 6 | 128 | Historial de Enfermeria importado |
| ROJAS JULIANA | 2026-06-28 | T | 6 | 128 | Historial de Enfermeria importado |
| VELEZ DANIEL | 2026-06-28 | N | 6 | 128 | Historial de Enfermeria importado |
| VELIZ LIONEL | 2026-06-28 | T | 6 | 128 | Historial de Enfermeria importado |
| ANDREOLI LUCIANA | 2026-06-29 | MT | 12 | 128 | Historial de Enfermeria importado |
| ARCE DANIEL | 2026-06-29 | TN | 6 | 128 | Historial de Enfermeria importado |
| ASTUDILLO MELINA | 2026-06-29 | M | 6 | 128 | Historial de Enfermeria importado |
| BORIA MAYRA | 2026-06-29 | T | 6 | 128 | Historial de Enfermeria importado |
| CARRERAS FLAVIA | 2026-06-29 | N | 6 | 128 | Historial de Enfermeria importado |
| CHIRINO CAROLINA | 2026-06-29 | M | 6 | 128 | Historial de Enfermeria importado |
| CORSO ARTURO | 2026-06-29 | T | 6 | 128 | Historial de Enfermeria importado |
| DURAN JAZMIN | 2026-06-29 | TN | 6 | 128 | Historial de Enfermeria importado |
| ESCALANTE CARLA | 2026-06-29 | MT | 12 | 128 | Historial de Enfermeria importado |
| ESCUDERO SERGIO | 2026-06-29 | TN | 6 | 128 | Historial de Enfermeria importado |
| FERNANDEZ PAOLA | 2026-06-29 | TNN | 12 | 128 | Historial de Enfermeria importado |
| GOMES STHEFANIA | 2026-06-29 | N | 6 | 128 | Historial de Enfermeria importado |
| MAÑE LORENA | 2026-06-29 | TNN | 12 | 128 | Historial de Enfermeria importado |
| MIRANDA YANINA | 2026-06-29 | M | 6 | 128 | Historial de Enfermeria importado |
| MONDONE PAULA | 2026-06-29 | TNN | 12 | 128 | Historial de Enfermeria importado |
| NIEVAS CARLA | 2026-06-29 | MT | 12 | 128 | Historial de Enfermeria importado |
| OLGUIN LUCIA | 2026-06-29 | N | 6 | 128 | Historial de Enfermeria importado |
| ORTIZ LAURA | 2026-06-29 | T | 6 | 128 | Historial de Enfermeria importado |
| PALACIOS FACUNDO | 2026-06-29 | TN | 6 | 128 | Historial de Enfermeria importado |
| RINALDINI IVANA | 2026-06-29 | M | 6 | 128 | Historial de Enfermeria importado |
| ROJAS JULIANA | 2026-06-29 | M | 6 | 128 | Historial de Enfermeria importado |
| VELEZ DANIEL | 2026-06-29 | TN | 6 | 128 | Historial de Enfermeria importado |
| VELIZ LIONEL | 2026-06-29 | M | 6 | 128 | Historial de Enfermeria importado |
| ALBELO TANIA | 2026-06-30 | T | 6 | 128 | Historial de Enfermeria importado |
| ALCARAZ ELIANA | 2026-06-30 | T | 6 | 128 | Historial de Enfermeria importado |
| ANDREOLI LUCIANA | 2026-06-30 | M | 6 | 128 | Historial de Enfermeria importado |
| ASTUDILLO MELINA | 2026-06-30 | M | 6 | 128 | Historial de Enfermeria importado |
| BORIA MAYRA | 2026-06-30 | MT | 12 | 128 | Historial de Enfermeria importado |
| CALDERON MARIA JOSE | 2026-06-30 | M | 6 | 128 | Historial de Enfermeria importado |
| CAMPOS PRISCILA | 2026-06-30 | TNN | 12 | 128 | Historial de Enfermeria importado |
| CARRERAS FLAVIA | 2026-06-30 | N | 6 | 128 | Historial de Enfermeria importado |
| DOMINGUEZ VERONICA | 2026-06-30 | TNN | 12 | 128 | Historial de Enfermeria importado |
| DURAN JAZMIN | 2026-06-30 | TN | 6 | 128 | Historial de Enfermeria importado |
| ESCALANTE CARLA | 2026-06-30 | T | 6 | 128 | Historial de Enfermeria importado |
| ESCUDERO SERGIO | 2026-06-30 | TN | 6 | 128 | Historial de Enfermeria importado |
| FERNANDEZ YESICA | 2026-06-30 | TNN | 12 | 128 | Historial de Enfermeria importado |
| GIMENEZ KAREN | 2026-06-30 | N | 6 | 128 | Historial de Enfermeria importado |
| GOMES STHEFANIA | 2026-06-30 | TN | 6 | 128 | Historial de Enfermeria importado |
| GOMEZ LOURDES | 2026-06-30 | T | 6 | 128 | Historial de Enfermeria importado |
| GRABOVIECKI FERNANDA | 2026-06-30 | N | 6 | 128 | Historial de Enfermeria importado |
| LUCERO MATIAS | 2026-06-30 | TNN | 12 | 128 | Historial de Enfermeria importado |
| MAÑE LORENA | 2026-06-30 | TN | 6 | 128 | Historial de Enfermeria importado |
| NIEVAS CARLA | 2026-06-30 | M | 6 | 128 | Historial de Enfermeria importado |
| OLGUIN LUCIA | 2026-06-30 | N | 6 | 128 | Historial de Enfermeria importado |
| ORTIZ LAURA | 2026-06-30 | T | 6 | 128 | Historial de Enfermeria importado |
| PALANA GRACIELA | 2026-06-30 | MT | 12 | 128 | Historial de Enfermeria importado |
| PEREIRA CRISTINA | 2026-06-30 | MT | 12 | 128 | Historial de Enfermeria importado |
| RINALDINI IVANA | 2026-06-30 | M | 6 | 128 | Historial de Enfermeria importado |
| VELEZ DANIEL | 2026-06-30 | TN | 6 | 128 | Historial de Enfermeria importado |

## 4. Demanda y Oferta de Turnos

### Demanda Base (Vacantes Requeridas)

| Puesto | Tipo Día | Hora Inicio | Hora Fin | Mínimo | Máximo | Días Habilitados |
| --- | --- | --- | --- | --- | --- | --- |
| UTI | Finde_Feriado | 00:00 | 06:00 | 6 | 7 | - |
| UTI | Finde_Feriado | 06:00 | 12:00 | 7 | 10 | - |
| UTI | Finde_Feriado | 12:00 | 18:00 | 9 | 14 | - |
| UTI | Finde_Feriado | 18:00 | 00:00 | 7 | 10 | - |
| UTI | Semana | 00:00 | 06:00 | 7 | 8 | - |
| UTI | Semana | 06:00 | 12:00 | 8 | 12 | - |
| UTI | Semana | 12:00 | 18:00 | 10 | 14 | - |
| UTI | Semana | 18:00 | 00:00 | 8 | 10 | - |

### Ajustes Temporales de Demanda

*(Sin ajustes de demanda activos en este período)*

### Oferta de Turnos Configurada

| Turno | Hora Inicio | Horas | Días Semana | Puesto | Orden |
| --- | --- | --- | --- | --- | --- |
| M | 06:00 | 6 | 0,1,2,3,4,5,6 | UTI | 1 |
| T | 12:00 | 6 | 0,1,2,3,4,5,6 | UTI | 2 |
| TN | 18:00 | 6 | 0,1,2,3,4,5,6 | UTI | 3 |
| N | 00:00 | 6 | 0,1,2,3,4,5,6 | UTI | 4 |
| MT | 06:00 | 12 | 0,1,2,3,4,5,6 | UTI | 6 |

### Ajustes Temporales de Turnos / Vacantes

*(Sin ajustes temporales de turnos activos en este período)*


SELECT * FROM reglas_catalogo
INNER JOIN servicios_reglas 
    ON reglas_catalogo.id = servicios_reglas.regla_id
INNER JOIN personal_reglas 
    ON reglas_catalogo.id = personal_reglas.regla_id
INNER JOIN personal_reglas_ajustes 
    ON reglas_catalogo.codigo_regla = personal_reglas_ajustes.codigo_regla
WHERE servicios_reglas.servicio_id = 2;
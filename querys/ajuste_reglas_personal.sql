SELECT 
    pra.id,
    pra.personal_nombre AS nombre,
    p.rol,
    p.servicio_id,
    pra.codigo_regla,
    pra.fecha_inicio,
    pra.fecha_fin,
    pra.accion,
    pra.parametros_json,
    pra.activo
FROM personal_reglas_ajustes pra
JOIN personal p ON pra.personal_nombre = p.nombre
WHERE p.servicio_id = 3;

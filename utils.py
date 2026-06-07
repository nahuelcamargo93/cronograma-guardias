def time_to_float(t_str: str) -> float:
    """Convierte un string de hora 'HH:MM' a float (ej: '14:30' -> 14.5)."""
    if not t_str:
        return 0.0
    try:
        h, m = map(int, t_str.split(':'))
        return h + m / 60.0
    except ValueError:
        return 0.0


def obtener_nombre_archivo(base_name: str, fecha_inicio_str: str, ext: str = None) -> str:
    """
    Genera el nombre de archivo con el sufijo '_mesaño' en español.
    Ej: 'Cronograma_Servicio_Kinesiologia' y '2026-08-01' -> 'Cronograma_Servicio_Kinesiologia_Agosto26.xlsx' (si ext='xlsx')
    """
    import os
    import datetime

    base, existing_ext = os.path.splitext(base_name)
    if existing_ext:
        if not ext:
            ext = existing_ext.lstrip('.')
        base_name = base
        
    try:
        dt = datetime.datetime.strptime(fecha_inicio_str, "%Y-%m-%d")
    except Exception:
        try:
            dt = datetime.date.fromisoformat(fecha_inicio_str)
        except Exception:
            dt = datetime.datetime.now()
            
    meses = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
        7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }
    mes_str = meses.get(dt.month, "Mes")
    anio_str = dt.strftime("%y")
    
    suffix = f"_{mes_str}{anio_str}"
    
    ext_str = f".{ext}" if ext else ""
    return f"{base_name}{suffix}{ext_str}"


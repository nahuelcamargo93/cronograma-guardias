def time_to_float(t_str: str) -> float:
    """Convierte un string de hora 'HH:MM' a float (ej: '14:30' -> 14.5)."""
    if not t_str:
        return 0.0
    try:
        h, m = map(int, t_str.split(':'))
        return h + m / 60.0
    except ValueError:
        return 0.0

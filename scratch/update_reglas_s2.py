import sys
sys.path.insert(0, r'c:\Users\asus\Desktop\Ryoko\cronograma_inteligente')
from database.connection import get_connection

with get_connection() as conn:
    conn.execute(
        "UPDATE servicios_reglas SET activo=0 WHERE servicio_id=2 AND codigo_regla='NO_REPETIR_N_CONSECUTIVO'"
    )
    # Verificar
    rows = conn.execute(
        "SELECT codigo_regla, activo FROM servicios_reglas WHERE servicio_id=2 AND codigo_regla IN ('NO_REPETIR_N_CONSECUTIVO','REGLA_REPETICION_TIPO_SEMANA')"
    ).fetchall()
    for r in rows:
        print(f"  {r[0]}: activo={r[1]}")

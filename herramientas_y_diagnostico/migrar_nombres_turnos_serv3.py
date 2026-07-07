"""
migrar_nombres_turnos_serv3.py
-------------------------------
Migración one-shot: renombra los turnos del servicio 3 (Médicos) del formato
corto (G_Planta, D_Planta, N_Planta, ...) al formato largo que usa Google Sheets
(Guardia_Planta, Dia_Planta, Noche_Planta, ...).

Tablas afectadas:
  - turnos_config          (nombre)
  - personal_asignaciones_fijas (turno)
  - guardias               (turno)

Ejecutar UNA SOLA VEZ. Es idempotente: si los nombres ya están migrados, no hace nada.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database.connection import get_connection

MAPA = {
    "G_Planta":    "Guardia_Planta",
    "D_Planta":    "Dia_Planta",
    "N_Planta":    "Noche_Planta",
    "G_Residente": "Guardia_Residente",
    "D_Residente": "Dia_Residente",
    "N_Residente": "Noche_Residente",
}

SERVICIO_ID = 3

def main():
    print("=" * 60)
    print("  MIGRACIÓN: Renombrar turnos servicio 3")
    print("=" * 60)

    with get_connection() as conn:
        for viejo, nuevo in MAPA.items():

            # 1. turnos_config
            cur = conn.execute(
                "UPDATE turnos_config SET nombre = ? WHERE servicio_id = ? AND nombre = ?",
                (nuevo, SERVICIO_ID, viejo)
            )
            if cur.rowcount:
                print(f"  [turnos_config]           {viejo!r:20s} -> {nuevo!r}")

            # 2. personal_asignaciones_fijas
            cur = conn.execute(
                "UPDATE personal_asignaciones_fijas SET turno = ? WHERE servicio_id = ? AND turno = ?",
                (nuevo, SERVICIO_ID, viejo)
            )
            if cur.rowcount:
                print(f"  [asignaciones_fijas] x{cur.rowcount:<2}  {viejo!r:20s} -> {nuevo!r}")

            # 3. guardias
            cur = conn.execute(
                """UPDATE guardias SET turno = ?
                   WHERE turno = ?
                     AND cronograma_id IN (SELECT id FROM cronogramas WHERE servicio_id = ?)""",
                (nuevo, viejo, SERVICIO_ID)
            )
            if cur.rowcount:
                print(f"  [guardias]           x{cur.rowcount:<2}  {viejo!r:20s} -> {nuevo!r}")

    print()
    print("[OK] Migración finalizada.")
    print("=" * 60)


if __name__ == "__main__":
    main()

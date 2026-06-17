"""
traductor.py — Capa de traducción bidireccional string <-> ID numérico.

Responsabilidad única: leer la DB para un servicio_id y exponer
diccionarios en memoria que aislan al motor de OR-Tools de los strings
de negocio. El motor solo ve enteros y atributos matemáticos puros.
"""
from .connection import get_connection


class Traductor:
    """Mapeo bidireccional para un servicio específico.

    Atributos públicos (todos de solo lectura tras __init__):
      emp_id   : {nombre_str -> int}
      id_emp   : {int -> nombre_str}
      turno_id : {nombre_str -> int}
      id_turno : {int -> nombre_str}
      puesto_id: {nombre_str -> int}
      id_puesto: {int -> nombre_str}
      turno_meta: {turno_id_int -> {"horas": int, "hora_inicio": str,
                                     "puesto_id": int, "dias_semana": list[int]}}
    """

    def __init__(self, servicio_id: int):
        self.servicio_id = servicio_id
        self._cargar()

    # ------------------------------------------------------------------
    # Carga
    # ------------------------------------------------------------------
    def _cargar(self):
        sid = self.servicio_id
        with get_connection() as conn:
            # 1. Empleados activos del servicio
            rows = conn.execute(
                "SELECT rowid, nombre FROM personal WHERE servicio_id = ? AND activo = 1",
                (sid,)
            ).fetchall()
            # Usamos índice secuencial (0-based) para el motor
            self.emp_id:  dict[str, int] = {}
            self.id_emp:  dict[int, str] = {}
            for i, (_, nombre) in enumerate(rows):
                self.emp_id[nombre] = i
                self.id_emp[i]      = nombre

            # 2. Puestos del servicio
            rows = conn.execute(
                "SELECT id, nombre FROM puestos WHERE servicio_id = ?", (sid,)
            ).fetchall()
            self.puesto_id: dict[str, int] = {n: db_id for db_id, n in rows}
            self.id_puesto: dict[int, str] = {db_id: n  for db_id, n in rows}

            # 3. Turnos activos del servicio + metadata matemática
            rows = conn.execute("""
                SELECT tc.id, tc.nombre, tc.horas, tc.hora_inicio,
                       tc.puesto_id, tc.dias_semana
                FROM turnos_config tc
                WHERE tc.servicio_id = ? AND tc.activo = 1
                ORDER BY tc.orden
            """, (sid,)).fetchall()

            self.turno_id:  dict[str, int] = {}
            self.id_turno:  dict[int, str] = {}
            self.turno_meta: dict[int, dict] = {}

            for i, (db_id, nombre, horas, hora_inicio, p_id, dias_str) in enumerate(rows):
                self.turno_id[nombre] = i
                self.id_turno[i]      = nombre
                dias = [int(d) for d in dias_str.split(",")] if dias_str else list(range(7))
                self.turno_meta[i] = {
                    "horas":       horas,
                    "hora_inicio": hora_inicio,
                    "puesto_id":   p_id,         # ID numérico de puestos tabla
                    "dias_semana": dias,
                }

    # ------------------------------------------------------------------
    # Helpers de consulta rápida
    # ------------------------------------------------------------------
    def horas_turno(self, turno_id: int) -> int:
        return self.turno_meta[turno_id]["horas"]

    def puesto_de_turno(self, turno_id: int) -> int:
        """Retorna el puesto_id (numérico) del turno."""
        return self.turno_meta[turno_id]["puesto_id"]

    def dias_validos_turno(self, turno_id: int) -> list:
        return self.turno_meta[turno_id]["dias_semana"]

    def n_empleados(self) -> int:
        return len(self.emp_id)

    def n_turnos(self) -> int:
        return len(self.turno_id)

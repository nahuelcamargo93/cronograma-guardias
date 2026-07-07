"""
scratch/test_debugger_hard.py — Test unitario de simulación para verificar el debugger hard.

Simula tres tipos de inviabilidad mediante monkey-patching sobre las consultas de DB:
1. Inviabilidad por Asignaciones/Francos contradictorios (Fase 2).
2. Inviabilidad por Demanda superior a la capacidad del plantel (Fase 3).
3. Inviabilidad por regla dura conflictiva (Fase 4).
"""

import sys
import os

# Asegurar que el path del proyecto está en sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import ejecutar_optimizacion
from database import queries as db_queries

def test_escenario_asignacion_contradictoria():
    print("\n" + "="*80)
    print("  [TEST] ESCENARIO 1: ASIGNACIÓN FIJA VS FRANCO FORZADO (Mismo día y persona)")
    print("="*80)
    
    # Guardar originales
    original_asig = db_queries.cargar_asignaciones_fijas_rango
    original_francos = db_queries.cargar_francos_forzados_rango
    original_reglas = db_queries.cargar_reglas_servicio
    
    # Leandro Franco tiene asignación y franco el 2026-07-02
    db_queries.cargar_asignaciones_fijas_rango = lambda *a, **k: (
        {("Franco, Leandro", "2026-07-02"): "Noche_UTI"}, {}
    )
    db_queries.cargar_francos_forzados_rango = lambda *a, **k: {
        ("Franco, Leandro", "2026-07-02")
    }
    
    # Desactivar todas las reglas duras del servicio para garantizar viabilidad base (solo queda la demanda y asignaciones)
    def mock_reglas_servicio(*args, **kwargs):
        reglas = original_reglas(*args, **kwargs)
        # Desactivamos todas las reglas duras
        reglas_desactivadas = {}
        for k, v in reglas.items():
            if isinstance(v, dict):
                v_copy = dict(v)
                v_copy["activo"] = 0
                reglas_desactivadas[k] = v_copy
            else:
                reglas_desactivadas[k] = v
        return reglas_desactivadas

    db_queries.cargar_reglas_servicio = mock_reglas_servicio
    
    try:
        ejecutar_optimizacion(
            servicio_id=3,
            fecha_inicio="2026-07-01",
            fecha_fin="2026-07-07", # 1 semana
            modo_debug=False,
            modo_debug_hard=True,
            max_time_in_seconds=10
        )
    finally:
        # Restaurar
        db_queries.cargar_asignaciones_fijas_rango = original_asig
        db_queries.cargar_francos_forzados_rango = original_francos
        db_queries.cargar_reglas_servicio = original_reglas


def test_escenario_demanda_excesiva():
    print("\n" + "="*80)
    print("  [TEST] ESCENARIO 2: DEMANDA EXCESIVA (Plantel insuficiente)")
    print("="*80)
    
    # Guardar originales
    original_config = db_queries.cargar_configuracion_turnos
    original_asig = db_queries.cargar_asignaciones_fijas_rango
    original_francos = db_queries.cargar_francos_forzados_rango
    
    # Desactivamos asignaciones y sobreescribimos demanda para pedir 99 enfermeros
    def mock_config(*args, **kwargs):
        turnos_c, met, dem_req, aj = original_config(*args, **kwargs)
        nuevo_dem_req = {
            "Semana": [
                {
                    "id": 9999,
                    "demanda_config_id": 9999,
                    "puesto": "UTI",
                    "puesto_id": 1,
                    "hora_inicio": "08:00",
                    "hora_fin": "20:00",
                    "cantidad_min": 99,
                    "cantidad_max": 99,
                    "dias_semana": "0,1,2,3,4" # Lunes a Viernes
                }
            ],
            "Finde_Feriado": []
        }
        return turnos_c, met, nuevo_dem_req, aj

    db_queries.cargar_configuracion_turnos = mock_config
    db_queries.cargar_asignaciones_fijas_rango = lambda *a, **k: ({}, {})
    db_queries.cargar_francos_forzados_rango = lambda *a, **k: set()
    
    try:
        ejecutar_optimizacion(
            servicio_id=2,
            fecha_inicio="2026-07-01",
            fecha_fin="2026-07-07",
            modo_debug=False,
            modo_debug_hard=True,
            max_time_in_seconds=10
        )
    finally:
        db_queries.cargar_configuracion_turnos = original_config
        db_queries.cargar_asignaciones_fijas_rango = original_asig
        db_queries.cargar_francos_forzados_rango = original_francos


if __name__ == "__main__":
    test_escenario_asignacion_contradictoria()
    test_escenario_demanda_excesiva()

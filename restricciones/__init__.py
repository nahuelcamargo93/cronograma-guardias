"""
restricciones/ — Paquete raíz del sistema de micro-reglas.

Estructura:
  /hard   → Leyes físicas (nunca flexibilizables)
  /soft   → Preferencias y equidad (penalizaciones en f. objetivo)
  /double → Límites configurables (HARD o SOFT según campo 'modo' en DB)

Contrato de cada micro-regla (aplica a los tres subpaquetes):
  Cada archivo debe exponer una función con la siguiente firma:

      def apply(modelo, ctx) -> None:
          ...

  Donde:
    - modelo : ortools.sat.python.cp_model.CpModel
    - ctx    : restricciones.contexto.ContextoModelo
               (contiene turnos, empleados, traductor, parámetros, etc.)

  El cargador dinámico (Tarea 2.5) importa y llama a apply() de forma
  genérica. Las reglas NO deben importar strings de negocio ni acceder
  a la DB directamente; solo consumen ctx.
"""

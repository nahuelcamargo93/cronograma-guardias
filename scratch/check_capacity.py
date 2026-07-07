import sqlite3
import pandas as pd

conn = sqlite3.connect('cronograma_inteligente.db')

print("=== Puestos del Servicio 2 ===")
df_puestos = pd.read_sql_query("SELECT id, nombre FROM puestos WHERE servicio_id = 2", conn)
print(df_puestos)

print("\n=== Personal habilitado por puesto para Servicio 2 ===")
df_personal_puestos = pd.read_sql_query("""
    SELECT p.nombre, p.rol, pt.nombre as puesto_habilitado
    FROM personal p
    JOIN personal_puestos pp ON p.nombre = pp.personal_nombre
    JOIN puestos pt ON pp.puesto_id = pt.id
    WHERE p.servicio_id = 2 AND COALESCE(p.activo, 1) = 1
    ORDER BY pt.nombre, p.nombre
""", conn)

puestos_counts = df_personal_puestos.groupby('puesto_habilitado').size().to_dict()
print(df_personal_puestos)
print("\nCantidad de personal habilitado por puesto:")
print(puestos_counts)

print("\n=== Demanda Config para Servicio 2 ===")
df_demanda = pd.read_sql_query("""
    SELECT dc.id, pt.nombre as puesto, dc.tipo_dia, dc.hora_inicio, dc.hora_fin, dc.cantidad_min, dc.cantidad_max, dc.dias_semana
    FROM demanda_config dc
    JOIN puestos pt ON dc.puesto_id = pt.id
    WHERE pt.servicio_id = 2 AND dc.activo = 1
""", conn)
print(df_demanda)

print("\n=== Ajustes de Demanda en Agosto 2026 ===")
df_ajustes_dem = pd.read_sql_query("""
    SELECT da.fecha_inicio, da.fecha_fin, pt.nombre as puesto, da.cantidad_min, da.cantidad_max
    FROM demanda_ajustes da
    JOIN demanda_config dc ON da.demanda_config_id = dc.id
    JOIN puestos pt ON dc.puesto_id = pt.id
    WHERE pt.servicio_id = 2 AND da.activo = 1
      AND da.fecha_inicio <= '2026-08-31' AND da.fecha_fin >= '2026-08-01'
""", conn)
print(df_ajustes_dem)

conn.close()

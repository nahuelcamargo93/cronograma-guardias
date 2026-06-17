import sqlite3
import json

DB_PATH = "c:/Users/asus/Desktop/Ryoko/cronograma_inteligente/cronograma_inteligente.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 1. Insertar en reglas_catalogo
regla_codigo = "ESQUEMA_SEMANAL_ENFERMERIA"
regla_tipo = "HARD"
regla_desc = "Esquema semanal fijo para Enfermería Servicio 2 (4 turnos de 6h y 1 de 12h condicional a semana activa)"

cursor.execute("""
    INSERT OR IGNORE INTO reglas_catalogo (codigo_regla, tipo, descripcion)
    VALUES (?, ?, ?)
""", (regla_codigo, regla_tipo, regla_desc))

# 2. Activar la regla para el Servicio 2 (Enfermería UTI, ID 2)
# Verifiquemos primero si el servicio con ID 2 existe
servicio = cursor.execute("SELECT id, nombre FROM servicios WHERE id = 2").fetchone()
if servicio:
    print(f"Servicio encontrado: {servicio[1]} (ID: {servicio[0]})")
    
    # Insertar o actualizar para activar
    cursor.execute("""
        INSERT INTO servicios_reglas (servicio_id, codigo_regla, parametros_json, activo)
        VALUES (?, ?, ?, 1)
        ON CONFLICT(servicio_id, codigo_regla) DO UPDATE SET activo = 1
    """, (servicio[0], regla_codigo, json.dumps({})))
    print("Regla ESQUEMA_SEMANAL_ENFERMERIA activada para el Servicio 2.")
else:
    print("Error: No se encontró el servicio con ID 2.")

conn.commit()
conn.close()
print("Base de datos actualizada correctamente.")

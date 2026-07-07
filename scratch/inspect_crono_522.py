import sqlite3
import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.queries import obtener_feriados

conn = sqlite3.connect("cronograma_inteligente.db")

crono_id = 522
print(f"=== INSPECCIONANDO CRONOGRAMA {crono_id} ===")

# Obtener metadata del crono
crono_info = conn.execute("SELECT fecha_inicio, fecha_fin, notas, estado FROM cronogramas WHERE id = ?", (crono_id,)).fetchone()
if not crono_info:
    print(f"No se encontró el cronograma {crono_id}")
    # Mostrar últimos cronos
    print("\nÚltimos cronogramas:")
    for row in conn.execute("SELECT id, fecha_inicio, fecha_fin, notas, estado FROM cronogramas ORDER BY id DESC LIMIT 5").fetchall():
        print(row)
    conn.close()
    exit()

print(f"Fecha inicio: {crono_info[0]}, Fin: {crono_info[1]}, Estado: {crono_info[3]}, Notas: {crono_info[2]}")

# Obtener guardias de servicio 4
guardias = conn.execute("""
    SELECT g.nombre, g.fecha, g.turno, g.es_finde, p.rol
    FROM guardias g
    JOIN personal p ON g.nombre = p.nombre
    WHERE g.cronograma_id = ? AND p.servicio_id = 4
    ORDER BY g.nombre, g.fecha
""", (crono_id,)).fetchall()

print(f"Total guardias servicio 4: {len(guardias)}")

# Feriados cargados en ese rango
# Busquemos los feriados para julio 2026 (o el rango del crono)
feriados_db = obtener_feriados(crono_info[0], crono_info[1], servicio_id=4)
feriados = set(feriados_db)
print(f"Feriados en el período: {feriados}")

# Estadísticas por persona
stats = {}
for nombre, fecha_str, turno, es_finde, rol in guardias:
    if nombre not in stats:
        stats[nombre] = {
            "rol": rol,
            "total_dias": 0,
            "findes": 0,
            "feriados": 0,
            "sabados": 0,
            "domingos": 0,
            "guardias_info": []
        }
    
    stats[nombre]["total_dias"] += 1
    stats[nombre]["guardias_info"].append((fecha_str, turno, es_finde))
    
    f_dt = datetime.date.fromisoformat(fecha_str)
    wd = f_dt.weekday()
    if wd == 5:
        stats[nombre]["sabados"] += 1
    elif wd == 6:
        stats[nombre]["domingos"] += 1
        
    if es_finde:
        stats[nombre]["findes"] += 1
    if fecha_str in feriados:
        stats[nombre]["feriados"] += 1

print("\n=== ESTADÍSTICAS DE FINES DE SEMANA Y FERIADOS ===")
for nombre, s in sorted(stats.items(), key=lambda x: x[0]):
    print(f"{nombre} ({s['rol']}): Total días={s['total_dias']}, Finde={s['findes']} (Sáb={s['sabados']}, Dom={s['domingos']}), Feriados={s['feriados']}")

# Consultar reglas de servicio 4 en la base de datos
print("\n=== REGLAS DEL SERVICIO 4 EN BD ===")
reglas = conn.execute("""
    SELECT codigo_regla, parametros_json, activo 
    FROM servicios_reglas 
    WHERE servicio_id = 4
""", ()).fetchall()
for codigo, params, activo in reglas:
    print(f"Regla: {codigo}, Activo: {activo}, Parámetros: {params}")

# Consultar si hay ajustes temporales de reglas del servicio 4 para este periodo
print("\n=== AJUSTES TEMPORALES DE REGLAS DE SERVICIO 4 ===")
ajustes = conn.execute("""
    SELECT codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo 
    FROM servicios_reglas_ajustes 
    WHERE servicio_id = 4
""", ()).fetchall()
for row in ajustes:
    print(row)

# Consultar infracciones registradas para crono 522
print("\n=== INFRACCIONES REGISTRADAS PARA CRONO 522 ===")
infracciones = conn.execute("""
    SELECT codigo_regla, etiqueta
    FROM infracciones
    WHERE cronograma_id = ?
""", (crono_id,)).fetchall()
for row in infracciones:
    print(row)

conn.close()

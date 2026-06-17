import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

crono_id = 261
nombre = 'BORIA MAYRA'

print(f"--- Guardias de {nombre} en Crono {crono_id} ---")
cursor.execute("""
    SELECT fecha, turno, horas 
    FROM guardias 
    WHERE cronograma_id = ? AND nombre = ?
    ORDER BY fecha
""", (crono_id, nombre))
guardias = cursor.fetchall()
for g in guardias:
    print(g)

# Obtener fecha de inicio y fin del cronograma
cursor.execute("SELECT fecha_inicio, fecha_fin FROM cronogramas WHERE id = ?", (crono_id,))
crono_info = cursor.fetchone()
print(f"Periodo: {crono_info}")

# Contar días totales y ver cuáles tiene libres
import datetime
f_ini = datetime.date.fromisoformat(crono_info[0])
f_fin = datetime.date.fromisoformat(crono_info[1])
total_dias = (f_fin - f_ini).days + 1

guardias_dict = {g[0]: g[1] for g in guardias}
dias_libres = []
for i in range(total_dias):
    f_actual = (f_ini + datetime.timedelta(days=i)).isoformat()
    if f_actual not in guardias_dict:
        dia_sem = (i + f_ini.weekday()) % 7
        dias_libres.append((i, f_actual, dia_sem))

print(f"\nDías libres de {nombre}:")
# Buscar rachas de 4 días libres que comiencen un jueves (3) o sábado (5)
for i, f_actual, dia_sem in dias_libres:
    print(f"Día {i} ({f_actual}) - Sem: {dia_sem}")

conn.close()

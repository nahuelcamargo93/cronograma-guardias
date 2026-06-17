import sqlite3
from datetime import date

db_path = "cronograma_inteligente.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

crono_id = 326

# Obtener categorías semanales guardadas para este cronograma
cursor.execute("""
    SELECT nombre, fecha_lunes, categoria 
    FROM semanas_categorias 
    WHERE cronograma_id = ? 
    ORDER BY nombre, fecha_lunes
""", (crono_id,))
rows = cursor.fetchall()

# Agrupar por empleado
emp_weeks = {}
for nombre, fecha_lunes, categoria in rows:
    emp_weeks.setdefault(nombre, []).append((date.fromisoformat(fecha_lunes), categoria))

print("=== VERIFICACIÓN DE NO REPETICIÓN CONSECUTIVA CALENDARIO ===")
colisiones = 0
total_transiciones = 0
for nombre, w_list in emp_weeks.items():
    for i in range(len(w_list) - 1):
        d1, cat1 = w_list[i]
        d2, cat2 = w_list[i+1]
        
        # Verificar si son semanas calendaras consecutivas (diferencia de exactamente 7 días)
        if (d2 - d1).days == 7:
            total_transiciones += 1
            if cat1 == cat2:
                print(f"Colisión detectada para {nombre}: {d1.isoformat()} ({cat1}) y {d2.isoformat()} ({cat2})")
                colisiones += 1

print(f"Total transiciones de semanas consecutivas evaluadas: {total_transiciones}")
print(f"Colisiones encontradas: {colisiones}")
conn.close()

import sqlite3
from datetime import date, timedelta
from database import queries as db_queries
from restricciones.hard._utils import determinar_familia_ganadora

db_path = "cronograma_inteligente.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

crono_id = 326
servicio_id = 2
fecha_inicio = "2026-06-01"

historial = db_queries.cargar_guardias_previas(fecha_inicio, dias_atras=28, servicio_id=servicio_id)

primer_lunes = date.fromisoformat(fecha_inicio)
lunes_previo = primer_lunes - timedelta(days=7)

print("=== VERIFICACIÓN HISTORIAL (2026-05-25) -> PRIMERA SEMANA (2026-06-01) ===")
cursor.execute("""
    SELECT nombre, categoria 
    FROM semanas_categorias 
    WHERE cronograma_id = ? AND fecha_lunes = ?
""", (crono_id, fecha_inicio))
semanas_primera = {nombre: cat for nombre, cat in cursor.fetchall()}

violaciones = 0
total = 0

for nombre, hist_prev in historial.items():
    ganador_prev = determinar_familia_ganadora(hist_prev, lunes_previo)
    ganador_primera = determinar_familia_ganadora(hist_prev, primer_lunes)
    
    cat_asignada = semanas_primera.get(nombre)
    
    if ganador_prev and cat_asignada:
        total += 1
        if ganador_prev == cat_asignada:
            # Si es igual, chequear si fue por historial forzado en la primera semana
            if ganador_primera == ganador_prev:
                print(f"{nombre}: Repetición forzada por historial solapado en la primera semana: {ganador_prev} -> {cat_asignada}")
            else:
                print(f"VIOLACIÓN DETECTADA: {nombre} repitió {ganador_prev} -> {cat_asignada} sin estar forzado.")
                violaciones += 1
        else:
            # Transición correcta
            pass

print(f"Total de transiciones desde historia evaluadas: {total}")
print(f"Violaciones no forzadas encontradas: {violaciones}")
conn.close()

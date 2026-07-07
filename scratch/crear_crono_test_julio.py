import sqlite3
import datetime

def main():
    conn = sqlite3.connect("cronograma_inteligente.db")
    cur = conn.cursor()
    
    # 1. Poner en 'borrador' temporalmente todos los cronogramas aprobados de julio de 2026
    # para que nuestro cronograma de test sea el último aprobado antes de agosto.
    cur.execute("""
        UPDATE cronogramas 
        SET estado = 'borrador' 
        WHERE estado = 'aprobado' AND fecha_inicio >= '2026-07-01' AND fecha_fin <= '2026-07-31'
    """)
    print("Cronogramas de julio aprobados puestos en 'borrador'.")
    
    # 2. Insertar nuestro cronograma de test aprobado para julio
    cur.execute("""
        INSERT INTO cronogramas (fecha_inicio, fecha_fin, creado_en, notas, estado)
        VALUES ('2026-07-01', '2026-07-31', ?, 'Cronograma Test Graciela Palana 31/7', 'aprobado')
    """, (datetime.datetime.now().isoformat(),))
    
    crono_id = cur.lastrowid
    print(f"Nuevo cronograma de test aprobado creado con ID: {crono_id}")
    
    # 3. Insertar la guardia de Palana el 31/7
    # (El 31/7 es viernes, es_finde = 0)
    cur.execute("""
        INSERT INTO guardias (cronograma_id, nombre, fecha, turno, horas, es_finde)
        VALUES (?, 'PALANA GRACIELA', '2026-07-31', 'T', 6, 0)
    """, (crono_id,))
    print("Guardia de PALANA GRACIELA el 2026-07-31 insertada.")
    
    conn.commit()
    conn.close()
    print("Listo!")

if __name__ == "__main__":
    main()

import sqlite3
import subprocess

def main():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    print("=== APLICANDO CAMBIOS PARA EL CRONOGRAMA 152 ===")
    
    # 1. Dia 20/06 - Garcia Rodriguez cambia N_Planta por D_Planta
    cursor.execute("""
        UPDATE guardias 
        SET turno = 'D_Planta' 
        WHERE cronograma_id = 152 
          AND nombre = 'Garcia Rodriguez, Maria Eugenia.' 
          AND fecha = '2026-06-20' 
          AND turno = 'N_Planta'
    """)
    print(f"García 20/06 (N_Planta -> D_Planta): Filas afectadas: {cursor.rowcount}")
    
    # 2. Dia 20/06 - Nuñez cambia D_Residente por N_Residente
    # Primero borramos D_Residente por si existiera
    cursor.execute("""
        DELETE FROM guardias 
        WHERE cronograma_id = 152 
          AND nombre = 'N\u00fa\u00f1ez Florencia Natalia' 
          AND fecha = '2026-06-20' 
          AND turno = 'D_Residente'
    """)
    del_count = cursor.rowcount
    
    # Insertamos N_Residente (es_finde = 1 porque es Sábado)
    cursor.execute("""
        INSERT INTO guardias (cronograma_id, nombre, fecha, turno, horas, es_finde) 
        VALUES (152, 'N\u00fa\u00f1ez Florencia Natalia', '2026-06-20', 'N_Residente', 12, 1)
    """)
    print(f"Núñez 20/06 (D_Residente -> N_Residente): Eliminados {del_count}, Insertado N_Residente")
    
    # 3. Dia 21/06 - Aguilera cambia N_Planta por D_Planta
    cursor.execute("""
        UPDATE guardias 
        SET turno = 'D_Planta' 
        WHERE cronograma_id = 152 
          AND nombre = 'Aguilera Graciela' 
          AND fecha = '2026-06-21' 
          AND turno = 'N_Planta'
    """)
    print(f"Aguilera 21/06 (N_Planta -> D_Planta): Filas afectadas: {cursor.rowcount}")
    
    # 4. Dia 21/06 - Motta cambia D_Planta por N_Planta
    cursor.execute("""
        UPDATE guardias 
        SET turno = 'N_Planta' 
        WHERE cronograma_id = 152 
          AND nombre = 'Motta, Mayra Belen' 
          AND fecha = '2026-06-21' 
          AND turno = 'D_Planta'
    """)
    print(f"Motta 21/06 (D_Planta -> N_Planta): Filas afectadas: {cursor.rowcount}")
    
    conn.commit()
    conn.close()
    print("\n[OK] Cambios guardados en la base de datos.")

if __name__ == '__main__':
    main()

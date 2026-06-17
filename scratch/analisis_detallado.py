import sqlite3
from datetime import datetime, date, timedelta

DB_PATH = "cronograma_inteligente.db"
CRONOGRAMA_ID = 378

def get_dates_in_range(start_date, end_date):
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    curr = start
    dates = []
    while curr <= end:
        dates.append(curr)
        curr += timedelta(days=1)
    return dates

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT fecha_inicio, fecha_fin FROM cronogramas WHERE id = ?", (CRONOGRAMA_ID,))
    fecha_inicio, fecha_fin = cursor.fetchone()
    fechas_mes = get_dates_in_range(fecha_inicio, fecha_fin)

    cursor.execute("SELECT DISTINCT nombre FROM guardias WHERE cronograma_id = ?", (CRONOGRAMA_ID,))
    personal_nombres = [r[0] for r in cursor.fetchall() if r[0] != "POLETTI NATALIA"]

    # 1. Obtener todas las licencias de este personal en julio
    cursor.execute("""
        SELECT nombre, tipo, fecha_inicio, fecha_fin FROM licencias
    """)
    licencias_data = cursor.fetchall()
    
    print("Licencias registradas en la DB para el personal del cronograma (excluyendo Poletti):")
    for nombre, tipo, lic_ini, lic_fin in licencias_data:
        if nombre in personal_nombres:
            # check overlap with July
            ini = date.fromisoformat(lic_ini)
            fin = date.fromisoformat(lic_fin)
            if not (fin < date(2026, 7, 1) or ini > date(2026, 7, 31)):
                print(f"  - {nombre}: Tipo={tipo}, Desde={lic_ini}, Hasta={lic_fin}")

    # Vamos a evaluar bajo dos hipótesis:
    # Hipótesis 1: El término "franco" excluye todas las licencias (LPP, LAR, CM, LM) y FLR.
    #             (Ya que las licencias no son francos. Como LPP es licencia, ya estaría excluida, pero el usuario la menciona para clarificar).
    # Hipótesis 2: El término "franco" incluye licencias LAR/CM/LM y solo excluye LPP, FLR y Poletti.

    for hip_num, hip_desc in [
        (1, "Excluyendo todas las licencias (LAR, CM, LM, LPP) y FLR"),
        (2, "Excluyendo únicamente LPP y FLR (es decir, LAR, CM, LM se consideran como franco)")
    ]:
        print(f"\n--- HIPÓTESIS {hip_num}: {hip_desc} ---")
        
        calendario = {}
        for nombre in personal_nombres:
            calendario[nombre] = {f: 'FRANCO' for f in fechas_mes}

        # Cargar Guardias (Trabajo)
        cursor.execute("SELECT nombre, fecha FROM guardias WHERE cronograma_id = ?", (CRONOGRAMA_ID,))
        for nombre, fecha_str in cursor.fetchall():
            if nombre in calendario:
                f = date.fromisoformat(fecha_str)
                if f in calendario[nombre]:
                    calendario[nombre][f] = 'TRABAJO'

        # Cargar FLR (Siempre excluido)
        cursor.execute("SELECT nombre, fecha_inicio, fecha_fin FROM flr_asignados WHERE cronograma_id = ?", (CRONOGRAMA_ID,))
        for nombre, flr_ini, flr_fin in cursor.fetchall():
            if nombre in calendario:
                ini = date.fromisoformat(flr_ini)
                fin = date.fromisoformat(flr_fin)
                curr = ini
                while curr <= fin:
                    if curr in calendario[nombre]:
                        calendario[nombre][curr] = 'FLR'
                    curr += timedelta(days=1)

        # Cargar Licencias según hipótesis
        for nombre, tipo, lic_ini, lic_fin in licencias_data:
            if nombre in calendario:
                # Determinar si excluir este tipo de licencia
                excluir_lic = False
                if hip_num == 1:
                    excluir_lic = True # Excluye todas
                elif hip_num == 2:
                    if tipo == 'LPP':
                        excluir_lic = True # Excluye solo LPP

                if excluir_lic:
                    ini = date.fromisoformat(lic_ini)
                    fin = date.fromisoformat(lic_fin)
                    curr = ini
                    while curr <= fin:
                        if curr in calendario[nombre] and calendario[nombre][curr] != 'TRABAJO':
                            calendario[nombre][curr] = 'LICENCIA_' + tipo
                        curr += timedelta(days=1)

        # Buscar rachas de >= 4 días consecutivos de Franco
        emp_consecutivos = {}
        for nombre in personal_nombres:
            racha_actual = []
            rachas_encontradas = []
            for f in fechas_mes:
                estado = calendario[nombre][f]
                if estado == 'FRANCO':
                    racha_actual.append(f)
                else:
                    if len(racha_actual) >= 4:
                        rachas_encontradas.append(list(racha_actual))
                    racha_actual = []
            if len(racha_actual) >= 4:
                rachas_encontradas.append(list(racha_actual))
            if rachas_encontradas:
                emp_consecutivos[nombre] = rachas_encontradas

        print(f"Cantidad de enfermeros con >= 4 días consecutivos de Franco: {len(emp_consecutivos)}")
        for nombre, rachas in sorted(emp_consecutivos.items()):
            desc = [f"desde {r[0]} hasta {r[-1]} ({len(r)} días)" for r in rachas]
            print(f"  - {nombre}: {', '.join(desc)}")

    conn.close()

if __name__ == "__main__":
    main()

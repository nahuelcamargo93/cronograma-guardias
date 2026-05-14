"""
ver_cronograma.py — Visor de cronogramas en el navegador.

Lee guardias_historial.db, genera un HTML interactivo y lo abre.
Uso:  python ver_cronograma.py
"""

import os
import webbrowser
import json
from datetime import date, timedelta

from db import DB_PATH, get_connection


def generar_html():
    conn = get_connection()

    guardias = conn.execute("""
        SELECT nombre, fecha, turno, horas, es_finde
        FROM guardias ORDER BY fecha, turno, nombre
    """).fetchall()

    personal = conn.execute("SELECT nombre, rol FROM personal ORDER BY nombre").fetchall()

    bloques = conn.execute("""
        SELECT fecha_inicio, fecha_fin, tipo FROM bloques_finde_largo
        ORDER BY fecha_inicio
    """).fetchall()

    licencias = conn.execute("""
        SELECT nombre, tipo, fecha_inicio, fecha_fin 
        FROM licencias 
        ORDER BY fecha_inicio DESC
    """).fetchall()

    conn.close()

    # JSON data for the frontend
    guardias_data = json.dumps([
        {'nombre': g[0], 'fecha': g[1], 'turno': g[2], 'horas': g[3], 'esFinde': g[4]}
        for g in guardias
    ], ensure_ascii=False)

    personal_data = json.dumps([
        {'nombre': p[0], 'rol': p[1]}
        for p in personal
    ], ensure_ascii=False)

    bloques_data = json.dumps([
        {'fechaInicio': b[0], 'fechaFin': b[1], 'tipo': b[2]}
        for b in bloques
    ], ensure_ascii=False)

    lar_data = json.dumps([
        {'nombre': l[0], 'fechaInicio': l[2], 'fechaFin': l[3]}
        for l in licencias if l[1] == 'LAR'
    ], ensure_ascii=False)

    lpp_data = json.dumps([
        {'nombre': l[0], 'fechaInicio': l[2], 'fechaFin': l[3]}
        for l in licencias if l[1] == 'LPP'
    ], ensure_ascii=False)

    if guardias:
        min_fecha = min(g[1] for g in guardias)
        max_fecha = max(g[1] for g in guardias)
    else:
        min_fecha = max_fecha = date.today().isoformat()

    total_personal = len(personal)
    total_horas = sum(g[3] for g in guardias)

    # Load HTML template
    template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cronograma_template.html")
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()

    html = template.replace('__GUARDIAS_DATA__', guardias_data)
    html = html.replace('__PERSONAL_DATA__', personal_data)
    html = html.replace('__BLOQUES_DATA__', bloques_data)
    html = html.replace('__LAR_DATA__', lar_data)
    html = html.replace('__LPP_DATA__', lpp_data)
    html = html.replace('__MIN_FECHA__', min_fecha)
    html = html.replace('__MAX_FECHA__', max_fecha)
    html = html.replace('__TOTAL_PERSONAL__', str(total_personal))
    html = html.replace('__TOTAL_HORAS__', str(total_horas))
    html = html.replace('__DB_NAME__', os.path.basename(DB_PATH))

    return html


def main():
    if not os.path.exists(DB_PATH):
        print(f"No se encontro la BD en: {DB_PATH}")
        print("Ejecuta primero 'python main.py' o 'python importar_excel.py'.")
        return

    print("Generando vista del cronograma...")
    html = generar_html()

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"HTML generado: {out_path}")
    print("Abriendo en el navegador...")
    webbrowser.open('file:///' + out_path.replace('\\', '/'))


if __name__ == "__main__":
    main()

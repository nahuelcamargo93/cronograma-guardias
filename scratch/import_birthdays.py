import sqlite3
import os
import re

DB_PATH = "cronograma_inteligente.db"

data_text = """
ABELENDA GRISELL PATRICIA 	19/08/1971
ALBELO TANIA BELEN	13/10/1995
ALCARAZ ELIANA BEATRIZ	24/10/1989
ALCARAZ, JOSE FRANCISCO SEBASTIAN 	25/05/1985
ANDREOLI LUCIANA VANESA 	1/06/1985
ARCE ROQUE DANIEL	30/06/1986
ASTUDILLO MELINA	28/01/1993
BARROSO ÉRICA ALEJANDRA 	6/03/1980
Bascur Cruz  Alejandra Elizabeth	3/02/1991
Boria Ortiz Mayra	10/12/1991
CALDERÓN DE LA TORRE MARÍA JOSÉ 	30/05/1992
CAMPOS PRISCILA NAHIR 	27/03/1989
CARRERAS FLAVIA AYELEN 	11/10/1991
CASTRO VILCHEZ LUCIANO	27/06/1997
CHIRINO SILVANA CAROLINA	26/08/1991
CORIA LUCIANO EZEQUIEL	5/12/2002
CORSO ARTURO	6/04/1982
DOMÍNGUEZ VERÓNICA ALEJANDRA 	23/09/1993
DURAN RENFIGIO JAZMIN LUCILA 	5/05/2003
ECHENIQUE ROCIO	25/03/1999
Escalante Carla Daniela	29/07/1990
Escudero Sergio Sebastian	30/09/1990
Fernández Paola Belén 	8/08/1997
FERNÁNDEZ SOLOA YESICA BEATRIZ 	1/05/1984
Gimenez Velázquez, Karen Gricel 	1/03/1999
GOMES BENEITE ELIDA STHEFANIA 	20/10/1994
GÓMEZ, LOURDES 	24/01/1991
GRABOVIECKI CORVALAN MARIA FERNANDA 	29/07/1996
GUIÑAZÚ KARINA	9/03/1992
IRAZÁBAL, MARIÁNGELES SILVINA 	7/04/1981
LUCERO MATÍAS EXEQUIEL	13/06/1996
Mañe María Lorena 	26/01/1993
MEDINA MARIA LAURA	24/09/1993
MIRANDA LUCIANA IVANA	17/02/1986
MIRANDA YANINA YOHANA	6/04/1987
MONDONE PAULA SILVINA	19/07/1990
NIEVAS CARLA ROMINA 	20/06/1996
OLGUIN LUCIA BELEN	1/10/1994
ORTIZ MARIA LAURA	21/05/1993
PALACIOS FACUNDO 	20/09/1989
PALANA GRACIELA LAURA	23/05/1973
PEREIRA CRISTINA BEATRIZ 	7/10/1992
POLETtI ZULEMA NATALIA 	15/01/1980
QUEVEDO VÉLEZ MARIA CELESTE	18/05/1984
RINALDINI DELGADO IVANA ANDREA	17/11/1990
SOSA GARRO PABLO NAHUEL	31/03/2001
SUAREZ JESICA 	27/01/1996
TULA, DAIANA JUDITH 	19/07/1989
VÉLEZ ALBERTO DANIEL 	20/12/1978
VELIZ LIONEL PABLO 	1/02/2002
VERA MARIA JULIETA 	15/02/1992
"""

def normalize(text):
    import unicodedata
    # text = text.replace('', 'N') # Hack for the DB output I saw
    text = "".join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    return text.upper().replace(',', '').replace('.', '').strip()

def format_date(date_str):
    parts = date_str.split('/')
    if len(parts) == 3:
        d, m, y = parts
        return f"{y}-{m.zfill(2)}-{d.zfill(2)}"
    return None

def run():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    db_names = [r[0] for r in cursor.execute("SELECT nombre FROM personal").fetchall()]
    
    updates = []
    lines = [l.strip() for l in data_text.strip().split('\n') if l.strip()]
    
    for line in lines:
        match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', line)
        if match:
            date_raw = match.group(1)
            name_raw = line.replace(date_raw, '').strip()
            iso_date = format_date(date_raw)
            
            norm_name = normalize(name_raw)
            name_parts = set(norm_name.split())
            
            best_match = None
            for db_name in db_names:
                norm_db = normalize(db_name)
                # Remove "LIC" prefix
                if norm_db.startswith("LIC "):
                    norm_db = norm_db[4:].strip()
                
                db_parts = norm_db.split()
                
                # Logic: If all parts of the DB name are in the input name parts, it's a likely match
                if all(p in name_parts for p in db_parts):
                    best_match = db_name
                    break
                
                # Or if the first part (Surname) and second part (First name) match
                if len(db_parts) >= 2 and db_parts[0] in name_parts and db_parts[1] in name_parts:
                    best_match = db_name
                    break
            
            if best_match:
                updates.append((iso_date, best_match))
                print(f"Matched: '{name_raw}' -> '{best_match}' ({iso_date})")
            else:
                print(f"No match for: '{name_raw}'")

    for iso_date, name in updates:
        cursor.execute("UPDATE personal SET fecha_cumpleanos = ? WHERE nombre = ?", (iso_date, name))
    
    conn.commit()
    print(f"Done. Updated {len(updates)} records.")
    conn.close()

if __name__ == "__main__":
    run()

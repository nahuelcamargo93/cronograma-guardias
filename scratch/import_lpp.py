import sqlite3
import os
import unicodedata
from datetime import date

DB_PATH = "cronograma_inteligente.db"

data_text = """
Graboviecki Fernanda 	6/4	19/4
Rojas Juliana 	6/4	19/4
Arce Daniel 	6/4	19/4
Palacios Facundo 	20/4	4/5
Medina Laura 	20/4	4/5
Velez Daniel 	20/4	4/5
Escudero Sergio 	20/4	4/5
Abelenda Grisell	20/4	4/5
Tula Daiana 	4/5	17/5
Andreoli Luciana	4/5	17/5
Fernandez Yessica 	4/5	17/5
Fernandez Paola 	4/5	17/5
Poletti Natalia 	18/5	1/6
Miranda Yanina	18/5	1/6
Alcaraz Francisco 	18/5	1/6
Quevedo Celeste	18/5	1/6
Carreras Flavia 	1/6	14/6
Rinaldini Ivana	1/6	14/6
Mondone Paula 	1/6	14/6
Gomez Lourdes	1/6	14/6
Alcaraz Eliana 	1/6	14/6
Pereira Cristina 	15/6	29/6
Lucero Matias	15/6	29/6
Palana Graciela 	15/6	29/6
Dominguez Veronica	15/6	29/6
Suarez Jessica	15/6	29/6
Campos Priscila 	15/6	29/6
Guiñazu Karina 	29/6	13/7
Miranda Luciana	29/6	13/7
Bascur Alejandra 	29/6	13/7
Castro Luciano	29/6	13/7
Vera Julieta	29/6	13/7
Echenique Rocio	29/6	13/7
"""

import difflib

def normalize(text):
    text = "".join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    return text.upper().replace(',', '').replace('.', '').strip()

def parse_date(d_m_str, year=2026):
    parts = d_m_str.strip().split('/')
    if len(parts) == 2:
        d, m = parts
        return f"{year}-{m.zfill(2)}-{d.zfill(2)}"
    return None

def run():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    db_names = [r[0] for r in cursor.execute("SELECT nombre FROM personal").fetchall()]
    norm_db_map = {normalize(n): n for n in db_names}
    
    inserts = []
    lines = [l.strip() for l in data_text.strip().split('\n') if l.strip()]
    
    for line in lines:
        parts = [p.strip() for p in line.split('\t') if p.strip()]
        if len(parts) < 3:
            parts = [p.strip() for p in line.rsplit(None, 2)]
            
        if len(parts) == 3:
            name_raw, start_raw, end_raw = parts
            fi = parse_date(start_raw)
            ff = parse_date(end_raw)
            
            norm_name = normalize(name_raw)
            
            # Fuzzy match
            best_match = None
            # Try exact first
            if norm_name in norm_db_map:
                best_match = norm_db_map[norm_name]
            else:
                # Try close match
                matches = difflib.get_close_matches(norm_name, norm_db_map.keys(), n=1, cutoff=0.7)
                if matches:
                    best_match = norm_db_map[matches[0]]
                else:
                    # Try part matching
                    name_parts = norm_name.split()
                    for norm_db, orig_db in norm_db_map.items():
                        db_parts = norm_db.split()
                        if all(p in name_parts for p in db_parts) or all(p in db_parts for p in name_parts):
                            best_match = orig_db
                            break
            
            if best_match and fi and ff:
                inserts.append((best_match, 'LPP', fi, ff))
                print(f"Matched: '{name_raw}' -> '{best_match}' ({fi} to {ff})")
            else:
                print(f"No match/date error for: '{line}' (Best match: {best_match}, fi: {fi}, ff: {ff})")

    # Clear existing LPP to avoid duplicates
    cursor.execute("DELETE FROM licencias WHERE tipo='LPP'")
    
    for name, tipo, fi, ff in inserts:
        cursor.execute("INSERT INTO licencias (nombre, tipo, fecha_inicio, fecha_fin) VALUES (?, ?, ?, ?)", (name, tipo, fi, ff))
    
    conn.commit()
    print(f"Done. Inserted {len(inserts)} LPP records.")
    conn.close()

if __name__ == "__main__":
    run()

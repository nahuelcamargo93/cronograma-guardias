import sqlite3
import os
import unicodedata

DB_PATH = "cronograma_inteligente.db"

data_text = """
ABELENDA GRISELL	CCTHRC
ALBELO TANIA	MNT
ALCARAZ ELIANA	CCTHRC
ALCARAZ FRANCISO	CS
ANDREOLI LUCIANA	CS
ARCE DANIEL 	CCTHRC
ASTUDILLO MELINA	MNT
BARROSO ERICA	CCTHRC
BASCUR ALEJANDRA	CCT
BORIA MAYRA	MNT
CALDERON MARIA JOSE	MNT
CAMPOS PRISCILA	CS
CARRERAS FLAVIA	CS
CASTRO LUCIANO 	CCTHRC
CORSO ARTURO	MNT
CHIRINO CAROLINA	MNT
CORIA LUCIANO	MNT
DOMINGUEZ VERONICA	CCTHRC
DURAN JAZMIN	MNT
ECHENIQUE ROCIO	CCTHRC
ESCALANTE CARLA	MNT
ESCUDERO SERGIO	CS
FERNANDEZ PAOLA	CCTHRC
FERNANDEZ YESICA 	CCTHRC
GIMENEZ KAREN	MNT
GOMES STHEFANIA	MNT
GOMEZ LOURDES	CCTHRC
GRABOVIECKI FERNANDA	CCTHRC
GUIÑAZU KARINA	CS
IRAZABAL MARIANGELES	CS
LUCERO MATIAS	CCTHRC
MAÑE LORENA	MNT
MEDINA LAURA	CCTHRC
MIRANDA LUCIANA	CCTHRC
MIRANDA YANINA	CS
MONDONE PAULA	CS
NIEVAS CARLA	MNT
OLGUIN LUCIA	MNT
ORTIZ LAURA	CS
PALACIOS FACUNDO	CS
PALANA GRACIELA	CCTHRC
PEREIRA CRISTINA	CS
POLETTI NATALIA	CS
QUEVEDO CELESTE	CS
RINALDINI IVANA	CCTHRC
ROJAS JULIANA	CS
SOSA NAHUEL	MNT
SUAREZ JESICA	CCTHRC
TULA DAIANA	CCTHRC
VELEZ DANIEL	CS
VELIZ LIONEL	MNT
VERA JULIETA	CCTHRC
"""

def normalize(text):
    text = "".join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    return text.upper().replace(',', '').replace('.', '').strip()

def run():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    db_names = [r[0] for r in cursor.execute("SELECT nombre FROM personal").fetchall()]
    
    updates = []
    lines = [l.strip() for l in data_text.strip().split('\n') if l.strip()]
    
    for line in lines:
        parts = line.split('\t')
        if len(parts) < 2:
            # Try spaces if tabs are missing
            parts = [p.strip() for p in line.rsplit(None, 1)]
            
        if len(parts) == 2:
            name_raw, regimen = parts
            norm_name = normalize(name_raw)
            name_parts = set(norm_name.split())
            
            best_match = None
            for db_name in db_names:
                norm_db = normalize(db_name)
                if norm_db.startswith("LIC "):
                    norm_db = norm_db[4:].strip()
                
                db_parts = norm_db.split()
                
                if all(p in name_parts for p in db_parts) or (len(db_parts) >= 2 and db_parts[0] in name_parts and db_parts[1] in name_parts):
                    best_match = db_name
                    break
            
            if best_match:
                updates.append((regimen, best_match))
                print(f"Matched: '{name_raw}' -> '{best_match}' ({regimen})")
            else:
                print(f"No match for: '{name_raw}'")

    for regimen, name in updates:
        cursor.execute("UPDATE personal SET regimen_trabajo = ? WHERE nombre = ?", (regimen, name))
    
    conn.commit()
    print(f"Done. Updated {len(updates)} records.")
    conn.close()

if __name__ == "__main__":
    run()

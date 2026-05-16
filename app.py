from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import json
import sqlite3
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

# Importar lógica del motor (sin tocarla, solo llamándola)
import db as legacy_db
from database import queries as db_queries
from main import ejecutar_optimizacion

app = FastAPI(title="Cronograma Inteligente WFM")

# CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database path
DB_PATH = legacy_db.DB_PATH

def get_db_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# --- Modelos API ---
class Servicio(BaseModel):
    id: int
    nombre: int
    organizacion_id: int

# --- Endpoints API ---

@app.get("/api/organizaciones")
async def get_organizaciones():
    with get_db_conn() as conn:
        rows = conn.execute("SELECT * FROM organizaciones").fetchall()
        return [dict(row) for row in rows]

@app.get("/api/servicios/{org_id}")
async def get_servicios(org_id: int):
    with get_db_conn() as conn:
        rows = conn.execute("SELECT * FROM servicios WHERE organizacion_id = ?", (org_id,)).fetchall()
        return [dict(row) for row in rows]

@app.get("/api/cronogramas/{servicio_id}")
async def get_cronogramas_historial(servicio_id: int):
    # Nota: La tabla cronogramas no tiene servicio_id directamente, pero las guardias sí están ligadas a personal de un servicio.
    # Por ahora, listaremos todos y filtraremos si es necesario.
    with get_db_conn() as conn:
        rows = conn.execute("""
            SELECT DISTINCT c.* 
            FROM cronogramas c
            JOIN guardias g ON g.cronograma_id = c.id
            JOIN personal p ON g.nombre = p.nombre
            WHERE p.servicio_id = ?
            ORDER BY c.fecha_inicio DESC
        """, (servicio_id,)).fetchall()
        return [dict(row) for row in rows]

@app.get("/api/cronograma/{cronograma_id}")
async def get_cronograma_detalle(cronograma_id: int):
    with get_db_conn() as conn:
        cronograma = conn.execute("SELECT * FROM cronogramas WHERE id = ?", (cronograma_id,)).fetchone()
        if not cronograma:
            raise HTTPException(status_code=404, detail="Cronograma no encontrado")
        
        guardias = conn.execute("""
            SELECT g.*, p.rol 
            FROM guardias g
            JOIN personal p ON g.nombre = p.nombre
            WHERE g.cronograma_id = ?
            ORDER BY g.fecha, g.turno
        """, (cronograma_id,)).fetchall()
        
        bloques = conn.execute("SELECT * FROM bloques_finde_largo WHERE cronograma_id = ?", (cronograma_id,)).fetchall()
        
        return {
            "metadata": dict(cronograma),
            "guardias": [dict(g) for g in guardias],
            "bloques_finde": [dict(b) for b in bloques]
        }

@app.get("/api/reglas/{servicio_id}")
async def get_reglas_servicio(servicio_id: int):
    reglas = db_queries.cargar_reglas_servicio(servicio_id)
    reglas_personal = db_queries.cargar_reglas_personal(servicio_id)
    
    with get_db_conn() as conn:
        # Demanda: agrupar por puesto + franja horaria (evita duplicados por tipo_dia)
        puestos = conn.execute("""
            SELECT 
                p.nombre as puesto,
                d.hora_inicio,
                d.hora_fin,
                MIN(d.cantidad_min) as cantidad_min,
                MAX(d.cantidad_max) as cantidad_max
            FROM puestos p
            LEFT JOIN demanda_config d ON p.id = d.puesto_id
            WHERE p.servicio_id = ?
            GROUP BY p.nombre, d.hora_inicio, d.hora_fin
            ORDER BY p.nombre, d.hora_inicio
        """, (servicio_id,)).fetchall()
        turnos = conn.execute("SELECT * FROM turnos_config WHERE servicio_id = ? AND activo = 1", (servicio_id,)).fetchall()
        
    return {
        "reglas_generales": reglas,
        "reglas_personal": reglas_personal,
        "puestos": [dict(row) for row in puestos],
        "turnos": [dict(t) for t in turnos]
    }

@app.get("/api/reglas_catalogo/{servicio_id}")
async def get_reglas_catalogo(servicio_id: int):
    """Devuelve TODAS las reglas del catálogo, marcando cuáles están activas para el servicio."""
    with get_db_conn() as conn:
        # Todas las reglas del catálogo
        todas = conn.execute("""
            SELECT id, codigo_regla, tipo, descripcion FROM reglas_catalogo ORDER BY tipo, codigo_regla
        """).fetchall()
        
        # Reglas activas para este servicio
        activas_serv = {r[0] for r in conn.execute("""
            SELECT rc.codigo_regla FROM servicios_reglas sr
            JOIN reglas_catalogo rc ON sr.regla_id = rc.id
            WHERE sr.servicio_id = ?
        """, (servicio_id,)).fetchall()}
        
        # Reglas activas por organización
        org_id = conn.execute("SELECT organizacion_id FROM servicios WHERE id = ?", (servicio_id,)).fetchone()[0]
        activas_org = {r[0] for r in conn.execute("""
            SELECT rc.codigo_regla FROM organizaciones_reglas or_r
            JOIN reglas_catalogo rc ON or_r.regla_id = rc.id
            WHERE or_r.organizacion_id = ?
        """, (org_id,)).fetchall()}

    activas = activas_serv | activas_org
    resultado = []
    for row in todas:
        resultado.append({
            "id": row[0],
            "codigo_regla": row[1],
            "tipo": row[2],
            "descripcion": row[3],
            "activa": row[1] in activas
        })
    return resultado

class GenerarRequest(BaseModel):
    servicio_id: int
    fecha_inicio: str
    fecha_fin: str
    notas: Optional[str] = ""

@app.post("/api/generar")
async def generar_cronograma(req: GenerarRequest):
    try:
        # Ejecutar la optimización
        # Nota: En una app real esto debería ser BackgroundTasks para no bloquear el request,
        # pero para esta demo lo haremos directo para simplificar el flujo.
        resultado = ejecutar_optimizacion(
            req.servicio_id, 
            req.fecha_inicio, 
            req.fecha_fin, 
            notas=req.notas
        )
        
        if resultado.get("status") == "success":
            return resultado
        else:
            raise HTTPException(status_code=400, detail=resultado.get("error", "Error desconocido"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Servir Frontend ---

# Asegurar que existan las carpetas
os.makedirs("vistas_web/static", exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def get_index():
    with open("vistas_web/dashboard.html", "r", encoding="utf-8") as f:
        return f.read()

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory="vistas_web/static"), name="static")

if __name__ == "__main__":
    import uvicorn
    print("Iniciando servidor en http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)

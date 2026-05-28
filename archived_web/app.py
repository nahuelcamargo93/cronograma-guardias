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

@app.get("/api/cronogramas")
async def get_todos_cronogramas():
    """Devuelve todos los cronogramas con el nombre del servicio asociado."""
    with get_db_conn() as conn:
        rows = conn.execute("""
            SELECT DISTINCT c.*, s.nombre as servicio_nombre, s.id as servicio_id, s.organizacion_id
            FROM cronogramas c
            JOIN guardias g ON g.cronograma_id = c.id
            JOIN personal p ON g.nombre = p.nombre
            JOIN servicios s ON p.servicio_id = s.id
            ORDER BY c.fecha_inicio DESC
        """).fetchall()
        return [dict(row) for row in rows]

@app.get("/api/cronogramas/{servicio_id}")
async def get_cronogramas_historial(servicio_id: int):
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

@app.get("/api/cronograma_activo/{servicio_id}")
async def get_cronograma_activo(servicio_id: int):
    """Obtiene el último cronograma APROBADO para el servicio."""
    with get_db_conn() as conn:
        row = conn.execute("""
            SELECT DISTINCT c.* 
            FROM cronogramas c
            JOIN guardias g ON g.cronograma_id = c.id
            JOIN personal p ON g.nombre = p.nombre
            WHERE p.servicio_id = ? AND c.estado = 'aprobado'
            ORDER BY c.fecha_inicio DESC, c.id DESC
            LIMIT 1
        """, (servicio_id,)).fetchone()
        if not row:
            return None
        return dict(row)

@app.post("/api/aprobar/{cronograma_id}")
async def aprobar_cronograma(cronograma_id: int):
    """Establece un cronograma como APROBADO y los demás del mismo servicio a BORRADOR."""
    with get_db_conn() as conn:
        row = conn.execute("""
            SELECT DISTINCT p.servicio_id 
            FROM guardias g
            JOIN personal p ON g.nombre = p.nombre
            WHERE g.cronograma_id = ?
            LIMIT 1
        """, (cronograma_id,)).fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="No se encontró servicio para este cronograma")
        
        servicio_id = row['servicio_id']
        
        conn.execute("BEGIN TRANSACTION")
        try:
            other_rows = conn.execute("""
                SELECT DISTINCT c.id
                FROM cronogramas c
                JOIN guardias g ON g.cronograma_id = c.id
                JOIN personal p ON g.nombre = p.nombre
                WHERE p.servicio_id = ? AND c.id != ?
            """, (servicio_id, cronograma_id)).fetchall()
            
            other_ids = [r['id'] for r in other_rows]
            if other_ids:
                placeholders = ",".join("?" for _ in other_ids)
                conn.execute(f"UPDATE cronogramas SET estado = 'borrador' WHERE id IN ({placeholders})", other_ids)
            
            conn.execute("UPDATE cronogramas SET estado = 'aprobado' WHERE id = ?", (cronograma_id,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=f"Error al aprobar: {str(e)}")
            
        return {"status": "success", "message": f"Cronograma #{cronograma_id} aprobado"}

@app.get("/api/cronograma/{cronograma_id}")
async def get_cronograma_detalle(cronograma_id: int):
    with get_db_conn() as conn:
        cronograma = conn.execute("SELECT * FROM cronogramas WHERE id = ?", (cronograma_id,)).fetchone()
        if not cronograma:
            raise HTTPException(status_code=404, detail="Cronograma no encontrado")
        
        guardias = conn.execute("""
            SELECT g.id, g.cronograma_id, g.nombre, g.fecha, g.turno, g.horas, g.es_finde,
                   p.rol, p.servicio_id,
                   COALESCE(pu.nombre, p.rol) as puesto
            FROM guardias g
            JOIN personal p ON g.nombre = p.nombre
            LEFT JOIN turnos_config tc ON tc.servicio_id = p.servicio_id AND tc.nombre = g.turno
            LEFT JOIN puestos pu ON tc.puesto_id = pu.id
            WHERE g.cronograma_id = ?
            ORDER BY g.fecha, pu.nombre, g.nombre
        """, (cronograma_id,)).fetchall()
        
        serv_row = conn.execute("""
            SELECT DISTINCT p.servicio_id FROM guardias g 
            JOIN personal p ON g.nombre = p.nombre 
            WHERE g.cronograma_id = ? LIMIT 1
        """, (cronograma_id,)).fetchone()
        
        puestos = []
        if serv_row:
            puestos = conn.execute(
                "SELECT id, nombre FROM puestos WHERE servicio_id = ? ORDER BY id",
                (serv_row[0],)
            ).fetchall()
        
        bloques = conn.execute("SELECT * FROM bloques_finde_largo WHERE cronograma_id = ?", (cronograma_id,)).fetchall()
        
        return {
            "metadata": dict(cronograma),
            "guardias": [dict(g) for g in guardias],
            "puestos": [dict(p) for p in puestos],
            "bloques_finde": [dict(b) for b in bloques]
        }

@app.get("/api/licencias/{servicio_id}")
async def get_licencias_servicio(servicio_id: int, desde: str = None, hasta: str = None):
    """Licencias del personal de un servicio, filtradas por rango de fechas opcional."""
    with get_db_conn() as conn:
        if desde and hasta:
            rows = conn.execute("""
                SELECT l.nombre, l.tipo, l.fecha_inicio, l.fecha_fin
                FROM licencias l
                JOIN personal p ON l.nombre = p.nombre
                WHERE p.servicio_id = ? AND l.fecha_inicio <= ? AND l.fecha_fin >= ?
                ORDER BY l.nombre, l.fecha_inicio
            """, (servicio_id, hasta, desde)).fetchall()
        else:
            rows = conn.execute("""
                SELECT l.nombre, l.tipo, l.fecha_inicio, l.fecha_fin
                FROM licencias l
                JOIN personal p ON l.nombre = p.nombre
                WHERE p.servicio_id = ?
                ORDER BY l.nombre, l.fecha_inicio
            """, (servicio_id,)).fetchall()
    return [dict(r) for r in rows]

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
            SELECT codigo_regla FROM servicios_reglas
            WHERE servicio_id = ?
        """, (servicio_id,)).fetchall()}
        
        # Reglas activas por organización
        org_id = conn.execute("SELECT organizacion_id FROM servicios WHERE id = ?", (servicio_id,)).fetchone()[0]
        activas_org = {r[0] for r in conn.execute("""
            SELECT codigo_regla FROM organizaciones_reglas
            WHERE organizacion_id = ?
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

@app.get("/api/personal/{servicio_id}")
async def get_personal_servicio(servicio_id: int):
    """Devuelve la lista completa de personal para un servicio, con todos sus campos."""
    with get_db_conn() as conn:
        rows = conn.execute("""
            SELECT nombre, categoria, rol, fecha_cumpleanos, es_madre, es_padre, regimen_trabajo, horas_mensuales_reglamentarias
            FROM personal
            WHERE servicio_id = ?
            ORDER BY nombre
        """, (servicio_id,)).fetchall()
        return [dict(row) for row in rows]

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

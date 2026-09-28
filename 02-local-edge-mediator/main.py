"""main.py — Edge Controller local (mediador físico).

Expone REST para el ERP web (browser -> http://127.0.0.1:8000/capturar).
CORS abierto por defecto para demo LAN; restringir con ENV en producción.

  $ pip install -r requirements.txt
  $ uvicorn main:app --host 127.0.0.1 --port 8000

Endpoints:
  GET  /health            liveness + estado calibración
  GET  /capturar          alias GET (pruebas rápidas / panel)
  POST /capturar          lectura fusionada báscula + cámara 3D
  GET  /api/calibration   offsets actuales
  POST /api/calibration   {height_offset_cm, length_offset_cm, ...}
  POST /api/scale/tare    tara de báscula
  GET  /api/scale/check   verifica enlace serie (mock/real)
  GET  /config_testing/   panel web local de calibración
"""
from __future__ import annotations

import itertools
import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from mock_hardware import CalibrationState, Camera3D, CameraConfig, ScaleConfig, ScaleReader

cal = CalibrationState()
scale = ScaleReader(ScaleConfig(
    port=os.getenv("SCALE_PORT", "COM3"),
    baudrate=int(os.getenv("SCALE_BAUD", "9600")),
    mock=os.getenv("SCALE_MOCK", "1") != "0",
    base_kg=float(os.getenv("SCALE_BASE_KG", "12.5")),
))
camera = Camera3D(CameraConfig(), cal)
folio_seq = itertools.count(1)

app = FastAPI(title="SYSCOM Edge Mediator", version="1.0.0")

origins = [o.strip() for o in os.getenv(
    "EDGE_ALLOWED_ORIGINS",
    "http://localhost:8080,http://127.0.0.1:8080,http://localhost,http://127.0.0.1,*").split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if "*" in origins else origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CaptureIn(BaseModel):
    operador: str | None = Field(default=None, max_length=120)


class CalIn(BaseModel):
    height_offset_cm: float | None = Field(default=None, ge=-50, le=50)
    length_offset_cm: float | None = Field(default=None, ge=-50, le=50)
    width_offset_cm: float | None = Field(default=None, ge=-50, le=50)
    plane_tilt_deg: float | None = Field(default=None, ge=-5, le=5)


def _fuse(operador: str | None) -> dict:
    peso = scale.read_stable()
    dims = camera.capture()
    folio = f"EDGE-{datetime.now(timezone.utc):%Y%m%d}-{next(folio_seq):04d}"
    return {
        "folio": folio,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "peso_kg": peso["peso_kg"],
        "largo_cm": dims["largo_cm"],
        "ancho_cm": dims["ancho_cm"],
        "alto_cm": dims["alto_cm"],
        "volumen_cm3": round(dims["largo_cm"] * dims["ancho_cm"] * dims["alto_cm"], 1),
        "estable": peso["estable"],
        "confianza_3d": dims["confianza"],
        "nube_puntos": dims["nube_puntos"],
        "calibrado": any(abs(v) > 1e-9 for v in cal.as_dict().values()),
        "calibracion": cal.as_dict(),
        "bascula": {"trama": peso["trama"], "puerto": peso["puerto"], "mock": peso["mock"]},
        "operador": operador,
        "fuente": "edge-mock v1",
    }


@app.get("/health")
def health():
    return {"ok": True, "service": "edge-mediator", "version": "1.0.0",
            "calibracion": cal.as_dict(), "bascula_mock": scale.cfg.mock}


@app.get("/capturar")
def capturar_get():
    return JSONResponse(_fuse(None))


@app.post("/capturar")
def capturar_post(body: CaptureIn | None = None):
    return JSONResponse(_fuse(body.operador if body else None))


@app.get("/api/calibration")
def cal_get():
    return {"ok": True, "calibracion": cal.as_dict()}


@app.post("/api/calibration")
def cal_post(body: CalIn):
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    return {"ok": True, "calibracion": cal.update(**data)}


@app.post("/api/scale/tare")
def tare():
    return {"ok": True, "tara_kg": scale.tare()}


@app.get("/api/scale/check")
def scale_check():
    r = scale.check_link()
    return {"ok": r["ok"], **r}


HERE = Path(__file__).parent
CFG_DIR = HERE / "config_testing"
if CFG_DIR.exists():
    app.mount("/config_testing", StaticFiles(directory=str(CFG_DIR), html=True), name="config_testing")


@app.get("/")
def root():
    return {"ok": True, "panel": "/config_testing/", "capturar": "POST /capturar", "health": "GET /health"}

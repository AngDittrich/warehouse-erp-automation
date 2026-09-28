"""mock_hardware.py — Simuladores de báscula RS232/USB y cámara 3D.

Capa de abstracción lista para hardware real:
- ScaleReader: hoy genera peso estable con ruido gaussiano; mañana abre
  `serial.Serial(port, baudrate)` y parsea tramas tipo "ST,GS,+ 12.340kg".
- Camera3D: hoy convierte una caja base + ruido en L×W×H (nube de puntos
  simulada); mañana aquí entra el SDK (p. ej. Intel RealSense / Zivid) con
  `capturar_nube()` -> bounding-box -> dimensiones.

La calibración (offset de plano/altura) vive en CalibrationState y se ajusta
desde /config_testing sin reiniciar el servicio.
"""
from __future__ import annotations

import math
import random
import threading
import time
from dataclasses import dataclass, field


@dataclass
class CalibrationState:
    """Offsets físicos del plano de medición (cm). Persistencia en memoria."""
    height_offset_cm: float = 0.0   # corrige plano de la mesa / conveyor
    length_offset_cm: float = 0.0
    width_offset_cm: float = 0.0
    plane_tilt_deg: float = 0.0     # solo informativo en mock
    lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def as_dict(self) -> dict:
        with self.lock:
            return {
                "height_offset_cm": self.height_offset_cm,
                "length_offset_cm": self.length_offset_cm,
                "width_offset_cm": self.width_offset_cm,
                "plane_tilt_deg": self.plane_tilt_deg,
            }

    def update(self, **kw) -> dict:
        with self.lock:
            for k, v in kw.items():
                if hasattr(self, k) and isinstance(v, (int, float)):
                    setattr(self, k, float(v))
            return {
                "height_offset_cm": self.height_offset_cm,
                "length_offset_cm": self.length_offset_cm,
                "width_offset_cm": self.width_offset_cm,
                "plane_tilt_deg": self.plane_tilt_deg,
            }


@dataclass
class ScaleConfig:
    port: str = "COM3"          # puerto serie real cuando exista báscula
    baudrate: int = 9600
    mock: bool = True           # False -> intentar pyserial real
    base_kg: float = 12.5       # peso nominal del mock (caja típica)
    noise_kg: float = 0.02


class ScaleReader:
    """Lector de báscula con interfaz serie simulada."""

    def __init__(self, cfg: ScaleConfig | None = None):
        self.cfg = cfg or ScaleConfig()
        self._tare_kg = 0.0

    # --- API pública -----------------------------------------------------
    def tare(self) -> float:
        """Pone a cero (tara) y devuelve el offset aplicado."""
        w = self._raw_sample()
        self._tare_kg = w
        return round(self._tare_kg, 3)

    def read_stable(self, samples: int = 5, delay_s: float = 0.05) -> dict:
        """Promedia N muestras; reporta estabilidad (desv. estándar)."""
        vals = [self._raw_sample() for _ in range(max(1, samples))]
        time.sleep(0)  # en HW real: delay_s entre tramas serie
        net = sum(vals) / len(vals) - self._tare_kg
        mean = max(0.0, net)
        var = sum((v - sum(vals) / len(vals)) ** 2 for v in vals) / len(vals)
        return {
            "peso_kg": round(mean, 3),
            "estable": math.sqrt(var) < 0.05,
            "desv_kg": round(math.sqrt(var), 4),
            "trama": self._fake_frame(mean),
            "puerto": self.cfg.port,
            "baudrate": self.cfg.baudrate,
            "mock": self.cfg.mock,
        }

    def check_link(self) -> dict:
        """Verificación de enlace serie para el panel de testing."""
        if self.cfg.mock:
            return {"ok": True, "modo": "MOCK",
                    "detalle": f"Puerto virtual {self.cfg.port}@{self.cfg.baudrate} listo"}
        try:
            import serial  # type: ignore
            s = serial.Serial(self.cfg.port, self.cfg.baudrate, timeout=1)
            s.close()
            return {"ok": True, "modo": "REAL", "detalle": f"{self.cfg.port} OK"}
        except Exception as e:  # pragma: no cover
            return {"ok": False, "modo": "REAL", "detalle": str(e)}

    # --- internos ---------------------------------------------------------
    def _raw_sample(self) -> float:
        if self.cfg.mock or True:  # mock por defecto; HW real tras validar pyserial
            drift = random.uniform(-1, 1) * self.cfg.noise_kg
            return max(0.0, self.cfg.base_kg + drift)
        raise NotImplementedError  # pragma: no cover

    @staticmethod
    def _fake_frame(peso_kg: float) -> str:
        return f"ST,GS,+{peso_kg:8.3f}kg"


@dataclass
class CameraConfig:
    base_l_cm: float = 45.0
    base_w_cm: float = 30.0
    base_h_cm: float = 25.0
    noise_cm: float = 0.3
    points: int = 12000  # puntos simulados de la nube


class Camera3D:
    """Cámara 3D simulada: nube de puntos -> bounding box -> L×W×H."""

    def __init__(self, cfg: CameraConfig | None = None, cal: CalibrationState | None = None):
        self.cfg = cfg or CameraConfig()
        self.cal = cal or CalibrationState()

    def capture(self) -> dict:
        c = self.cfg
        cal = self.cal.as_dict()
        # Ruido gaussiano por eje + offsets de calibración del plano
        l = max(0.1, random.gauss(c.base_l_cm, c.noise_cm) + cal["length_offset_cm"])
        w = max(0.1, random.gauss(c.base_w_cm, c.noise_cm) + cal["width_offset_cm"])
        h = max(0.1, random.gauss(c.base_h_cm, c.noise_cm) + cal["height_offset_cm"])
        return {
            "largo_cm": round(l, 1),
            "ancho_cm": round(w, 1),
            "alto_cm": round(h, 1),
            "nube_puntos": c.points + random.randint(-400, 400),
            "plano_offset_cm": cal["height_offset_cm"],
            "confianza": round(random.uniform(0.96, 0.995), 3),
            "mock": True,
        }

# Edge Mediator local — Cámara 3D + Báscula
```powershell
pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 8000
# Panel: http://127.0.0.1:8000/config_testing/
# Docs:  http://127.0.0.1:8000/docs
```
ENV útiles: `SCALE_PORT=COM3`, `SCALE_BAUD=9600`, `SCALE_MOCK=1`,
`SCALE_BASE_KG=12.5`, `EDGE_ALLOWED_ORIGINS=*`.
Producción: `SCALE_MOCK=0` + `pip install pyserial`, y restringir CORS al dominio del ERP.

# Mini ERP — Estación de empaque (nube)
Correr con PHP >= 8.0:
```powershell
php -S localhost:8080 -t 01-cloud-erp
# abrir http://localhost:8080
```
Requiere el Edge local en `http://127.0.0.1:8000` (ver `02-local-edge-mediator`).
`EDGE_URL` puede sobreescribirse por variable de entorno.
Los registros se guardan en `data/empaques.json` (demo sin BD).

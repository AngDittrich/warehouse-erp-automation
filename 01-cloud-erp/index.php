<?php
// 01-cloud-erp/index.php — Mini ERP Nube (capa web, sin acceso directo a hardware)
// Arquitectura: el browser del operador hace fetch al Edge local (127.0.0.1:8000).
// El PHP NUNCA toca la báscula/cámara; solo persiste registros ya capturados.
date_default_timezone_set('America/Mexico_City');
$hoy = date('Y-m-d');
$edgeUrl = getenv('EDGE_URL') ?: 'http://127.0.0.1:8000';
?>
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SYSCOM · ERP Empaque Inteligente</title>
<link rel="stylesheet" href="assets/css/style.css">
</head>
<body data-edge-url="<?= htmlspecialchars($edgeUrl, ENT_QUOTES) ?>">
<header class="topbar">
  <div class="topbar-inner">
    <div class="brand">
      <div class="brand-mark">S</div>
      <div>
        <div class="brand-name">SYSCOM<sup>.mx</sup> <span class="tag">ERP · Nube</span></div>
        <div class="brand-sub">Smart Warehouse · Estación de Empaque</div>
      </div>
    </div>
    <div class="edge-status" id="edgeStatus" data-state="unknown">
      <span class="dot"></span><span id="edgeStatusText">Edge: verificando…</span>
    </div>
  </div>
</header>

<main class="layout">
  <section class="card form-card">
    <div class="card-head">
      <h1>Captura de empaque</h1>
      <p>El operador captura datos. Peso y dimensiones llegan del <strong>Edge local</strong> (cámara 3D + báscula).</p>
    </div>

    <form id="packForm" autocomplete="off">
      <div class="grid-2">
        <div class="field">
          <label for="operador">Nombre del operador</label>
          <input type="text" id="operador" name="operador" placeholder="Ej. Juan Pérez" required>
        </div>
        <div class="field">
          <label for="fecha">Fecha</label>
          <input type="date" id="fecha" name="fecha" value="<?= $hoy ?>" required>
        </div>
      </div>

      <div class="grid-2">
        <div class="field">
          <label for="peso">Peso (kg)</label>
          <input type="number" id="peso" name="peso" step="0.001" min="0" placeholder="0.000" required>
        </div>
        <div class="field">
          <label for="volumen">Volumen (cm³) · auto</label>
          <input type="text" id="volumen" readonly placeholder="—">
        </div>
      </div>

      <div class="grid-3">
        <div class="field">
          <label for="largo">Largo (cm)</label>
          <input type="number" id="largo" name="largo" step="0.1" min="0" placeholder="0.0" required>
        </div>
        <div class="field">
          <label for="ancho">Ancho (cm)</label>
          <input type="number" id="ancho" name="ancho" step="0.1" min="0" placeholder="0.0" required>
        </div>
        <div class="field">
          <label for="alto">Alto (cm)</label>
          <input type="number" id="alto" name="alto" step="0.1" min="0" placeholder="0.0" required>
        </div>
      </div>

      <div class="actions">
        <button type="button" id="btnCapturar" class="btn btn-primary">
          <span class="btn-icon">◉</span> Capturar Empaque
        </button>
        <button type="submit" id="btnGuardar" class="btn btn-secondary">Guardar registro</button>
        <button type="button" id="btnLimpiar" class="btn btn-ghost">Limpiar</button>
      </div>
      <p class="hint">“Capturar Empaque” = <code>fetch()</code> al Edge <code id="edgeUrlLabel">http://127.0.0.1:8000/capturar</code> → autocompleta Peso/Largo/Ancho/Alto en tiempo real.</p>
    </form>

    <div class="capture-out" id="captureOut" hidden>
      <div class="capture-out-head">Última lectura Edge <span id="captureTime"></span></div>
      <pre id="captureJson"></pre>
    </div>
    <div class="alert" id="alert" hidden></div>
  </section>

  <aside class="side">
    <section class="card">
      <div class="card-head"><h2>Registro actual</h2></div>
      <dl class="kv">
        <div><dt>Folio</dt><dd id="kvFolio">—</dd></div>
        <div><dt>Operador</dt><dd id="kvOperador">—</dd></div>
        <div><dt>Peso volumétrico*</dt><dd id="kvVol">—</dd></div>
        <div><dt>Fuente</dt><dd id="kvFuente">edge-mock v1</dd></div>
      </dl>
      <p class="micro">* Peso vol. = L×W×H / 5000 (factor paquetería estándar, editable en <code>app.js</code>).</p>
    </section>

    <section class="card">
      <div class="card-head row">
        <h2>Historial (ERP)</h2>
        <button class="btn btn-ghost btn-sm" id="btnReloadHist">Recargar</button>
      </div>
      <div class="table-wrap">
        <table id="histTable">
          <thead><tr><th>Folio</th><th>Fecha</th><th>Operador</th><th>Kg</th><th>L×W×H</th></tr></thead>
          <tbody><tr><td colspan="5" class="muted">Sin registros.</td></tr></tbody>
        </table>
      </div>
    </section>
  </aside>
</main>

<footer class="foot">SYSCOM · Mini ERP desacoplado — PHP nube + Edge local · <span id="year"></span></footer>
<script src="assets/js/app.js"></script>
</body>
</html>

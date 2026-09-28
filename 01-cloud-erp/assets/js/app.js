// 01-cloud-erp/assets/js/app.js
// Capa Nube: solo habla con el Edge vía fetch del browser (mismo PC del operador).
// El PHP nunca accede al hardware.
(function () {
  'use strict';
  const body = document.body;
  const EDGE_URL = (body.dataset.edgeUrl || 'http://127.0.0.1:8000').replace(/\/$/, '');
  const VOL_FACTOR = 5000; // divisor peso volumétrico paquetería

  const $ = (id) => document.getElementById(id);
  const els = {
    operador: $('operador'), fecha: $('fecha'), peso: $('peso'),
    largo: $('largo'), ancho: $('ancho'), alto: $('alto'), volumen: $('volumen'),
    btnCap: $('btnCapturar'), form: $('packForm'), alert: $('alert'),
    out: $('captureOut'), json: $('captureJson'), time: $('captureTime'),
    edge: $('edgeStatus'), edgeText: $('edgeStatusText'),
    folio: $('kvFolio'), kvOp: $('kvOperador'), kvVol: $('kvVol'),
    hist: document.querySelector('#histTable tbody'),
  };
  $('edgeUrlLabel').textContent = EDGE_URL + '/capturar';
  $('year').textContent = new Date().getFullYear();

  function showAlert(msg, ok) {
    els.alert.hidden = false;
    els.alert.className = 'alert ' + (ok ? 'ok' : 'err');
    els.alert.textContent = msg;
    clearTimeout(showAlert._t);
    showAlert._t = setTimeout(() => { els.alert.hidden = true; }, 6000);
  }

  function recalc() {
    const L = parseFloat(els.largo.value), W = parseFloat(els.ancho.value), H = parseFloat(els.alto.value);
    if ([L, W, H].every((v) => Number.isFinite(v) && v > 0)) {
      const vol = L * W * H;
      els.volumen.value = vol.toFixed(1);
      els.kvVol.textContent = (vol / VOL_FACTOR).toFixed(2) + ' kg vol.';
    } else {
      els.volumen.value = '';
      els.kvVol.textContent = '—';
    }
    els.kvOp.textContent = els.operador.value || '—';
  }
  ['operador', 'largo', 'ancho', 'alto'].forEach((id) => $(id).addEventListener('input', recalc));

  async function checkEdge() {
    try {
      const ctrl = new AbortController();
      const t = setTimeout(() => ctrl.abort(), 2500);
      const r = await fetch(EDGE_URL + '/health', { signal: ctrl.signal });
      clearTimeout(t);
      if (!r.ok) throw new Error('HTTP ' + r.status);
      els.edge.dataset.state = 'ok';
      els.edgeText.textContent = 'Edge: conectado';
    } catch {
      els.edge.dataset.state = 'fail';
      els.edgeText.textContent = 'Edge: sin conexión (inicia :8000)';
    }
  }

  // Trigger principal: petición asíncrona al servicio local + autocompletado real-time.
  async function capturar() {
    els.btnCap.disabled = true;
    els.btnCap.innerHTML = '⏳ Leyendo cámara 3D + báscula…';
    try {
      const r = await fetch(EDGE_URL + '/capturar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ operador: els.operador.value || null }),
      });
      if (!r.ok) {
        const txt = await r.text();
        throw new Error('Edge HTTP ' + r.status + ' · ' + txt.slice(0, 200));
      }
      const d = await r.json();
      // Contrato: { peso_kg, largo_cm, ancho_cm, alto_cm, ... }
      els.peso.value = Number(d.peso_kg).toFixed(3);
      els.largo.value = Number(d.largo_cm).toFixed(1);
      els.ancho.value = Number(d.ancho_cm).toFixed(1);
      els.alto.value = Number(d.alto_cm).toFixed(1);
      recalc();
      els.folio.textContent = d.folio || '—';
      $('kvFuente').textContent = (d.fuente || 'edge-mock v1') + (d.calibrado ? ' · calibrado' : '');
      els.out.hidden = false;
      els.time.textContent = '· ' + new Date().toLocaleTimeString();
      els.json.textContent = JSON.stringify(d, null, 2);
      showAlert('Lectura Edge aplicada: ' + d.peso_kg + ' kg · ' + d.largo_cm + '×' + d.ancho_cm + '×' + d.alto_cm + ' cm.', true);
    } catch (e) {
      console.error(e);
      showAlert('No se pudo leer el Edge. Verifica que corre en ' + EDGE_URL + ' (uvicorn main:app). Detalle: ' + e.message, false);
    } finally {
      els.btnCap.disabled = false;
      els.btnCap.innerHTML = '<span class="btn-icon">◉</span> Capturar Empaque';
      checkEdge();
    }
  }

  async function guardar(e) {
    e.preventDefault();
    const payload = {
      operador: els.operador.value.trim(),
      fecha: els.fecha.value,
      peso_kg: parseFloat(els.peso.value),
      largo_cm: parseFloat(els.largo.value),
      ancho_cm: parseFloat(els.ancho.value),
      alto_cm: parseFloat(els.alto.value),
      folio_edge: els.folio.textContent !== '—' ? els.folio.textContent : null,
    };
    if (!payload.operador || ![payload.peso_kg, payload.largo_cm, payload.ancho_cm, payload.alto_cm].every((v) => Number.isFinite(v) && v > 0)) {
      showAlert('Completa operador, peso y dimensiones (> 0) antes de guardar. Usa “Capturar Empaque” o captura manual.', false);
      return;
    }
    try {
      const r = await fetch('api/guardar_empaque.php', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
      });
      const d = await r.json();
      if (!r.ok || !d.ok) throw new Error(d.error || ('HTTP ' + r.status));
      els.folio.textContent = d.registro.folio;
      showAlert('Registro guardado en ERP · folio ' + d.registro.folio, true);
      loadHist();
    } catch (err) {
      showAlert('Error guardando en ERP: ' + err.message, false);
    }
  }

  async function loadHist() {
    try {
      const r = await fetch('api/listar_empaques.php');
      const d = await r.json();
      if (!d.ok || !d.registros.length) {
        els.hist.innerHTML = '<tr><td colspan="5" class="muted">Sin registros.</td></tr>';
        return;
      }
      els.hist.innerHTML = d.registros.slice(-12).reverse().map((x) =>
        '<tr><td>' + x.folio + '</td><td>' + x.fecha + '</td><td>' +
        String(x.operador).replace(/[<>&]/g, '') + '</td><td>' + x.peso_kg +
        '</td><td>' + x.largo_cm + '×' + x.ancho_cm + '×' + x.alto_cm + '</td></tr>'
      ).join('');
    } catch { /* ERP sin PHP corriendo: se ignora en demo estática */ }
  }

  els.btnCap.addEventListener('click', capturar);
  els.form.addEventListener('submit', guardar);
  $('btnLimpiar').addEventListener('click', () => {
    els.form.reset();
    els.fecha.valueAsDate = new Date();
    els.out.hidden = true; recalc();
  });
  $('btnReloadHist').addEventListener('click', loadHist);

  recalc(); checkEdge(); loadHist();
  setInterval(checkEdge, 15000);
})();

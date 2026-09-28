<?php
// api/guardar_empaque.php — Handler ERP: persiste registros (JSON plano, sin BD para demo).
header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Headers: Content-Type');
header('Access-Control-Allow-Methods: POST, OPTIONS');
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') { http_response_code(204); exit; }
if ($_SERVER['REQUEST_METHOD'] !== 'POST') { http_response_code(405); echo json_encode(['ok'=>false,'error'=>'Solo POST']); exit; }

$raw = file_get_contents('php://input');
$data = json_decode($raw, true);
if (!is_array($data)) { http_response_code(400); echo json_encode(['ok'=>false,'error'=>'JSON inválido']); exit; }

$operador = trim($data['operador'] ?? '');
$fecha    = trim($data['fecha'] ?? date('Y-m-d'));
$peso  = filter_var($data['peso_kg']  ?? null, FILTER_VALIDATE_FLOAT);
$largo = filter_var($data['largo_cm'] ?? null, FILTER_VALIDATE_FLOAT);
$ancho = filter_var($data['ancho_cm'] ?? null, FILTER_VALIDATE_FLOAT);
$alto  = filter_var($data['alto_cm']  ?? null, FILTER_VALIDATE_FLOAT);

if ($operador === '' || $peso === false || $largo === false || $ancho === false || $alto === false
    || $peso <= 0 || $largo <= 0 || $ancho <= 0 || $alto <= 0) {
    http_response_code(422);
    echo json_encode(['ok'=>false,'error'=>'operador, peso_kg, largo/ancho/alto_cm requeridos y > 0']);
    exit;
}

$dir = __DIR__ . '/../data';
if (!is_dir($dir)) mkdir($dir, 0775, true);
$file = $dir . '/empaques.json';
$all = file_exists($file) ? (json_decode(file_get_contents($file), true) ?: []) : [];

$folio = 'EMP-' . date('Ymd') . '-' . str_pad(count($all) + 1, 4, '0', STR_PAD_LEFT);
$registro = [
    'folio'      => $folio,
    'folio_edge' => $data['folio_edge'] ?? null,
    'operador'   => $operador,
    'fecha'      => $fecha,
    'peso_kg'    => round($peso, 3),
    'largo_cm'   => round($largo, 1),
    'ancho_cm'   => round($ancho, 1),
    'alto_cm'    => round($alto, 1),
    'volumen_cm3'=> round($largo * $ancho * $alto, 1),
    'created_at' => date('c'),
];
$all[] = $registro;
file_put_contents($file, json_encode($all, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE), LOCK_EX);
echo json_encode(['ok'=>true,'registro'=>$registro], JSON_UNESCAPED_UNICODE);

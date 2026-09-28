<?php
// api/listar_empaques.php — GET historial para la tabla del ERP.
header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
$file = __DIR__ . '/../data/empaques.json';
$all = file_exists($file) ? (json_decode(file_get_contents($file), true) ?: []) : [];
echo json_encode(['ok'=>true,'total'=>count($all),'registros'=>$all], JSON_UNESCAPED_UNICODE);

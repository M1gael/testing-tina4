<?php
// Calls Tina4\Server::parseMultipartBody, the parser the socket server uses (Server.php:1326),
// on the body curl sends for: -F tags[]=red -F tags[]=blue -F colour[]=green -F name=x
require_once $argv[1] . '/vendor/autoload.php';
$b = 'XyZ';
$part = fn($n, $v) => "--$b\r\nContent-Disposition: form-data; name=\"$n\"\r\n\r\n$v\r\n";
$body = $part('tags[]', 'red') . $part('tags[]', 'blue') . $part('colour[]', 'green') . $part('name', 'x') . "--$b--\r\n";
echo json_encode(\Tina4\Server::parseMultipartBody($body, "multipart/form-data; boundary=$b")), "\n";

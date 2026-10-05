<?php
// Same peers as peer.php, but on an ERROR page (a route that throws), 404, and a
// plain HTML page: where does the toolbar markup go?
//   TREE=<tina4-php tree> TINA4_DEBUG=true php boom.php
require_once getenv('TREE') . '/vendor/autoload.php';
$app = new \Tina4\App(basePath: __DIR__ . '/app');
$hit = function (string $path, string $peer, string $host) use ($app): array {
    $r = $app(['method' => 'GET', 'path' => $path, 'headers' => ['host' => $host, 'accept' => 'text/html'],
        'remote_ip' => $peer, 'ip' => $peer]);
    return [$r->getStatusCode() ?? 200, (string)$r->getBody()];
};
printf("%-14s %-12s %-6s %s\n", 'peer', 'page', 'status', 'dev toolbar elements in body');
foreach (['127.0.0.1' => '127.0.0.1:7145', '172.17.0.1' => '172.17.0.1:7145', '203.0.113.7' => '203.0.113.7:7145'] as $ip => $host) {
    foreach (['/hello' => 'html page', '/boom' => '500 overlay', '/missing' => '404 page'] as $path => $what) {
        [$code, $body] = $hit($path, $ip, $host);
        printf("%-14s %-12s %-6s %d (trace shown: %s)\n", $ip, $what, $code, substr_count($body, 'id="tina4-dev-toolbar"'),
            str_contains($body, 'boom from a route') ? 'yes' : 'no');
    }
}

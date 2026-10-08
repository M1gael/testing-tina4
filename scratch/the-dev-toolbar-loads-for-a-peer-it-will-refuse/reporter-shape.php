<?php
// The shape tina4-php#279 reports: the browser dials a published port on the
// host's loopback (Host: localhost:8797, which the host allow-list accepts), and
// the app sees the Docker gateway (or a LAN box) as the socket peer, which the
// peer gate refuses. Only the PEER differs between rows.
//   TREE=<tina4-php tree> TINA4_DEBUG=true php reporter-shape.php
require_once getenv('TREE') . '/vendor/autoload.php';
$app = new \Tina4\App(basePath: __DIR__ . '/app');
$hit = function (string $path, string $peer) use ($app): array {
    $r = $app(['method' => 'GET', 'path' => $path, 'headers' => ['host' => 'localhost:8797'], 'remote_ip' => $peer, 'ip' => $peer]);
    return [$r->getStatusCode() ?? 200, (string) $r->getBody()];
};
printf("%-12s %-22s %-22s %-22s %s\n", 'peer', '/hello', '/nothing-here (404)', '/boom (500 overlay)', '/__dev/toolbar.js');
foreach (['127.0.0.1', '172.17.0.1', '192.168.0.50'] as $peer) {
    $cells = [];
    foreach (['/hello', '/nothing-here', '/boom'] as $path) {
        [$status, $body] = $hit($path, $peer);
        $cells[] = sprintf('%d toolbar=%d', $status, substr_count($body, 'id="tina4-dev-toolbar"'));
    }
    [$status, $body] = $hit('/__dev/toolbar.js', $peer);
    preg_match('/refused \(([^)]+)\)/', $body, $m);
    printf("%-12s %-22s %-22s %-22s %d %s\n", $peer, $cells[0], $cells[1], $cells[2], $status, $m[1] ?? '');
}

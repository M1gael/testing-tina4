<?php
// What does a NON-LOOPBACK peer get from a TINA4_DEBUG app?
//
// Driven through App::__invoke(array), the framework's own direct entry point
// (its docblock: "Direct (PHP-FPM / php -S): $app();"). The array form carries
// `remote_ip` straight to Request::$remoteIp -- the RAW socket peer the
// dev-admin gate reads -- so a peer can be varied without binding a debug
// server to a network interface.
//
// Each cell sends the Host header a browser would really send: the address the
// client dialled. That matters -- DevAdmin::guardRequest() runs THREE gates in
// order (host allow-list, same-origin, loopback peer) and a harness that sends
// one fixed Host cannot tell which of them refused.
//
//   TREE=<tina4-php tree> TINA4_DEBUG=true php peer.php
require_once getenv('TREE') . '/vendor/autoload.php';

$app = new \Tina4\App(basePath: __DIR__ . '/app');

/** One request, as a browser dialling $host from $peer. Returns [status, body]. */
$hit = function (string $path, string $peer, string $host, array $headers = []) use ($app): array {
    $r = $app([
        'method' => 'GET',
        'path' => $path,
        'headers' => array_merge(['host' => $host], $headers),
        'remote_ip' => $peer,
        'ip' => $peer,
    ]);
    return [$r->getStatusCode() ?? 200, (string)$r->getBody()];
};
/** The gate that refused, from the dev-admin error body. */
$why = function (string $body): string {
    if (preg_match('/dev-admin: refused \(([^)]+)\)/', $body, $m)) {
        return $m[1];
    }
    return str_contains($body, '"routes"') ? 'ALLOWED' : 'other';
};

$cells = [
    'loopback    127.0.0.1'    => ['127.0.0.1',    '127.0.0.1:7145'],
    'docker gw   172.17.0.1'   => ['172.17.0.1',   '172.17.0.1:7145'],
    'LAN         192.168.0.50' => ['192.168.0.50', '192.168.0.50:7145'],
];

printf("%-26s  %-26s  %s\n", 'peer (as its browser dials it)', 'GET /hello', 'GET /__dev/api/routes');
printf("%-26s  %-26s  %s\n", str_repeat('-', 26), str_repeat('-', 26), str_repeat('-', 34));
foreach ($cells as $label => [$ip, $host]) {
    [$code, $body] = $hit('/hello', $ip, $host);
    $toolbar = str_contains($body, '__dev') ? 'toolbar INJECTED' : 'no toolbar';
    [$dcode, $dbody] = $hit('/__dev/api/routes', $ip, $host);
    printf("%-26s  %s  %-18s  %s %s\n", $label, $code, $toolbar, $dcode, $why($dbody));
}

echo "\nEvery documented opt-in, for the docker-gateway peer dialling 172.17.0.1:\n";
putenv('TINA4_HOST=172.17.0.1'); $_ENV['TINA4_HOST'] = '172.17.0.1';
putenv('TINA4_MCP_TOKEN=s3cret'); $_ENV['TINA4_MCP_TOKEN'] = 's3cret';
foreach ([
    'TINA4_HOST only'                                  => [],
    'TINA4_HOST + TINA4_MCP_TOKEN, no header (browser)' => [],
    'TINA4_HOST + TINA4_MCP_TOKEN, Bearer   (curl)'     => ['authorization' => 'Bearer s3cret'],
    'TINA4_HOST + TINA4_MCP_TOKEN, X-MCP-Token (curl)'  => ['x-mcp-token' => 's3cret'],
] as $label => $h) {
    if ($label === 'TINA4_HOST only') {
        putenv('TINA4_MCP_TOKEN'); unset($_ENV['TINA4_MCP_TOKEN']);
    } else {
        putenv('TINA4_MCP_TOKEN=s3cret'); $_ENV['TINA4_MCP_TOKEN'] = 's3cret';
    }
    [$dcode, $dbody] = $hit('/__dev/api/routes', '172.17.0.1', '172.17.0.1:7145', $h);
    printf("  %-52s %s %s\n", $label, $dcode, $why($dbody));
}

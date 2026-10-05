<?php
// Is there ANY way, from outside the framework, to shorten the 30s?
// Each hatch is tried for real and reported.
require_once getenv('TREE') . '/vendor/autoload.php';
$port = (int)($argv[1] ?? 0);

$mk = fn() => new \Tina4\Messenger(host: '127.0.0.1', port: $port, username: 'u@e.com',
    password: 'x', fromAddress: 'f@e.com', encryption: 'none');

$time = function (callable $f): float { $t = microtime(true); $f(); return microtime(true) - $t; };

// 1. php.ini default_socket_timeout -- ignored, because the timeout is passed
//    explicitly to stream_socket_client and stream_set_timeout.
ini_set('default_socket_timeout', '2');
printf("default_socket_timeout=2       -> %.1fs\n", $time(fn() => $mk()->send('t@e.com', 's', 'b')));

// 2. A subclass setting the property. `private` puts it out of reach: the child
//    declares its OWN $timeout and the parent keeps reading its own.
eval('namespace Tina4; class ShortMessenger extends Messenger { public function __construct(...$a) { parent::__construct(...$a); $this->timeout = 2; } }');
try {
    $sub = new \Tina4\ShortMessenger(host: '127.0.0.1', port: $port, username: 'u@e.com',
        password: 'x', fromAddress: 'f@e.com', encryption: 'none');
    printf("subclass sets \$timeout = 2    -> %.1fs\n", $time(fn() => $sub->send('t@e.com', 's', 'b')));
} catch (\Throwable $e) {
    printf("subclass sets \$timeout = 2    -> %s\n", get_class($e) . ': ' . $e->getMessage());
}

// 3. Reflection -- works, but it is not an API, and no application should need it.
$r = $mk();
$p = new \ReflectionProperty(\Tina4\Messenger::class, 'timeout');
$p->setValue($r, 2);
printf("ReflectionProperty::setValue(2) -> %.1fs\n", $time(fn() => $r->send('t@e.com', 's', 'b')));

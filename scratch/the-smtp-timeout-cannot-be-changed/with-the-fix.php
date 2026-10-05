<?php
// Against a FIXED tree: both levers, and the garbage cases.
require_once getenv('TREE') . '/vendor/autoload.php';
$port = (int)($argv[1] ?? 0);
$time = function (callable $f): float { $t = microtime(true); $f(); return microtime(true) - $t; };
$mk = function (array $extra = []) use ($port) {
    return new \Tina4\Messenger(...($extra + ['host' => '127.0.0.1', 'port' => $port,
        'username' => 'u@e.com', 'password' => 'x', 'fromAddress' => 'f@e.com',
        'encryption' => 'none']));
};
$send = fn($m) => $m->send('t@e.com', 's', 'b');

printf("constructor timeout: 2      -> %.1fs\n", $time(fn() => $send($mk(['timeout' => 2]))));
putenv('TINA4_MAIL_TIMEOUT=3'); $_ENV['TINA4_MAIL_TIMEOUT'] = '3';
printf("TINA4_MAIL_TIMEOUT=3        -> %.1fs\n", $time(fn() => $send($mk())));
printf("constructor 2 beats env 3   -> %.1fs\n", $time(fn() => $send($mk(['timeout' => 2]))));
putenv('TINA4_MAIL_TIMEOUT=banana'); $_ENV['TINA4_MAIL_TIMEOUT'] = 'banana';
$r = new ReflectionProperty(\Tina4\Messenger::class, 'timeout');
printf("TINA4_MAIL_TIMEOUT=banana   -> resolves to %ds (the default)\n", $r->getValue($mk()));
putenv('TINA4_MAIL_TIMEOUT=0'); $_ENV['TINA4_MAIL_TIMEOUT'] = '0';
printf("TINA4_MAIL_TIMEOUT=0        -> resolves to %ds (the default)\n", $r->getValue($mk()));
putenv('TINA4_MAIL_TIMEOUT'); unset($_ENV['TINA4_MAIL_TIMEOUT']);
printf("nothing set                 -> resolves to %ds\n", $r->getValue($mk()));
try { $mk(['timeout' => 0]); echo "constructor 0               -> ACCEPTED (wrong)\n"; }
catch (\Throwable $e) { printf("constructor 0               -> %s: %s\n", get_class($e), $e->getMessage()); }

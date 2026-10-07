<?php
// php tls-stalls.php <tree> <port> <tls|starttls> [timeout-env-seconds]
require $argv[1] . '/vendor/autoload.php';
if (isset($argv[4])) { putenv('TINA4_MAIL_TIMEOUT=' . $argv[4]); }
$t = microtime(true);
try {
    $r = (new \Tina4\Messenger(host: '127.0.0.1', port: (int)$argv[2], username: 'u@example.com', password: 'p',
        fromAddress: 'u@example.com', encryption: $argv[3]))->send('to@example.com', 's', 'b');
    $out = 'success=' . var_export($r['success'] ?? null, true) . ' ' . ($r['message'] ?? '');
} catch (\Throwable $e) { $out = get_class($e) . ': ' . $e->getMessage(); }
printf("%-9s elapsed=%.1fs  %s\n", $argv[3], microtime(true) - $t, substr(str_replace("\n", ' ', $out), 0, 110));

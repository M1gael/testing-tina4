<?php
// How long does one Messenger::send() take against a wedged SMTP relay, and
// can anything the public API offers make it shorter?
//
//   TREE=<tina4-php tree> php timeout.php <port>
require_once getenv('TREE') . '/vendor/autoload.php';

$port = (int)($argv[1] ?? 0);

// Every knob the public surface offers: the constructor's named parameters and
// the TINA4_MAIL_* env. Neither carries a timeout; TINA4_MAIL_TIMEOUT is set
// here to show it is simply not read.
putenv('TINA4_MAIL_TIMEOUT=2');
$_ENV['TINA4_MAIL_TIMEOUT'] = '2';

$mail = new \Tina4\Messenger(
    host: '127.0.0.1',
    port: $port,
    username: 'user@example.com',
    password: 'x',
    fromAddress: 'from@example.com',
    encryption: 'none',
);

$ref = new \ReflectionClass(\Tina4\Messenger::class);
$prop = $ref->hasProperty('timeout') ? $ref->getProperty('timeout') : null;
printf("timeout property: %s, visibility=%s, value=%ds\n",
    $prop ? 'present' : 'ABSENT',
    $prop === null ? '-' : ($prop->isPrivate() ? 'private' : ($prop->isProtected() ? 'protected' : 'public')),
    $prop === null ? -1 : $prop->getValue($mail));

$ctor = $ref->getConstructor();
$names = array_map(fn($p) => $p->getName(), $ctor->getParameters());
printf("constructor parameters: %s\n", implode(', ', $names));
printf("a timeout parameter:    %s\n", in_array('timeout', $names, true) ? 'YES' : 'NO');
$setters = array_filter(
    array_map(fn($m) => $m->getName(), $ref->getMethods(\ReflectionMethod::IS_PUBLIC)),
    fn($n) => stripos($n, 'timeout') !== false
);
printf("a public timeout setter: %s\n", $setters ? implode(', ', $setters) : 'NONE');

$t = microtime(true);
try {
    $r = $mail->send('to@example.com', 'subject', 'body');
    $outcome = 'send() returned success=' . var_export($r['success'] ?? null, true)
        . ', message=' . substr((string)($r['message'] ?? ''), 0, 90);
} catch (\Throwable $e) {
    $outcome = get_class($e) . ': ' . substr($e->getMessage(), 0, 90);
}
printf("elapsed: %.1fs  (%s)\n", microtime(true) - $t, $outcome);

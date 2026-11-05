<?php
// Usage: php probe_php_attacks.php <tina4-php src root> <latest|earliest>
// A) a consumer that starts BEFORE its topic exists must still see the first record;
// B) deadLetters() must list a job already on <topic>.dead_letter under any policy.
[$_, $root, $reset] = $argv;
require "$root/Tina4/Queue/QueueBackend.php";
require "$root/Tina4/Queue/KafkaBackend.php";
use Tina4\Queue\KafkaBackend;
$b = getenv('TINA4_KAFKA_BROKERS');
putenv("TINA4_KAFKA_AUTO_OFFSET_RESET=$reset");
$t = 'frq01_phpa_' . bin2hex(random_bytes(4));
$cons = new KafkaBackend(['brokers' => $b]); $prod = new KafkaBackend(['brokers' => $b]);
$seen = [$cons->dequeue($t)['n'] ?? null];
$prod->enqueue($t, ['n' => 'first']);
for ($k = 0; $k < 4; $k++) { $m = $cons->dequeue($t); $seen[] = $m['n'] ?? null; if ($m) break; }
echo "A reset=$reset seen=" . json_encode($seen) . ' VERDICT ' . (in_array('first', $seen, true) ? 'PASS' : 'FAIL (first record on a new topic skipped)') . "\n";
$t2 = 'frq01_phpd_' . bin2hex(random_bytes(4));
$prod->enqueue("$t2.dead_letter", ['id' => 'dead-1', 'attempts' => 9]);
$fresh = new KafkaBackend(['brokers' => $b]);
$ids = array_map(fn($m) => $m['id'] ?? null, $fresh->deadLetters($t2));
echo "B reset=$reset deadLetters=" . json_encode($ids) . ' VERDICT ' . (in_array('dead-1', $ids, true) ? 'PASS' : 'FAIL') . "\n";

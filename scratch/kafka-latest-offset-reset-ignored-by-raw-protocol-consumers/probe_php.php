<?php
// Usage: php probe_php.php <tina4-php src root> <latest|earliest>
// Same scenario as probe_py.py, through Tina4\Queue\KafkaBackend (raw protocol).
[$_, $root, $reset] = $argv;
require "$root/Tina4/Queue/QueueBackend.php";
require "$root/Tina4/Queue/KafkaBackend.php";
use Tina4\Queue\KafkaBackend;
$brokers = getenv('TINA4_KAFKA_BROKERS');
$topic = 'frq01_php_' . bin2hex(random_bytes(4));
putenv('TINA4_KAFKA_AUTO_OFFSET_RESET');
$prod = new KafkaBackend(['brokers' => $brokers, 'group_id' => 'frq01_prod']);
for ($i = 0; $i < 3; $i++) $prod->enqueue($topic, ['n' => "old-$i"]);
putenv("TINA4_KAFKA_AUTO_OFFSET_RESET=$reset");
$cons = new KafkaBackend(['brokers' => $brokers, 'group_id' => 'frq01_grp_' . bin2hex(random_bytes(4))]);
$seen = [];
$m = $cons->dequeue($topic); $seen[] = $m['n'] ?? null;
$prod->enqueue($topic, ['n' => 'new']);
for ($k = 0; $k < 6; $k++) { $m = $cons->dequeue($topic); $seen[] = $m['n'] ?? null; if (($m['n'] ?? '') === 'new') break; }
echo "php[raw] reset=$reset seen=" . json_encode($seen) . "\n";
$old = array_filter($seen, fn($s) => $s && str_starts_with($s, 'old'));
if ($reset === 'latest') echo 'VERDICT ' . (!$old && in_array('new', $seen, true) ? 'PASS' : ($old ? 'FAIL (replayed backlog)' : 'ERROR (new not seen)')) . "\n";
else echo 'VERDICT ' . ($seen[0] === 'old-0' ? 'PASS' : 'FAIL') . "\n";

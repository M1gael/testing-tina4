<?php
// Does a failed save() inside a caller's explicit transaction roll back the caller's earlier, successful save()?
// usage: php nested-rollback.php <tina4-php tree> <work dir>
require $argv[1] . '/vendor/autoload.php';

class Company extends \Tina4\ORM
{
    public string $tableName = 'company';
    public string $primaryKey = 'id';
}

[, $tree, $work] = $argv;
$file = $work . '/app.db';
@unlink($file);
(new PDO('sqlite:' . $file))->exec('CREATE TABLE company (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)');
$db = new \Tina4\Database\Database('sqlite:///' . $file, true, '', '', 0);
$fresh = static fn(): int => (int) (new PDO('sqlite:' . $file))->query('SELECT COUNT(*) FROM company')->fetchColumn();
$same = static fn(): int => (int) $db->fetchOne('SELECT COUNT(*) AS n FROM company')['n'];

$db->startTransaction();
$a = new Company(['name' => 'first']);
$a->setDb($db);
$ra = $a->save();
printf("RESULT first-save      returned=%s same=%d\n", $ra === false ? 'false' : 'model', $same());

$b = new Company(['name' => null]);
$b->setDb($db);
$rb = $b->save();
printf("RESULT bad-save        returned=%s err=%s same=%d\n", $rb === false ? 'false' : 'model', $b->lastError ?? '-', $same());

try {
    $db->commit();
    echo "RESULT outer-commit     ok\n";
} catch (\Throwable $e) {
    echo "RESULT outer-commit     threw " . substr($e->getMessage(), 0, 120) . "\n";
}
printf("RESULT after           same=%d fresh=%d\n", $same(), $fresh());

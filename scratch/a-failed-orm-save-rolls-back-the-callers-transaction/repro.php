<?php
// Does ORM save() on SQLite reach the database file, when a raw INSERT does?
// usage: php repro.php <tina4-php tree> <work dir> <autocommit: 1|0|null> <plain|outer|outer-rollback>
// plain: save() alone. outer: an explicit startTransaction() is open around save().
require $argv[1] . '/vendor/autoload.php';

class Company extends \Tina4\ORM
{
    public string $tableName = 'company';
    public string $primaryKey = 'id';
}

[, $tree, $work, $ac] = $argv;
$mode = $argv[4] ?? "plain";
$file = $work . '/app.db';
@unlink($file);
$autoCommit = $ac === 'null' ? null : $ac === '1';

(new PDO('sqlite:' . $file))->exec('CREATE TABLE company (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)');
$db = new \Tina4\Database\Database("sqlite:///" . $file, $autoCommit, "", "", (int) ($argv[5] ?? 0));

// An independent connection: sees only what is committed to the file.
$fresh = static fn(): int => (int) (new PDO('sqlite:' . $file))->query('SELECT COUNT(*) FROM company')->fetchColumn();
$same = static fn(): int => (int) $db->fetchOne('SELECT COUNT(*) AS n FROM company')['n'];

$db->exec("INSERT INTO company (name) VALUES ('raw')");
printf("RESULT raw-insert       same=%d fresh=%d\n", $same(), $fresh());

if ($mode !== 'plain') {
    $db->startTransaction();
}
$c = new Company(['name' => 'orm']);
$c->setDb($db);
$r = $c->save();
printf("RESULT %-16s returned=%s id=%s err=%s same=%d fresh=%d\n", $mode . '-save',
    $r === false ? 'false' : 'model', var_export($c->id, true), $c->lastError ?? '-', $same(), $fresh());

if ($mode === 'outer') {
    $db->commit();
    printf("RESULT outer-commit     same=%d fresh=%d\n", $same(), $fresh());
} elseif ($mode === 'outer-rollback') {
    $db->rollback();
    printf("RESULT outer-rollback   same=%d fresh=%d\n", $same(), $fresh());
}

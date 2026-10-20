<?php
// Does save() on a model that declares fields silently drop a value assigned to
// an undeclared property that names one of the table's real columns?
// usage: php repro.php <tina4-php tree> <work dir>
require $argv[1] . '/vendor/autoload.php';

// Declares only $name: its column set is closed (ADR-0069 G2).
class Typed extends \Tina4\ORM
{
    public string $tableName = 'company';
    public string $primaryKey = 'id';
    public ?int $id = null;
    public ?string $name = null;
}

// Declares nothing: resolves dynamic properties against the real columns.
class Plain extends \Tina4\ORM
{
    public string $tableName = 'company';
    public string $primaryKey = 'id';
}

[, $tree, $work] = $argv;
$file = $work . '/app.db';
@unlink($file);
(new PDO('sqlite:' . $file))->exec(
    'CREATE TABLE company (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, login_username TEXT)'
);
$db = new \Tina4\Database\Database('sqlite:///' . $file);
\Tina4\ORM::bindDatabase($db);
$pdo = new PDO('sqlite:' . $file);
$stored = static fn($id) => $id === null ? '-' : var_export(
    $pdo->query('SELECT login_username FROM company WHERE id = ' . (int)$id)->fetchColumn(), true
);
$seed = static function (string $login) use ($pdo): int {
    $pdo->exec("INSERT INTO company (name, login_username) VALUES ('seed', '$login')");
    return (int)$pdo->lastInsertId();
};
$report = static function (string $case, $model, $ok) use ($stored) {
    printf("%-28s save=%-5s stored=%-8s error=%s\n", $case, $ok === false ? 'false' : 'ok',
        $stored($model->id ?? null), $ok === false ? $model->getError() : '-');
};

// A: new typed model, undeclared real column assigned.
$m = new Typed(); $m->setDb($db);
$m->name = 'a'; $m->loginUsername = 'alice';
$report('A new+assign real column', $m, $m->save());

// B: load, save untouched (a column the model does not declare came back on load).
$id = $seed('bob');
$m = new Typed(); $m->setDb($db); $m->load('id = ?', [$id]);
$m->name = 'b2';
$report('B load+save untouched', $m, $m->save());

// C: load, change the undeclared real column.
$id = $seed('carol');
$m = new Typed(); $m->setDb($db); $m->load('id = ?', [$id]);
$m->loginUsername = 'carol2';
$report('C load+change real column', $m, $m->save());

// D: undeclared property naming no column (a join extra) is not a write.
$m = new Typed(); $m->setDb($db);
$m->name = 'd'; $m->companyCount = 3;
$report('D assign non-column', $m, $m->save());

// E: untyped model writes the real column.
$m = new Plain(); $m->setDb($db);
$m->name = 'e'; $m->loginUsername = 'eve';
$report('E untyped assign', $m, $m->save());

// F: fill() with the snake_case column on a new typed model.
$m = new Typed(); $m->setDb($db);
$m->fill(['name' => 'f', 'login_username' => 'frank']);
$report('F fill real column', $m, $m->save());

// G: load, re-assign the same value.
$id = $seed('gail');
$m = new Typed(); $m->setDb($db); $m->load('id = ?', [$id]);
$m->loginUsername = 'gail';
$report('G load+same value', $m, $m->save());

// H: rows from select()/find() are hydrated the same way; save one untouched.
$id = $seed('hank');
$h = Typed::findById($id);
$h->name = 'h2';
$report('H findById+save untouched', $h, $h->save());

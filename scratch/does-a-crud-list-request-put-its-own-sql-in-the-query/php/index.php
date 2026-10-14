<?php
// Stock tina4-php v3: AutoCrud + Crud::toCrud over a 3-row sqlite table.
require_once getenv('TINA4_PHP_TREE') . '/vendor/autoload.php';

use Tina4\ORM;
use Tina4\AutoCrud;
use Tina4\Crud;
use Tina4\Router;
use Tina4\Database\SQLite3Adapter;

class Person extends ORM
{
    public string $tableName = 'people';
    public string $primaryKey = 'id';
    public ?int $id = null;
    public ?string $name = null;
    public ?int $age = null;
}

$dbFile = __DIR__ . '/people.db';
$fresh = !file_exists($dbFile);
$db = new SQLite3Adapter($dbFile);
if ($fresh) {
    $db->exec('CREATE TABLE people (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, age INTEGER)');
    foreach ([["Ann", 30], ["O'Brien", 40], ["Zed", 25]] as [$n, $a]) {
        $db->exec('INSERT INTO people (name, age) VALUES (?, ?)', [$n, $a]);
    }
    $db->exec('CREATE TABLE secrets (id INTEGER PRIMARY KEY, token TEXT)');
    $db->exec("INSERT INTO secrets (id, token) VALUES (1, 'TOPSECRET')");
    $db->commit();
}
ORM::bindDatabase($db);

$app = new \Tina4\App(basePath: __DIR__);

$crud = new AutoCrud($db);
$crud->register(Person::class, true);
$crud->generateRoutes();

Router::get('/grid', fn ($request, $response) => $response->html(Crud::toCrud($request, ['model' => Person::class])))->noAuth();
Router::get('/gridsql', fn ($request, $response) => $response->html(Crud::toCrud($request, ['model' => Person::class, 'sql' => 'SELECT id, name, age FROM people'])))->noAuth();

$app->run();

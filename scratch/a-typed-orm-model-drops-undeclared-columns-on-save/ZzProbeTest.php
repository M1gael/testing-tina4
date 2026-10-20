<?php
use PHPUnit\Framework\TestCase;

// Declared typed property: the model's column set is closed on 3.13.151.
class ZzTyped extends \Tina4\ORM
{
    public string $tableName = 'zz_widget';
    public string $primaryKey = 'id';
    public ?string $name = null;
}

// No typed public property: every column is dynamic.
class ZzPlain extends \Tina4\ORM
{
    public string $tableName = 'zz_widget';
    public string $primaryKey = 'id';
}

class ZzProbeTest extends TestCase
{
    public function testProbe(): void
    {
        $db = \Tina4\App::getDatabase();
        $db->exec('CREATE TABLE IF NOT EXISTS zz_widget (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, code TEXT)');
        foreach ([ZzTyped::class, ZzPlain::class] as $class) {
            $m = new $class();
            $m->name = 'declared-or-dynamic';
            $m->code = 'dynamic';
            $ok = $m->save();
            $row = $db->fetchOne('SELECT name, code FROM zz_widget WHERE id = ?', [$m->id]);
            echo "\nPROBE {$class}: save=" . ($ok === false ? 'false' : 'model') . " row=" . json_encode($row) . "\n";
        }
        $this->assertTrue(true);
    }
}

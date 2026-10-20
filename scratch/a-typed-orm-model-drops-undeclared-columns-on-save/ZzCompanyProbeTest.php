<?php
// Copy into an airoffices checkout's tests/ and run with vendor/bin/phpunit.
// Seeds a Company the way CompanyLoginServiceTest does, then reads the row back
// by id (did the INSERT commit?) and by login_username (did the column land?).
use PHPUnit\Framework\TestCase;

class ZzCompanyProbeTest extends TestCase
{
    public function testSeedAndReadBack(): void
    {
        $db = \Tina4\App::getDatabase();
        $name = 'zz_inv_' . bin2hex(random_bytes(3));
        $c = new Company();
        $c->name = 'probe';
        $c->loginUsername = $name;
        $c->loginPassword = 'x';
        $c->isActive = 1;
        $c->isDeleted = 0;
        $ok = $c->save();
        $id = $c->id;
        $byId = $db->fetchOne('SELECT login_username, is_active FROM company WHERE id = ?', [$id]);
        $byName = $db->fetchOne('SELECT id FROM company WHERE login_username = ?', [$name]);
        echo "\nPROBE save=" . ($ok === false ? 'false' : 'model') . " id=" . var_export($id, true)
            . " row_by_id=" . json_encode($byId) . " row_by_login=" . json_encode($byName) . "\n";
        $db->exec('DELETE FROM company WHERE id = ?', [$id]);
        $this->assertTrue(true);
    }
}

<?php
// Usage: TREE=<tina4-php tree> PGURL_HOSTPART=postgres@127.0.0.1:5432/postgres php live.php
// A real PostgreSQL: each scheme through Database::create(), through the PDO adapter
// directly, and through TINA4_DATABASE_URL -> App::getDatabase(). A row back is the pass.
require getenv('TREE') . '/vendor/autoload.php';
$rest = getenv('PGURL_HOSTPART') ?: 'postgres@127.0.0.1:5432/postgres';
$one = static function (callable $make): string {
    try {
        $db = $make();
        $row = $db->fetchOne('SELECT 41 + 1 AS answer');
        return 'row answer=' . ($row['answer'] ?? '?') . ' via ' . (new ReflectionClass($db))->getShortName();
    } catch (\Throwable $e) {
        return 'FAILED ' . (new ReflectionClass($e))->getShortName() . ': ' . substr($e->getMessage(), 0, 70);
    }
};
foreach (['postgres', 'postgresql', 'pgsql'] as $scheme) {
    $url = "{$scheme}://{$rest}";
    printf("%-10s Database::create      %s\n", $scheme, $one(fn () => \Tina4\Database\Database::create($url)));
    printf("%-10s PdoPostgresAdapter    %s\n", $scheme, $one(fn () => new \Tina4\Database\PdoPostgresAdapter($url)));
}
putenv("TINA4_DATABASE_URL=pgsql://{$rest}");
printf("%-10s App::getDatabase()    %s\n", 'pgsql env', $one(fn () => \Tina4\App::getDatabase()));

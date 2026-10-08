<?php
// Usage: TREE=<tina4-php tree with vendor/> php prove.php
// Every scheme DatabaseUrl accepts, put through Database::create(). A refusal by
// scheme is the bug; a connect attempt (refused, nothing listens) is the pass.
require getenv('TREE') . '/vendor/autoload.php';
// A sqlite:// URL is a file path: run where its file can be thrown away.
$work = sys_get_temp_dir() . '/pgsql-alias-' . bin2hex(random_bytes(4));
mkdir($work);
chdir($work);
register_shutdown_function(static fn () => shell_exec('rm -rf ' . escapeshellarg($work)));
$aliases = (new ReflectionClassConstant(\Tina4\DatabaseUrl::class, 'ENGINE_ALIASES'))->getValue();
printf("tree %s\n", trim((string) shell_exec('git -C ' . escapeshellarg(getenv('TREE')) . ' rev-parse --short HEAD')));
foreach (array_keys($aliases) as $scheme) {
    $url = "{$scheme}://127.0.0.1:1/x";
    try {
        $engine = (new \Tina4\DatabaseUrl($url))->engine;
    } catch (\Throwable $e) {
        $engine = 'parse error';
    }
    try {
        \Tina4\Database\Database::create($url);
        $verdict = 'opened';
    } catch (\Throwable $e) {
        $verdict = str_contains($e->getMessage(), 'Unsupported database scheme') ? 'REFUSED BY SCHEME' : 'attempted (' . (new ReflectionClass($e))->getShortName() . ')';
    }
    printf("%-12s DatabaseUrl engine %-10s Database::create: %s\n", $scheme, $engine, $verdict);
}

<?php
// TREE: the tina4-php source tree to run (prove.sh sets it); its vendor/ needs composer install.
require_once getenv('TREE') . '/vendor/autoload.php';
$app = new \Tina4\App(basePath: __DIR__);
$app->handle();

<?php
require_once "./vendor/autoload.php";

// OB_APP=1: the entry file leaves an output buffer open, as many older PHP apps do.
if (getenv('OB_APP') === '1') {
    ob_start();
}

// PRESTART=1: the app starts the native session itself, in its entry file, before
// the router runs (the pattern in the reporter's follow-up comment on issue 253).
if (getenv('PRESTART') === '1') {
    @mkdir(__DIR__ . '/data/sessions-app', 0755, true);
    session_save_path(__DIR__ . '/data/sessions-app');
    session_start();
}

$app = new \Tina4\App(basePath: __DIR__);
$app->handle();

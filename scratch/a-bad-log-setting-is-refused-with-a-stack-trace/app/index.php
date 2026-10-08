<?php
// The front controller from the report: one App per request under php -S.
require getenv('TREE') . '/vendor/autoload.php';
(new \Tina4\App(__DIR__))->handle();

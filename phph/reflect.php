<?php
require 'vendor/autoload.php';
if(class_exists('\Tina4\Debug', true)) {
    $ref = new ReflectionClass('\Tina4\Debug');
    echo 'Found: ' . $ref->getFileName() . PHP_EOL;
} else {
    echo 'Class \Tina4\Debug Not found'.PHP_EOL;
}
if(function_exists('dump')) {
    $ref = new ReflectionFunction('dump');
    echo 'Function dump Found: ' . $ref->getFileName() . PHP_EOL;
} else {
    echo 'Function dump Not found'.PHP_EOL;
}

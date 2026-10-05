<?php
\Tina4\Router::get('/hello', function ($request, $response) {
    return $response('<html><body><h1>hello</h1></body></html>', 200, 'text/html');
})->noAuth();

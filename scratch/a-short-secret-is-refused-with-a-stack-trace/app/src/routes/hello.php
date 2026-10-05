<?php
\Tina4\Router::get('/hello', function ($request, $response) {
    return $response('ok', 200, 'text/plain');
})->noAuth();

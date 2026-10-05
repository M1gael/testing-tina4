<?php
\Tina4\Router::get('/boom', function ($request, $response) {
    throw new \RuntimeException('boom from a route');
})->noAuth();
\Tina4\Router::get('/nothere-page', fn ($request, $response) => $response('<html><body>x</body></html>'))->noAuth();

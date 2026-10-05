<?php
// A throw raised AFTER App::start() has installed the exception handler --
// the control for the boot-secret refusal, which is raised before it.
\Tina4\Router::get('/boom', function ($request, $response) {
    throw new \RuntimeException('a route-level boom');
})->noAuth();

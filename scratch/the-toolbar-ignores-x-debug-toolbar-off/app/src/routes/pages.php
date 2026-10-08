<?php
// The documented opt-out (docs/php/30-dev-tools.md, "Disabling the Toolbar"), on an HTML page.
// Set with ->header(): the page's own example passes a third argument json() does not take.
\Tina4\Router::get('/off', function ($request, $response) {
    $response->header('X-Debug-Toolbar', 'off');
    return $response->html('<html><body><h1>off</h1></body></html>');
})->noAuth();
\Tina4\Router::get('/on', fn ($request, $response) => $response->html('<html><body><h1>on</h1></body></html>'))->noAuth();
// The page's example verbatim (JSON gets no toolbar anyway; this shows whether the header is sent).
\Tina4\Router::get('/doc-example', function ($request, $response) {
    return $response->json(["data" => "no toolbar"], 200, [
        "X-Debug-Toolbar" => "off"
    ]);
})->noAuth();

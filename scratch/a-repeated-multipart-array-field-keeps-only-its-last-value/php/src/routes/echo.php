<?php
\Tina4\Router::post('/echo', fn($request, $response) => $response->json(['body' => $request->body]))->noAuth();
\Tina4\Router::get('/q', fn($request, $response) => $response->json(['query' => $request->query]))->noAuth();

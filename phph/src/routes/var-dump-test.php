<?php use Tina4\Router; Router::get("/api/var-dump-test", function ($request, $response) { var_dump(["test" => "data"]); return $response->json(["ok" => true]); });

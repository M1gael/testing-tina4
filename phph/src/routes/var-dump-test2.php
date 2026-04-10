<?php use Tina4\Router; Router::get("/api/test-dump2", function ($request, $response) { return $response->render("temp_dump.twig", ["data" => ["test" => "data"]]); });

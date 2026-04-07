<?php
use Tina4\Router;
use Tina4\Validator;

// testing request and response objects from chapter 3
Router::get("/api/echo", function ($request, $response) {
    return $response->json([
        "method" => $request->method,
        "path" => $request->path,
        "ip" => $request->ip,
        "headers" => $request->headers,
        "user_agent" => $request->header("User-Agent"),
        "query" => $request->query,
        "cookies" => $request->cookies
    ]);
});

Router::post("/api/echo-body", function ($request, $response) {
    return $response->json([
        "body" => $request->body,
        "content_type" => $request->header("Content-Type")
    ]);
});

// testing validator and sendError
/**
 * @noauth
 */
Router::post("/api/validate", function ($request, $response) {
    $v = new Validator($request->body);
    $v->required("name")->email("email");

    if (!$v->isValid()) {
        $errors = $v->errors();
        return $response->sendError("VALIDATION_FAILED", $errors[0]["message"], 400);
    }

    return $response->json(["message" => "Validation passed"]);
});

// testing response methods
Router::get("/api/redirect-test", function ($request, $response) {
    return $response->redirect("/api/echo");
});

Router::get("/api/cookie-test", function ($request, $response) {
    return $response->cookie("test_cookie", "tina4-rocks", ["maxAge" => 3600])
                    ->json(["message" => "Cookie set"]);
});

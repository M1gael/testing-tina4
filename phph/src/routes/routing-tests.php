<?php
use Tina4\Database\Database;
use Tina4\Router;

// testing basic routes and http methods from chapter 2
Router::get("/hello", function ($request, $response) {
    return $response->json(["message" => "Hello, World!"]);
});

Router::get("/methods", function ($request, $response) {
    return $response->json(["action" => "list all products"]);
});

Router::post("/methods", function ($request, $response) {
    return $response->json(["action" => "create a product"], 201);
});

Router::put("/methods/{id}", function ($request, $response) {
    $id = $request->params["id"];
    return $response->json(["action" => "replace product " . $id]);
});

Router::patch("/methods/{id}", function ($request, $response) {
    $id = $request->params["id"];
    return $response->json(["action" => "update product " . $id]);
});

Router::delete("/methods/{id}", function ($request, $response) {
    $id = $request->params["id"];
    return $response->json(["action" => "delete product " . $id]);
});

// testing path parameters and auto-casting
Router::get("/users/{id}/posts/{postId}", function ($request, $response) {
    $userId = $request->params["id"];
    $postId = $request->params["postId"];

    return $response->json([
        "user_id" => $userId,
        "post_id" => $postId,
        "user_id_type" => gettype($userId),
        "post_id_type" => gettype($postId)
    ]);
});

// testing typed parameters
Router::get("/orders/{id:int}", function ($request, $response) {
    $id = $request->params["id"];
    return $response->json([
        "order_id" => $id,
        "type" => gettype($id)
    ]);
});

Router::get("/files/{filepath:path}", function ($request, $response) {
    $filepath = $request->params["filepath"];
    return $response->json([
        "filepath" => $filepath,
        "type" => gettype($filepath)
    ]);
});

// testing route groups
Router::group("/api/v1", function () {
    Router::get("/status", function ($request, $response) {
        return $response->json(["version" => "1.0"]);
    });
});

// testing middleware
function simpleLogger($request, $response) {
    // lowercase comment: tina4 php middleware doesn't take $next, it's a simple list of observers
    return true; // continue
}

Router::get("/api/middleware-test", function ($request, $response) {
    return $response->json(["message" => "middleware worked"]);
})->middleware(["simpleLogger"]);

// testing decorators
/**
 * @noauth
 */
Router::post("/api/public-post", function ($request, $response) {
    return $response->json(["message" => "this post is public"]);
});

/**
 * @secured
 */
Router::get("/api/secure-get", function ($request, $response) {
    return $response->json(["message" => "this get is secure"]);
});

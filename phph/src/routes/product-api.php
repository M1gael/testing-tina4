<?php
use Tina4\Router;

// testing full crud api for products from chapter 2 exercise
$products = [
    ["id" => 1, "name" => "Wireless Keyboard", "category" => "Electronics", "price" => 79.99, "in_stock" => true],
    ["id" => 2, "name" => "Yoga Mat", "category" => "Fitness", "price" => 29.99, "in_stock" => true],
    ["id" => 3, "name" => "Coffee Grinder", "category" => "Kitchen", "price" => 49.99, "in_stock" => false],
    ["id" => 4, "name" => "Standing Desk", "category" => "Office", "price" => 549.99, "in_stock" => true],
    ["id" => 5, "name" => "Running Shoes", "category" => "Fitness", "price" => 119.99, "in_stock" => true]
];

Router::get("/api/products", function ($request, $response) use (&$products) {
    $category = $request->params["category"] ?? null;
    $result = $products;
    if ($category) {
        $result = array_values(array_filter($products, function($p) use ($category) {
            return strtolower($p["category"]) === strtolower($category);
        }));
    }
    return $response->json($result);
});

Router::get("/api/products/{id:int}", function ($request, $response) use (&$products) {
    $id = $request->params["id"];
    foreach ($products as $product) {
        if ($product["id"] === $id) {
            return $response->json($product);
        }
    }
    return $response->json(["error" => "Product not found"], 404);
});

/**
 * @noauth
 */
Router::post("/api/products", function ($request, $response) use (&$products) {
    $newProduct = $request->body;
    $newProduct["id"] = count($products) + 1;
    $products[] = $newProduct;
    return $response->json($newProduct, 201);
});

/**
 * @noauth
 */
Router::put("/api/products/{id:int}", function ($request, $response) use (&$products) {
    $id = $request->params["id"];
    foreach ($products as &$product) {
        if ($product["id"] === $id) {
            $product = array_merge($product, $request->body);
            return $response->json($product);
        }
    }
    return $response->json(["error" => "Product not found"], 404);
});

/**
 * @noauth
 */
Router::delete("/api/products/{id:int}", function ($request, $response) use (&$products) {
    $id = $request->params["id"];
    foreach ($products as $key => $product) {
        if ($product["id"] === $id) {
            unset($products[$key]);
            return $response->json(null, 204);
        }
    }
    return $response->json(["error" => "Product not found"], 404);
});

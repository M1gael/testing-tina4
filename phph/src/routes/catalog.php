<?php
use Tina4\Router;

// testing catalog page from chapter 4 exercise
Router::get("/catalog", function ($request, $response) {
    $products = [
        ["name" => "Espresso Machine", "category" => "Kitchen", "price" => 299.99, "in_stock" => true, "featured" => true],
        ["name" => "Yoga Mat", "category" => "Fitness", "price" => 29.99, "in_stock" => true, "featured" => false],
        ["name" => "Standing Desk", "category" => "Office", "price" => 549.99, "in_stock" => true, "featured" => true],
        ["name" => "Blender", "category" => "Kitchen", "price" => 89.99, "in_stock" => false, "featured" => false],
        ["name" => "Running Shoes", "category" => "Fitness", "price" => 119.99, "in_stock" => true, "featured" => false],
        ["name" => "Desk Lamp", "category" => "Office", "price" => 39.99, "in_stock" => true, "featured" => true],
        ["name" => "Cast Iron Skillet", "category" => "Kitchen", "price" => 44.99, "in_stock" => true, "featured" => false]
    ];

    $categories = array_unique(array_column($products, "category"));
    sort($categories);

    $activeCategory = $request->params["category"] ?? "";
    $filteredProducts = $products;
    if ($activeCategory !== "") {
        $filteredProducts = array_values(array_filter($products, function($p) use ($activeCategory) {
            return $p["category"] === $activeCategory;
        }));
    }

    return $response->render("catalog.twig", [
        "products" => $filteredProducts,
        "categories" => $categories,
        "active_category" => $activeCategory
    ]);
});

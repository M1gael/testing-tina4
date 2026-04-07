<?php
use Tina4\Router;

// testing image upload exercise from chapter 3
Router::post("/api/images", function ($request, $response) {
    // lowercase comment: check if file was uploaded
    if (empty($request->files["image"])) {
        return $response->json(["error" => "No image file provided. Use field name 'image'."], 400);
    }

    $file = $request->files["image"];

    // lowercase comment: validate file type
    $allowedTypes = ["image/jpeg", "image/png", "image/webp"];
    if (!in_array($file->type, $allowedTypes)) {
        return $response->json([
            "error" => "Invalid file type",
            "received" => $file->type,
            "allowed" => $allowedTypes
        ], 400);
    }

    // lowercase comment: validate file size (max 2mb)
    $maxSize = 2 * 1024 * 1024;
    if ($file->size > $maxSize) {
        return $response->json([
            "error" => "File too large",
            "size_bytes" => $file->size,
            "max_bytes" => $maxSize
        ], 400);
    }

    // lowercase comment: generate unique filename preserving extension
    $extension = pathinfo($file->name, PATHINFO_EXTENSION);
    $savedName = uniqid("img_") . "." . strtolower($extension);
    $uploadDir = __DIR__ . "/../public/uploads"; // adjusted for project structure
    $destination = $uploadDir . "/" . $savedName;

    // lowercase comment: create uploads directory if it does not exist
    if (!is_dir($uploadDir)) {
        mkdir($uploadDir, 0755, true);
    }

    // lowercase comment: move the uploaded file
    rename($file->tmpPath, $destination);

    return $response->json([
        "message" => "Image uploaded successfully",
        "original_name" => $file->name,
        "saved_name" => $savedName,
        "size_kb" => round($file->size / 1024, 1),
        "type" => $file->type,
        "url" => "/uploads/" . $savedName
    ], 201);
});

Router::get("/api/images/{filename}", function ($request, $response) {
    $filename = $request->params["filename"];

    // lowercase comment: prevent directory traversal
    if (strpos($filename, "..") !== false || strpos($filename, "/") !== false) {
        return $response->json(["error" => "Invalid filename"], 400);
    }

    $filepath = __DIR__ . "/../public/uploads/" . $filename;

    if (!file_exists($filepath)) {
        return $response->json(["error" => "Image not found"], 404);
    }

    return $response->file($filepath);
});

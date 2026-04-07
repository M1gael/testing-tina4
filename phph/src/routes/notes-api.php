<?php
use Tina4\Router;
use Tina4\Database\Database;
use Tina4\Validator;

// testing full crud api for notes from chapter 5 exercise
Router::get("/api/notes", function ($request, $response) {
    $db = Database::getConnection();
    if (!$db) {
        error_log("DATABASE CONNECTION FAILED (null)");
        return $response->json(["error" => "No database connection"], 500);
    }
    $tag = $request->params["tag"] ?? null;
    $search = $request->params["search"] ?? null;

    $sql = "SELECT * FROM notes WHERE 1=1";
    $params = [];

    if ($tag) {
        $sql .= " AND tag = :tag";
        $params["tag"] = $tag;
    }

    if ($search) {
        $sql .= " AND (title LIKE :search OR content LIKE :search)";
        $params["search"] = "%" . $search . "%";
    }

    $sql .= " ORDER BY created_at DESC";

    $result = $db->fetch($sql, $params);

    return $response->json([
        "notes" => $result->toArray(),
        "count" => count($result),
        "metadata" => $result->toPaginate()
    ]);
});

Router::get("/api/notes/{id:int}", function ($request, $response) {
    $db = Database::getConnection();
    $id = $request->params["id"];
    $note = $db->fetchOne("SELECT * FROM notes WHERE id = :id", ["id" => $id]);

    if (!$note) {
        return $response->json(["error" => "Note not found"], 404);
    }

    return $response->json($note);
});

/**
 * @noauth
 */
Router::post("/api/notes", function ($request, $response) {
    error_log("POST /api/notes called");
    $db = Database::getConnection();
    $v = new Validator($request->body);
    $v->required("title")->required("content");

    if (!$v->isValid()) {
        return $response->sendError("VALIDATION_FAILED", $v->errors()[0]["message"], 400);
    }

    $db->insert("notes", [
        "title" => $request->body["title"],
        "content" => $request->body["content"],
        "tag" => $request->body["tag"] ?? "general"
    ]);

    // lowercase comment: get last inserted ID (sqlite specific)
    $lastIdResult = $db->fetchOne("SELECT last_insert_rowid() AS id");
    $id = $lastIdResult["id"];

    $newNote = $db->fetchOne("SELECT * FROM notes WHERE id = :id", ["id" => $id]);

    return $response->json($newNote, 201);
});

/**
 * @noauth
 */
Router::put("/api/notes/{id:int}", function ($request, $response) {
    $db = Database::getConnection();
    $id = $request->params["id"];

    $note = $db->fetchOne("SELECT * FROM notes WHERE id = :id", ["id" => $id]);
    if (!$note) {
        return $response->json(["error" => "Note not found"], 404);
    }

    $data = array_merge($note, $request->body);
    $data["updated_at"] = date("Y-m-d H:i:s"); // lowercase comment: update timestamp

    $db->update("notes", [
        "title" => $data["title"],
        "content" => $data["content"],
        "tag" => $data["tag"],
        "updated_at" => $data["updated_at"]
    ], "id = :id", ["id" => $id]);

    return $response->json($data);
});

/**
 * @noauth
 */
Router::delete("/api/notes/{id:int}", function ($request, $response) {
    $db = Database::getConnection();
    $id = $request->params["id"];

    $note = $db->fetchOne("SELECT * FROM notes WHERE id = :id", ["id" => $id]);
    if (!$note) {
        return $response->json(["error" => "Note not found"], 404);
    }

    $db->delete("notes", "id = :id", ["id" => $id]);

    return $response->json(null, 204);
});

// testing schema inspection from chapter 5
Router::get("/api/db/schema", function ($request, $response) {
    $db = Database::getConnection();
    $tables = $db->getTables();
    $schema = [];
    foreach ($tables as $table) {
        $schema[$table] = $db->getColumns($table);
    }
    return $response->json([
        "engine" => "sqlite", // lowercase comment: getDatabaseType() doesn't exist in php class
        "tables" => $schema
    ]);
});

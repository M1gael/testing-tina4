<?php
// One php app for claims 4 (ch05 §3), 5 (ch33 CSRF field names) and 6 (no-auth POST, CSRF on).
require_once getenv('PHPT') . '/vendor/autoload.php';
use Tina4\Router; use Tina4\Auth; use Tina4\Database;
Router::get("/ping", fn($rq, $rs) => $rs(["pong" => true]));
// a logged-in browser: identity token in the session, so the auth gate passes and only CSRF decides
Router::get("/login", function ($rq, $rs) { $rq->session->set("token", Auth::getToken(["user_id" => 1])); return $rs(["logged_in" => true]); });
Router::get("/ft", fn($rq, $rs) => $rs->render("ft.twig", []));   // the framework's own form token
Router::post("/api/save", fn($rq, $rs) => $rs(["saved" => true])); // default write route
Router::post("/api/open", fn($rq, $rs) => $rs(["saved" => true]))->noAuth();
// ch05 §3 "Getting the Database Object", verbatim body
Router::get("/api/test-db", function ($request, $response) {
    $db = Database::getConnection();

    $result = $db->fetch("SELECT 1 + 1 AS answer");

    return $response->json($result);
});
// same body, class named by its real namespace (Tina4\Database\Database)
Router::get("/api/test-db-fq", function ($request, $response) {
    $db = \Tina4\Database\Database::getConnection();
    $result = $db->fetch("SELECT 1 + 1 AS answer");
    return $response->json($result);
});
// control: fetchOne gives the single-object shape the doc prints
Router::get("/api/test-db-one", fn($rq, $rs) => $rs->json(\Tina4\Database\Database::getConnection()->fetchOne("SELECT 1 + 1 AS answer")));
$app = new \Tina4\App(basePath: __DIR__);
$app->handle();

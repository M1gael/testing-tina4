<?php
require_once "./vendor/autoload.php";
use Tina4\Router; use Tina4\Auth;
Router::get("/ping", fn($rq, $rs) => $rs(["pong" => true]));
// a logged-in browser: identity token held in the session, no Bearer
Router::get("/login", function ($rq, $rs) { $rq->session->set("token", Auth::getToken(["user_id" => 1])); return $rs(["logged_in" => true]); });
Router::get("/profile", fn($rq, $rs) => $rs->render("profile.twig", []));
Router::post("/api/profile", fn($rq, $rs) => $rs(["saved" => true])); // default write route: auth required
Router::post("/api/open", fn($rq, $rs) => $rs(["saved" => true]))->noAuth(); // ch10 exercise shape
$app = new \Tina4\App(basePath: __DIR__);
$app->handle();

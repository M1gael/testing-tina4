<?php
use Tina4\Router;

// The two routes from tina4-php issue 253, verbatim.
Router::post("/regen", function ($request, $response) {
    session_regenerate_id(true);   // e.g. login fixation defence
    $_SESSION["hit"] = ($_SESSION["hit"] ?? 0) + 1;
    return $response(["id" => session_id(), "hit" => $_SESSION["hit"]]);
})->noAuth();

Router::get("/whoami", function ($request, $response) {
    return $response(["id" => session_id(), "hit" => $_SESSION["hit"] ?? null]);
});

// Controls. /set writes the session without regenerating: if the session
// survives /set but not /regen, the regenerate is the cause. /regen-keep
// regenerates without deleting the old session file.
Router::post("/set", function ($request, $response) {
    $_SESSION["hit"] = ($_SESSION["hit"] ?? 0) + 1;
    return $response(["id" => session_id(), "hit" => $_SESSION["hit"]]);
})->noAuth();

Router::post("/regen-keep", function ($request, $response) {
    session_regenerate_id(false);
    $_SESSION["hit"] = ($_SESSION["hit"] ?? 0) + 1;
    return $response(["id" => session_id(), "hit" => $_SESSION["hit"]]);
})->noAuth();

// What the process thinks of its own state, for the mechanism.
Router::get("/probe", function ($request, $response) {
    $sent = headers_sent($file, $line);
    return $response([
        "sapi" => PHP_SAPI,
        "ob" => ini_get("output_buffering"),
        "status" => session_status(),
        "headers_sent" => $sent ? basename((string)$file) . ":" . $line : false,
        "id" => session_id(),
        "name" => session_name(),
        "pid" => getmypid(),
    ]);
});

// Tina4's own session ($request->session, the tina4_session cookie), for
// comparison: does the framework's session API survive where $_SESSION does not?
Router::post("/t-set", function ($request, $response) {
    $request->session->set("hit", ($request->session->get("hit") ?? 0) + 1);
    return $response(["id" => $request->session->getSessionId(), "hit" => $request->session->get("hit")]);
})->noAuth();

Router::post("/t-regen", function ($request, $response) {
    $request->session->regenerate();
    $request->session->set("hit", ($request->session->get("hit") ?? 0) + 1);
    return $response(["id" => $request->session->getSessionId(), "hit" => $request->session->get("hit")]);
})->noAuth();

Router::get("/t-who", function ($request, $response) {
    return $response(["id" => $request->session->getSessionId(), "hit" => $request->session->get("hit")]);
});

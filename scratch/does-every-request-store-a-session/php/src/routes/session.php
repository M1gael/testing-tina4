<?php
use Tina4\Router;
Router::get('/where', fn ($request, $response) => $response((new ReflectionClass(\Tina4\Session::class))->getFileName()));
Router::get('/plain', fn ($request, $response) => $response('plain'));                                   // never touches the session
Router::get('/read', fn ($request, $response) => $response('user=' . ($request->session->get('user') ?? '-')));
Router::get('/write', function ($request, $response) {
    $request->session->set('user', 'alice');
    return $response('wrote');
});
Router::get('/login', function ($request, $response) {                                                    // regenerate, then set
    $request->session->regenerate();
    $request->session->set('user', 'alice');
    return $response('logged in');
});
Router::get('/flash-set', function ($request, $response) {
    $request->session->flash('notice', 'saved');
    return $response('flashed');
});
Router::get('/flash-get', fn ($request, $response) => $response('flash=' . ($request->session->getFlash('notice') ?? '-')));
Router::get('/native-read', fn ($request, $response) => $response('native=' . ($_SESSION['n'] ?? '-')));
Router::get('/native-write', function ($request, $response) {
    $_SESSION['n'] = 'set';
    return $response('native wrote');
});
Router::get('/native-login', function ($request, $response) {
    session_regenerate_id(true);
    $_SESSION['n'] = 'set';
    return $response('native logged in');
});
// An anonymous form: the token is rendered on a GET that writes no session, posted back to a
// route that takes it (TINA4_CSRF=true). php binds a form token to the native session id
// when one is active (Frond formToken: session_id()).
Router::get('/form', fn ($request, $response) => $response((new \Tina4\Frond())->renderString('{{ form_token_value() }}')));
Router::post('/submit', fn ($request, $response) => $response('submitted'));

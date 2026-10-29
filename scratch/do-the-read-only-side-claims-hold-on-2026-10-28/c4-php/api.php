<?php
// claim 4: ch21 php doc call shapes vs the real Tina4\Api. Each line: <check> <doc-shape result> | <control result>
require getenv('PHPT') . '/vendor/autoload.php';
use Tina4\Api;
$base = 'http://127.0.0.1:' . getenv('EPORT');
$allow = ['127.0.0.1'];  // SSRF guard: loopback must be allow-listed
function tryit(callable $f): string { try { return json_encode($f()); } catch (\Throwable $e) { return get_class($e) . ': ' . strtok($e->getMessage(), "\n"); } }
$api = new Api($base, allowHosts: $allow);
// (a) payload as FOURTH arg (doc: sendRequest('POST','/posts',[],[...]))
echo "a_doc_payload4th ", tryit(fn() => $api->sendRequest('POST', '/posts', [], ['title' => 'T'])), "\n";
echo "a_ctl_payload3rd ", tryit(fn() => $api->sendRequest('POST', '/posts', ['title' => 'T'])['body']), "\n";
echo "a_ctl_4th_is_ctype ", tryit(fn() => $api->sendRequest('POST', '/posts', 'x=1', 'application/x-www-form-urlencoded')['body']['ctype']), "\n";
// (b) query params as THIRD arg on GET (doc: sendRequest('GET','/posts',['userId'=>1,...]))
echo "b_doc_query3rd ", tryit(fn() => array_intersect_key($api->sendRequest('GET', '/posts', ['userId' => 1, '_limit' => 5])['body'], ['query'=>1,'body'=>1])), "\n";
echo "b_ctl_get_params ", tryit(fn() => $api->get('/posts', ['userId' => 1, '_limit' => 5])['body']['query']), "\n";
// (c) addCustomHeaders vs addHeaders
echo "c_doc_addCustomHeaders ", tryit(function () use ($base, $allow) { $a = new Api($base, allowHosts: $allow); $a->addCustomHeaders(['X-Probe' => 'v']); return $a->get('/h')['body']['xh']; }), "\n";
echo "c_ctl_addHeaders ", tryit(function () use ($base, $allow) { $a = new Api($base, allowHosts: $allow); $a->addHeaders(['X-Probe' => 'v']); return $a->get('/h')['body']['xh']; }), "\n";
// (d) setUsernamePassword vs setBasicAuth
echo "d_doc_setUsernamePassword ", tryit(function () use ($base, $allow) { $a = new Api($base, allowHosts: $allow); $a->setUsernamePassword('k', 's'); return $a->get('/a')['body']['auth']; }), "\n";
echo "d_ctl_setBasicAuth ", tryit(function () use ($base, $allow) { $a = new Api($base, allowHosts: $allow); $a->setBasicAuth('k', 's'); return $a->get('/a')['body']['auth']; }), "\n";
// (e) per-call timeout. Doc: sendRequest('GET','/path',[],[],['timeout'=>5]). Then the same 5th-arg options with a
// valid 4th arg, against a 3s endpoint with timeout 1: honoured => error/no code, ignored => 200 after ~3s.
echo "e_doc_percall_timeout ", tryit(fn() => $api->sendRequest('GET', '/path', [], [], ['timeout' => 5])['http_code']), "\n";
$t = microtime(true); $c = tryit(fn() => $api->sendRequest('GET', '/slow', null, 'application/json', ['timeout' => 1])['http_code']);
printf("e_percall_opts_on_slow %s after %.1fs\n", $c, microtime(true) - $t);
$r = new ReflectionMethod(Api::class, 'sendRequest');
echo "e_sendRequest_params ", implode(',', array_map(fn($p) => $p->getName(), $r->getParameters())), "\n";
$t = microtime(true); $c = tryit(fn() => (new Api($base, timeout: 1, allowHosts: $allow))->get('/slow')['http_code']);
printf("e_ctl_ctor_timeout_on_slow %s after %.1fs\n", $c, microtime(true) - $t);

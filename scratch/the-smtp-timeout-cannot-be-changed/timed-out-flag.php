<?php
// Does fgets() === false tell a read timeout from a closed connection? It does not;
// the stream's metadata does. Two real sockets: one peer never speaks, one hangs up.
$silent = stream_socket_server('tcp://127.0.0.1:0');           // never accept()ed
$closer = stream_socket_server('tcp://127.0.0.1:0');
foreach (['silent peer' => $silent, 'peer hangs up' => $closer] as $label => $server) {
    $port = (int) substr(strrchr(stream_socket_get_name($server, false), ':'), 1);
    $c = stream_socket_client("tcp://127.0.0.1:$port", $en, $es, 2);
    if ($server === $closer) { fclose(stream_socket_accept($server, 2)); }
    stream_set_timeout($c, 1);
    $t = microtime(true); $line = fgets($c, 4096); $meta = stream_get_meta_data($c);
    printf("%-14s fgets=%s after %.1fs  timed_out=%s eof=%s\n", $label, var_export($line, true),
        microtime(true) - $t, var_export($meta['timed_out'], true), var_export($meta['eof'], true));
}

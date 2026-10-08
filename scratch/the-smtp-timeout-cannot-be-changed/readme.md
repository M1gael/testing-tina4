# The SMTP timeout cannot be changed

tina4-php's `Messenger` holds every SMTP connect and read for a hard-coded 30 s. No
parameter, environment variable or setter reaches it, and the property is `private`.
A relay that accepts the connection and then says nothing holds `send()`, and the
request behind it, for the full 30 s. It then reports "Lost connection to SMTP server",
not a timeout.

Upstream: tina4-php#278. Ledger: `f-misc-06`.

## Mechanism (tina4-php 3.13.148, `4891b8d0`)

- `Tina4/Messenger.php:91`: `private int $timeout = 30`, read by the connect and by
  `stream_set_timeout()`.
- `Messenger.php:1176`: `fgets()` returns false both for a timeout and for a closed
  connection, and both were reported as "Lost connection".
  `stream_get_meta_data()['timed_out']` tells them apart (`timed-out-flag.php`).

## Run

```sh
TREE=<tina4-php tree> ./prove.sh
```

`blackhole-smtp.py` accepts and never answers. `timeout.php` runs on stock and
`with-the-fix.php` on a fixed tree.

## Before and after (`out-3.13.148.txt`, PHP 8.4.26, Linux)

```
stock: a timeout parameter: NO; a public setter: NONE
       elapsed: 30.0s  (SMTP error: Lost connection to SMTP server)
fix:   constructor timeout 2 -> 2.0s;  TINA4_MAIL_TIMEOUT=3 -> 3.0s;  constructor beats env
       TINA4_MAIL_TIMEOUT=banana or 0 -> warns once, uses 30s;  constructor 0 -> InvalidArgumentException
```

The fix resolves the timeout as constructor argument, then `TINA4_MAIL_TIMEOUT`, then
30. It bounds the connect, an implicit-TLS or STARTTLS handshake, and every read and
write. A timeout now reads "Timed out after Ns waiting for the SMTP server to reply".
Zero is refused: to PHP's socket calls 0 means "do not wait at all", not "no limit".

## Other ports (3.13.148)

py, rb and nd are affected (`python/`, `ruby/`, `nodejs/`; see the ledger row).

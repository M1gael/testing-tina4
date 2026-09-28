# Is the flyer hello-route snippet right?

Yes. On 2026-09-28, `tina4 init python my-app` (CLI 3.8.77, tina4-python 3.13.139), then `src/routes/hello.py` copied verbatim from `flyer.png`, then `tina4 serve`.

- `curl localhost:7146/api/hello/Ada` returned 200 `application/json` `{"hello":"Ada"}`.
- `/swagger/openapi.json` lists `/api/hello/{name}`.

The only difference is cosmetic: the real body has no space after the colon.

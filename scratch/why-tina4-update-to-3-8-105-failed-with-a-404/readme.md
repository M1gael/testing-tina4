# Why `tina4 update` from 3.8.104 failed with a 404 on 2026-10-26

Report (macOS arm64, `sudo tina4 update`): Current 3.8.104, Latest 3.8.105, `curl: (56) The requested
URL returned error: 404`, then "The release asset is fine -- trying another asset name would not have
helped."

Tree: tina4 `origin/main` 0b92b43 (3.8.106), fetched 2026-10-26.

## Answer

Two separate faults.

1. **The 404 (upstream, not ours; fixed in 3.8.106).** 3.8.104 (#115) reads "latest" from
   `releases.atom`, which lists every pushed tag. v3.8.105 was tagged but not yet published as a
   release, so 3.8.104 offered it and asked for assets that did not exist. Read: commit 0b92b43
   message; run: `gh release view v3.8.105` says "release not found", the tag no longer exists, and
   v3.8.106 is published with `tina4-darwin-arm64` answering 200. #118 resolves latest from the
   `releases/latest` redirect, which skips drafts. A 3.8.104 install updates fine now, because the
   feed's newest entry, v3.8.106, is published (inferred: this breaks again during any later
   tag-before-publish window, for anyone still on 3.8.104).
2. **The wrong diagnosis (ours, from #21 / f-cli-05).** `classify_curl_status`
   (`src/main.rs:2164`) treats only exit 22 as an HTTP refusal; every other code is "Local" and
   prints "The release asset is fine" (`src/main.rs:2238-2243`). The report shows curl exiting
   **56** on a 404 under `-f`. Curl 8.15.0 here exits 22 for the same URL over HTTP/2 and 1.1
   (run). A 56-for-404 under `-fsS` is reported against curl 8.7.1 (ALT bug 49883), which is
   the version macOS ships as /usr/bin/curl (inferred: not reproduced here; the build of 8.7.1 was
   not run). The message's own text, "returned error: 404", says the server refused.

## Not visited

- A real Mac, or curl 8.7.1 itself.
- Whether 56 accompanies every HTTP error on that curl, or only some.

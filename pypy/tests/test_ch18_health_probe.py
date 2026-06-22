# Probe — covers PY-18-14. Encodes the 3.13.39 error-aware /health contract: the body
# carries an `errors` count and a `status` of "ok"/"error", and the HTTP code is 503
# exactly when status=="error" (≥1 unresolved error recorded). On 3.13.30 /health had
# no `errors` field and was always 200 — this probe flips red if the framework reverts
# to a static health check, or if the ok/error <-> 200/503 mapping changes. The error
# store is file-backed at data/.broken/<ts>_<type>.broken and persists across serve
# restarts (so a single stale dev error keeps /health red until the store is cleared).
import json

from tina4_python.test import Test, assert_equal, assert_true


class HealthContractTest(Test):
    def test_health_error_aware_contract(self):
        resp = self.get("/health")
        body = json.loads(resp.body)

        # fields introduced in 3.13.39 (absent on 3.13.30's static health payload)
        assert_true("errors" in body, "health body should report an `errors` count")
        assert_true("version" in body, "health body should report the framework version")
        assert_true(body["status"] in ("ok", "error"), "status must be 'ok' or 'error'")

        # contract: status is "ok" iff zero unresolved errors; HTTP 503 iff "error"
        if body["errors"] == 0:
            assert_equal(body["status"], "ok", "zero errors -> status ok")
            assert_equal(resp.status, 200, "ok -> HTTP 200")
        else:
            assert_equal(body["status"], "error", "recorded errors -> status error")
            assert_equal(resp.status, 503, "error -> HTTP 503")

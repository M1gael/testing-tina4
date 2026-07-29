# Probe — covers PY-18-10. Response Object reference regression sentinel.
# ch18 section 5 — Response Object probe
# Originally demonstrated PY-18-10 against tina4-python 3.13.2.
# Fixed in 3.13.4 via DOCS UPDATE (the framework was unchanged — the chapter
# was brought into line with what TestResponse always exposed). The new S5
# "Response Object" subsection now correctly lists `resp.status`, `resp.body`
# (bytes), `resp.text()`, `resp.json()`, and lowercased headers.
#
# Probe retained as regression sentinel for BOTH directions:
#   - If the docs re-introduce `resp.status_code` or "body is a string", the
#     test_doc_* assertions stay failing — but now those failures are out of
#     line with corrected docs, so the failures themselves become the alarm.
#   - If the framework ever adds a `status_code` attribute or returns a string
#     body, the test_doc_* assertions would PASS — also an alarm (silent API
#     drift).
#
# Each test is ONE observation. The PASS/FAIL pattern itself is the proof:
#   - test_doc_*  → exercises the (formerly bad) chapter claim verbatim. FAIL
#                   means the framework still doesn't have that attribute /
#                   shape, which matches the corrected docs.
#   - test_real_* → exercises the framework's actual API. PASS means the
#                   real attribute exists.

import pytest
# Probe dormant. Remove this skip line to re-enable.
pytest.skip("probe dormant — see readme convention", allow_module_level=True)

from tina4_python.test import Test, assert_equal, assert_true


class ResponseObjectProbe(Test):

    # ── 1. status_code (doc) vs status (real) ─────────────────────

    # Probe path — any unregistered URL returns a TestResponse with status 404.
    # That's all this probe needs; no DB, no route stubs.
    PROBE_PATH = "/__ch18_probe_unregistered_path__"

    def test_resp_has_status_not_status_code(self):
        """PY-18-10 (docs fixed in 3.13.4): TestResponse exposes `.status`
        (int) — not `.status_code`. Probe asserts correct contract.
        Regression = `status_code` reappears = doc/framework drift."""
        resp = self.get(self.PROBE_PATH)
        assert_true(hasattr(resp, "status"), "TestResponse must expose .status")
        assert_true(not hasattr(resp, "status_code"),
                    "PY-18-10 regression: .status_code must not exist on TestResponse")

    def test_real_resp_status_attribute_works(self):
        """The actual attribute is `resp.status`."""
        resp = self.get(self.PROBE_PATH)
        assert_equal(resp.status, 404, "real attribute is .status (int) — 404 because the path isn't registered")

    # ── 2. body type: docs claim string, reality is bytes ─────────

    def test_resp_body_is_bytes(self):
        """PY-18-10 (docs fixed in 3.13.4): TestResponse.body is raw bytes,
        and the refreshed S5 "Response Object" subsection documents it as such.
        Probe asserts correct contract.
        Regression = body becomes str = framework or doc drift."""
        resp = self.get(self.PROBE_PATH)
        assert_true(isinstance(resp.body, bytes),
                    "PY-18-10 regression: resp.body must remain bytes")

    def test_real_resp_body_is_bytes(self):
        """Reality: resp.body is bytes. json.loads() happens to accept bytes,
        which is why the chapter's `json.loads(resp.body)` calls don't blow up —
        but the docs are still wrong about the type."""
        resp = self.get(self.PROBE_PATH)
        assert_true(isinstance(resp.body, bytes), "reality: resp.body is bytes")

    # ── 3. helper methods the docs never mention ─────────────────

    def test_undocumented_text_helper_exists(self):
        """The class has resp.text() — undocumented."""
        resp = self.get(self.PROBE_PATH)
        text = resp.text()
        assert_true(isinstance(text, str), "resp.text() decodes bytes → str — undocumented")

    def test_undocumented_json_helper_exists(self):
        """The class has resp.json() — undocumented. (Not called on a 404 body
        because the 404 body may be empty/non-JSON; just check the method exists.)"""
        resp = self.get(self.PROBE_PATH)
        assert_true(callable(getattr(resp, "json", None)), "resp.json() method exists — undocumented")

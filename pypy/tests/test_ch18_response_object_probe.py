# ch18 section 5 — Response Object probe
# Empirically demonstrates PY-18-10: the documented Response Object reference
# (chapter 18, "Response Object" subsection, lines 384-393) does not match
# what `tina4_python.test_client.TestResponse` actually exposes.
#
# Each test is ONE observation. The PASS/FAIL pattern itself is the proof:
#   - test_doc_*  → exercises the chapter's claim verbatim. FAIL means the
#                   chapter is wrong on that point.
#   - test_real_* → exercises the framework's actual API. PASS means the
#                   real attribute exists.

from tina4_python.test import Test, assert_equal, assert_true


class ResponseObjectProbe(Test):

    # ── 1. status_code (doc) vs status (real) ─────────────────────

    # Probe path — any unregistered URL returns a TestResponse with status 404.
    # That's all this probe needs; no DB, no route stubs.
    PROBE_PATH = "/__ch18_probe_unregistered_path__"

    def test_doc_resp_status_code_attribute_exists(self):
        """Chapter shows `resp.status_code`. Reality: AttributeError."""
        resp = self.get(self.PROBE_PATH)
        _ = resp.status_code   # this raises AttributeError on every assertion in the chapter

    def test_real_resp_status_attribute_works(self):
        """The actual attribute is `resp.status`."""
        resp = self.get(self.PROBE_PATH)
        assert_equal(resp.status, 404, "real attribute is .status (int) — 404 because the path isn't registered")

    # ── 2. body type: docs claim string, reality is bytes ─────────

    def test_doc_resp_body_is_a_string(self):
        """Chapter line 390: 'Response body as a string'."""
        resp = self.get(self.PROBE_PATH)
        assert_true(isinstance(resp.body, str), "docs claim resp.body is a string")

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

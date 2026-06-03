# ch18 section 5 — "Test Client Methods" cheat sheet
# VERBATIM examples from the chapter's reference subsection. The snippet in the
# chapter is a list of comment-separated examples (not runnable code) — here
# each example is wrapped in its own `test_*` method so `tina4 test` can run
# them, but the body of each method is verbatim from the chapter.
#
# Expected outcome (per PY-18-08):
#   - get/delete signatures work → those tests pass (no assertions, so a clean
#     return counts as pass)
#   - post/put/patch positional-body calls fail with TypeError → the body must
#     be a keyword arg (json=...) but the chapter shows positional usage.
#
# This file is intentionally UNPATCHED — it's the latest file under evaluation,
# per the readme's "Patching Convention" rule that the newest file stays
# verbatim so a fresh `tina4 test` run only shows interesting failures here.

from tina4_python.test import Test

class ClientMethodsTest(Test):

    def test_get_request(self):
        # GET request
        resp = self.get("/api/products")

    def test_get_with_query_parameters(self):
        # GET with query parameters
        resp = self.get("/api/products?category=Electronics&page=2")

    def test_post_with_json_body(self):
        # POST with JSON body
        resp = self.post("/api/products", {"name": "Widget", "price": 9.99})

    def test_put_with_json_body(self):
        # PUT with JSON body
        resp = self.put("/api/products/1", {"name": "Updated Widget"})

    def test_patch_with_json_body(self):
        # PATCH with JSON body
        resp = self.patch("/api/products/1", {"price": 12.99})

    def test_delete(self):
        # DELETE
        resp = self.delete("/api/products/1")

    def test_get_with_custom_headers(self):
        # Request with custom headers
        resp = self.get("/api/profile", headers={
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiIs..."
        })

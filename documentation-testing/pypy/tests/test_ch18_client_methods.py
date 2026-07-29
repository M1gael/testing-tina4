# ch18 section 5 — "Test Client Methods" cheat sheet
# VERBATIM examples from the chapter's reference subsection. The chapter shows
# each method as a comment-prefixed example (not runnable code) — here each
# example is wrapped in its own `test_*` method so `tina4 test` can run them,
# but the body of each method is verbatim from the chapter.
#
# PY-18-08a was fixed in 3.13.4 — the chapter now uses keyword `json=` form
# for post/put/patch bodies. No code patches required.

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
        resp = self.post("/api/products", json={"name": "Widget", "price": 9.99})

    def test_put_with_json_body(self):
        # PUT with JSON body
        resp = self.put("/api/products/1", json={"name": "Updated Widget"})

    def test_patch_with_json_body(self):
        # PATCH with JSON body
        resp = self.patch("/api/products/1", json={"price": 12.99})

    def test_delete(self):
        # DELETE
        resp = self.delete("/api/products/1")

    def test_get_with_custom_headers(self):
        # Request with custom headers
        resp = self.get("/api/profile", headers={
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiIs..."
        })

# ch18 section 7 — Setup and Teardown
# Two patches applied so the snippet can run. Remove both to reproduce the
# original PY-18-12 NameError + PY-18-07b "No database bound" cascade.
#
# ============================== PATCHES ==============================
#
# PATCH [PY-18-12]: chapter never imports `User`. Same defect class as PY-18-07a
# (S4 Product) before the 3.13.4 fix; the parallel S7 fix is missing.
from src.orm.User import User
#
# PATCH [PY-18-07b]: chapter claims `tina4 test` auto-binds a separate test DB
# at `data/test.db` and resets it between runs. False — env var must be set
# and the table created explicitly.
import os
os.environ.setdefault("TINA4_DATABASE_URL", "sqlite:///data/test.db")
os.makedirs("data", exist_ok=True)
User.create_table()
#
# ============================ END PATCHES ============================

# Verbatim chapter code starts here:
from tina4_python.test import Test, assert_equal, assert_not_none
import time

class UserTest(Test):

    def set_up(self):
        # Runs before each test
        user = User()
        user.name = "Test User"
        user.email = f"test-{int(time.time())}@example.com"
        user.save()
        self.user_id = user.id

    def tear_down(self):
        # Runs after each test
        if self.user_id:
            user = User.find(self.user_id)
            if user:
                user.delete()

    def test_user_exists(self):
        user = User.find(self.user_id)
        assert_not_none(user.id, "User should exist")
        assert_equal(user.name, "Test User", "Name should match")

    def test_update_user(self):
        user = User.find(self.user_id)
        user.name = "Updated Name"
        user.save()

        reloaded = User.find(self.user_id)
        assert_equal(reloaded.name, "Updated Name", "Name should be updated")

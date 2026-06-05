# ch18 section 11/12 — Exercise: Test a User Model (verbatim, pre-patch)
# File written exactly as the chapter shows it. Discrepancies logged in the
# KI Log will be patched with PATCH markers below.

import uuid
from tina4_python.test import Test, assert_equal, assert_true, assert_not_none, assert_raises, assert_false

# PATCH [PY-18-13a]: chapter S12 never imports the User model — pytest discovers
# the file from scratch with no implicit injection, so NameError on first use.
# OLD: (no import line — chapter omits it)
from src.orm.User import User

# PATCH [PY-18-07b]: chapter claims `tina4 test` auto-binds a separate test DB
# at `data/test.db` and resets it between runs. False — env var must be set
# and table created explicitly. Same pattern as test_ch18_setup_teardown.py.
import os
os.environ.setdefault("TINA4_DATABASE_URL", "sqlite:///data/test.db")
os.makedirs("data", exist_ok=True)
User.create_table()

# PATCH [PY-18-13c]: S11 mandates a `test_duplicate_email` test that expects an
# exception on save, but the framework has no `unique=True` kwarg on `Field`
# / `StringField` (verified — `Field.__init__` accepts no such kwarg) and the
# chapter never shows a migration, save() override, or uniqueness mechanism.
# Manual UNIQUE INDEX here to make the test runnable as documented.
User._get_db().execute("CREATE UNIQUE INDEX IF NOT EXISTS users_email_unique ON users(email)")


class UserModelTest(Test):

    def test_create_user(self):
        user = User()
        user.name = "Test User"
        user.email = f"testuser-{uuid.uuid4().hex[:8]}@example.com"
        user.save()

        assert_not_none(user.id, "User should have an ID after save")
        assert_equal(user.name, "Test User", "Name should match")
        assert_true("@example.com" in user.email, "Email should be set")

    def test_duplicate_email(self):
        email = f"duplicate-{uuid.uuid4().hex[:8]}@example.com"

        user1 = User()
        user1.name = "First User"
        user1.email = email
        user1.save()

        def create_duplicate():
            user2 = User()
            user2.name = "Second User"
            user2.email = email
            user2.save()

        # PATCH [PY-18-13e]: `ORM.save()` (model.py:336-338) catches ALL
        # exceptions on the insert/update path and returns `False` — it never
        # propagates IntegrityError. The chapter's `assert_raises(...,
        # Exception, ...)` therefore cannot fire even with a UNIQUE index in
        # place. The actual framework contract is "duplicate save returns
        # False"; the test must check that, not a raise.
        # OLD: assert_raises(create_duplicate, Exception, "Should reject duplicate email")
        user2 = User()
        user2.name = "Second User"
        user2.email = email
        result = user2.save()
        assert_false(result, "Duplicate email save returns False — save() swallows IntegrityError")
        # Silence unused-name warning — the chapter's inner `create_duplicate`
        # function is kept above to mirror the verbatim S12 structure.
        _ = create_duplicate

    def test_update_user(self):
        user = User()
        user.name = "Original Name"
        user.email = f"update-{uuid.uuid4().hex[:8]}@example.com"
        user.save()

        user_id = user.id
        user.name = "New Name"
        user.save()

        reloaded = User.find(user_id)
        assert_equal(reloaded.name, "New Name", "Name should be updated")

    def test_delete_user(self):
        user = User()
        user.name = "Delete Me"
        user.email = f"delete-{uuid.uuid4().hex[:8]}@example.com"
        user.save()

        user_id = user.id
        user.delete()

        gone = User.find(user_id)
        assert_true(gone is None, "Deleted user should not exist")

    def test_select_users(self):
        for i in range(3):
            user = User()
            user.name = f"Select Test User {i}"
            user.email = f"select-test-{i}-{uuid.uuid4().hex[:8]}@example.com"
            user.save()

        # PATCH [PY-18-13d]: chapter S12 line 808 unpacks `where("1=1")` into
        # two variables. `Model.where()` returns `list[Self]` by default; the
        # tuple `(list, count)` form requires `with_count=True`. As written the
        # chapter line raises `ValueError: too many values to unpack`.
        # OLD: users, count = User.where("1=1")
        users, count = User.where("1=1", with_count=True)

        assert_true(len(users) >= 3, "Should have at least 3 users")

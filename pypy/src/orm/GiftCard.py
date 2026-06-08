# Mirror of upstream issue #46 reporter's GiftCard model.
#
# Schema is created by hand in the live-repro test (BOOLEAN is_deleted)
# to match the reporter's PostgreSQL setup as closely as possible
# without their actual migration in hand.
#
# Used ONLY by tests/test_issue_46_live_repro.py; not part of any
# Tina4 chapter exercise.

from tina4_python.orm import ORM, IntegerField, StringField, NumericField


class GiftCard(ORM):
    table_name = "gift_cards"
    # The schema's `is_deleted` is a real BOOLEAN column. Tina4's
    # default `soft_delete=True` auto-appends `is_deleted = 0` to
    # generated WHERE clauses, which triggers the SAME BOOLEAN vs
    # integer error this whole repro is about — masking the issue
    # we actually want to exercise. Turn the auto-filter off so our
    # tests control the filter shape explicitly. (Adjacent finding:
    # framework-generated SQL has the same BOOLEAN/integer hazard.)
    soft_delete = False

    id                = IntegerField(primary_key=True, auto_increment=True)
    created_by_email  = StringField()
    owned_by_email    = StringField()
    amount            = NumericField()
    # Note: framework has no BooleanField (see PY-18-07 in main's KI Log).
    # Treating is_deleted as IntegerField means Python-side it's read as
    # int, but the column on the live DB is actual BOOLEAN — psycopg2
    # casts BOOLEAN → bool on read, int → bool on write. The mismatch
    # only matters in the WHERE filter SQL the reporter wrote
    # (`is_deleted = 0`), which is the whole point of this repro.
    is_deleted        = IntegerField()

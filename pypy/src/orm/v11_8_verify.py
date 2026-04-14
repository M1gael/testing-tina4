from tina4_python.orm import Database, ORM, IntegerField, StringField

class VerificationModel(ORM):
    # test chapter 6 - testing exact documentation arguments
    id = IntegerField(pk=True)  # docs say pk=True
    name = StringField()
    created_at = IntegerField(auto_now_add=True)  # docs say auto_now_add=True

from tina4_python.orm import Database, ORM, IntegerField, StringField

class VerificationModel(ORM):
    # test chapter 6 - testing exact documentation arguments
    id = IntegerField(primary_key=True)  # docs say primary_key=True
    name = StringField()
    created_at = IntegerField()  # docs say 

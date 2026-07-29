# ch18 supporting model — Product (from Chapter 6 ORM patterns)
from tina4_python.orm import ORM, IntegerField, StringField, NumericField, Field

class Product(ORM):
    table_name = "products"

    id       = IntegerField(primary_key=True, auto_increment=True)
    name     = StringField(required=True)
    category = StringField()
    price    = NumericField()
    in_stock = Field(bool, default=True)

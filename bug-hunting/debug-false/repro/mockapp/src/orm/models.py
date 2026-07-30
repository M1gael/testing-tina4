"""19 AutoCRUD models — the route-count multiplier, made visible.

Every model with ``auto_crud = True`` generates FIVE REST routes:

    GET    /api/<table>          list
    GET    /api/<table>/{id}     read
    POST   /api/<table>          create
    PUT    /api/<table>/{id}     update
    DELETE /api/<table>/{id}     delete

19 models x 5 = 95 generated routes. Plus one hand-written route
(src/routes/hello.py) and the 3 routes the framework registers on its own,
the dev footer reads exactly:

    99 routes

...which is the number in the bug report. Nothing here is contrived — this
is one flag per model, the documented one-liner from Chapter 6.

Delete a model and the footer count drops by 5. That is the whole point:
the number is honest, it is just unexplained and undrillable in the footer.

No database is needed to reproduce any of this. Route registration happens
at import time in the ORM metaclass; only executing a query would touch the
DB. The .env points at sqlite so nothing has to be installed either way.
"""

from tina4_python.orm import (
    ORM,
    BooleanField,
    DateTimeField,
    IntegerField,
    StringField,
)


class Customer(ORM):
    table_name = "customers"
    auto_crud = True

    id = IntegerField(primary_key=True, auto_increment=True)
    name = StringField(required=True, max_length=200)
    email = StringField(default="")
    created_at = DateTimeField()


class Order(ORM):
    table_name = "orders"
    auto_crud = True

    id = IntegerField(primary_key=True, auto_increment=True)
    reference = StringField(required=True)
    total = IntegerField(default=0)
    created_at = DateTimeField()


class OrderLine(ORM):
    table_name = "order_lines"
    auto_crud = True

    id = IntegerField(primary_key=True, auto_increment=True)
    order_id = IntegerField(default=0)
    quantity = IntegerField(default=1)


class Product(ORM):
    table_name = "products"
    auto_crud = True

    id = IntegerField(primary_key=True, auto_increment=True)
    name = StringField(required=True, max_length=200)
    price = IntegerField(default=0)
    in_stock = BooleanField(default=True)


class Category(ORM):
    table_name = "categories"
    auto_crud = True

    id = IntegerField(primary_key=True, auto_increment=True)
    name = StringField(required=True)


class Supplier(ORM):
    table_name = "suppliers"
    auto_crud = True

    id = IntegerField(primary_key=True, auto_increment=True)
    name = StringField(required=True)
    contact_email = StringField(default="")


class Invoice(ORM):
    table_name = "invoices"
    auto_crud = True

    id = IntegerField(primary_key=True, auto_increment=True)
    number = StringField(required=True)
    paid = BooleanField(default=False)


class Payment(ORM):
    table_name = "payments"
    auto_crud = True

    id = IntegerField(primary_key=True, auto_increment=True)
    invoice_id = IntegerField(default=0)
    amount = IntegerField(default=0)


class Shipment(ORM):
    table_name = "shipments"
    auto_crud = True

    id = IntegerField(primary_key=True, auto_increment=True)
    order_id = IntegerField(default=0)
    tracking = StringField(default="")


class Warehouse(ORM):
    table_name = "warehouses"
    auto_crud = True

    id = IntegerField(primary_key=True, auto_increment=True)
    name = StringField(required=True)
    region = StringField(default="")


class StockLevel(ORM):
    table_name = "stock_levels"
    auto_crud = True

    id = IntegerField(primary_key=True, auto_increment=True)
    product_id = IntegerField(default=0)
    quantity = IntegerField(default=0)


class Employee(ORM):
    table_name = "employees"
    auto_crud = True

    id = IntegerField(primary_key=True, auto_increment=True)
    name = StringField(required=True)
    role = StringField(default="staff")


class Department(ORM):
    table_name = "departments"
    auto_crud = True

    id = IntegerField(primary_key=True, auto_increment=True)
    name = StringField(required=True)


class Ticket(ORM):
    table_name = "tickets"
    auto_crud = True

    id = IntegerField(primary_key=True, auto_increment=True)
    subject = StringField(required=True)
    closed = BooleanField(default=False)


class Comment(ORM):
    table_name = "comments"
    auto_crud = True

    id = IntegerField(primary_key=True, auto_increment=True)
    ticket_id = IntegerField(default=0)
    body = StringField(default="")


class Attachment(ORM):
    table_name = "attachments"
    auto_crud = True

    id = IntegerField(primary_key=True, auto_increment=True)
    ticket_id = IntegerField(default=0)
    filename = StringField(default="")


class AuditLog(ORM):
    table_name = "audit_logs"
    auto_crud = True

    id = IntegerField(primary_key=True, auto_increment=True)
    action = StringField(default="")
    created_at = DateTimeField()


class Setting(ORM):
    table_name = "settings"
    auto_crud = True

    id = IntegerField(primary_key=True, auto_increment=True)
    key = StringField(required=True)
    value = StringField(default="")


class Webhook(ORM):
    table_name = "webhooks"
    auto_crud = True

    id = IntegerField(primary_key=True, auto_increment=True)
    url = StringField(required=True)
    active = BooleanField(default=True)

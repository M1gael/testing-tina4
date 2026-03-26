from tina4_python.core.router import get

@get("/products")
async def products_page(request, response):
    products = [
        {
            "name": "Wireless Keyboard",
            "description": "Ergonomic wireless keyboard with backlit keys.",
            "price": 79.99,
            "in_stock": True
        },
        {
            "name": "USB-C Hub",
            "description": "7-port USB-C hub with HDMI, SD card reader, and Ethernet.",
            "price": 49.99,
            "in_stock": True
        },
        {
            "name": "Monitor Stand",
            "description": "Adjustable aluminum monitor stand with cable management.",
            "price": 129.99,
            "in_stock": False
        },
        {
            "name": "Mechanical Mouse",
            "description": "High-precision wireless mouse with 16,000 DPI sensor.",
            "price": 59.99,
            "in_stock": True
        }
    ]

    return response.render("products.html", {"products": products})

    
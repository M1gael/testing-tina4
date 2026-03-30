from tina4_python.core.router import get, template

# 1. beyond json -- rendering html
# 2. the @template decorator

@template("about.html")
@get("/about")
async def about_page(request, response):
    # handler returning a dict to be rendered by @template
    return {
        "title": "About Us",
        "company": "My Store",
        "founded": 2020
    }

@get("/about-explicit")
async def about_page_explicit(request, response):
    # testing response.render() directly
    return response.render("about.html", {
        "title": "About Us Explicit",
        "company": "My Store Explicit",
        "founded": 2021
    })

@get("/templates/variables")
async def templates_variables(request, response):
    # Testing Section 3: Variables and Output
    class User:
        def name(self):
            return "Alice"
        
        def t(self, key):
            return f"Translated {key}"
        
        @property
        def address(self):
            return {"city": "Cape Town"}

    data = {
        "name": "Alice",
        "balance": 150.50,
        "user": User(),
        "order": {
            "items": [{"name": "Keyboard"}, {"name": "Mouse"}]
        },
        "text": "This is a long text for slicing",
        "items": ["a", "b", "c", "d", "e", "f"],
        "user_input": "<script>alert('hacked')</script>",
        "trusted_html": "<strong>This is trusted</strong>"
    }
    
    return response.render("variables.html", data)

@get("/templates/filters")
async def templates_filters(request, response):
    # Testing Section 4: Filters and Chaining
    data = {
        "items": ["apple", "banana", "cherry", "date"],
        "scores": [85, 42, 99, 12, 77],
        "data": {"id": 1, "status": "active"},
        "missing": None
    }
    
    return response.render("filters.html", data)

@get("/templates/logic")
async def templates_logic(request, response):
    # Testing Section 5: Control Tags
    data = {
        "user": {
            "role": "moderator",
            "verified": False,
            "first_name": "Alice",
            "last_name": "Smith"
        },
        "price": 150,
        "in_stock": True,
        "items": ["Item A", "Item B", "Item C"],
        "products": [
            {"name": "Laptop", "price": 999.99},
            {"name": "Mouse", "price": 25.50}
        ],
        "empty_list": []
    }
    
    return response.render("control_tags.html", data)

@get("/templates/inheritance")
async def templates_inheritance(request, response):
    # Testing Section 6: Template Inheritance
    return response.render("home.html")






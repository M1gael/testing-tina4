# Tina4 Model Test Prompts (`prompt.md`)

This file contains tiered test prompts for evaluating the **Tina4 Model / Agent** (e.g., Qwen 27B / 36B models). 

> **Important Visual Requirement for Tina4 Agent**: Every generated program MUST include a prominent visual banner at the top of the web interface displaying:
> 1. **Program Name**: The title of the program/test level.
> 2. **Task Objective**: The exact prompt instructions it was given to execute.
> 3. **Success Verification Checklist**: Dynamic/visual indicators demonstrating that required features are present and working.

---

## Test Level 1: Basic Routing & UI (Easy)

### Prompt Text for Tina4 Model:
```text
Build a simple Tina4 Web application in Python using tina4_python.

Visual & UI Requirements:
1. Top Banner: Include a header section at the top of the main page with:
   - Program Name: "Tina4 Level 1 - Basic System Status"
   - Objective: "Demonstrate basic Tina4 @get route and Frond/Twig template rendering."
   - Verification Checklist: Badges showing [✓ Tina4 Route Active] [✓ Frond Template Loaded] [✓ Dynamic Variables Rendered].
2. Content: Display a welcome message, current server time, framework version badge, and a list of 3 sample system metrics rendered dynamically via the Frond template engine.

Technical Requirements:
- Use @get("/") route decorator from tina4_python.
- Store HTML template in `src/templates/index.twig`.
```

---

## Test Level 2: Interactive Microservice & REST API (Medium)

### Prompt Text for Tina4 Model:
```text
Build an interactive microservice and JSON API application using tina4_python.

Visual & UI Requirements:
1. Top Banner: Include a header section at the top of the main page with:
   - Program Name: "Tina4 Level 2 - Interactive Microservice Dashboard"
   - Objective: "Demonstrate REST API endpoints (@get, @post), JSON payload processing, and dynamic AJAX updates."
   - Verification Checklist: Badges showing [✓ REST @get API] [✓ REST @post Handler] [✓ Client-Side Dynamic UI].
2. Content: 
   - Display a dashboard showcasing a Task Manager / Note Logger.
   - An interactive HTML form that posts JSON data to `@post("/api/notes")`.
   - A list of notes fetched dynamically from `@get("/api/notes")`.

Technical Requirements:
- Create `@get("/")` for main page HTML response.
- Create `@get("/api/notes")` returning a JSON list of items.
- Create `@post("/api/notes")` processing incoming JSON requests and appending data.
```

---

## Test Level 3: Database ORM & Full CRUD Application (Hard)

### Prompt Text for Tina4 Model:
```text
Build a complete CRUD application powered by Tina4 Python with database integration (SQLite).

Visual & UI Requirements:
1. Top Banner: Include a header section at the top of the page with:
   - Program Name: "Tina4 Level 3 - Full Inventory Management System"
   - Objective: "Demonstrate Tina4 ORM database handling, full CRUD operations, and templated views."
   - Verification Checklist: Badges showing [✓ Database Migration/Init] [✓ Create Item] [✓ Read/List Items] [✓ Update Item] [✓ Delete Item].
2. Content:
   - Data table displaying inventory items (ID, Name, Category, Stock Quantity, Price).
   - Form to add new inventory items.
   - Action buttons for inline editing stock quantities and deleting items.
   - Live visual indicator of total items and inventory valuation.

Technical Requirements:
- Use Tina4 database routing and ORM models for SQLite.
- Implement full CRUD endpoints (@get, @post, @put/@post for edit, @delete/@post for removal).
- Ensure error handling and success feedback messages are rendered on the UI.
```

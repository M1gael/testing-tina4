from tina4_python.core.router import get, post
from datetime import datetime

# chapter 6: exercise: build a contact form api
# chapter 8: gotchas

submissions = []
next_id = 1


@post("/api/contact")
async def submit_contact(request, response):
    # global next_id to maintain state across requests
    global next_id
    body = request.body
    errors = []

    # validate name (requirement: 2-100 chars)
    name = body.get("name", "")
    if not name:
        errors.append("Name is required")
    elif len(name) < 2 or len(name) > 100:
        errors.append("Name must be between 2 and 100 characters")

    # validate email (requirement: must contain @)
    email = body.get("email", "")
    if not email:
        errors.append("Email is required")
    elif "@" not in email:
        errors.append("Email must contain @")

    # validate subject (requirement: required)
    subject = body.get("subject", "")
    if not subject:
        errors.append("Subject is required")

    # validate message (requirement: 10+ chars)
    message = body.get("message", "")
    if not message:
        errors.append("Message is required")
    elif len(message) < 10:
        errors.append("Message must be at least 10 characters")

    # validate urgency (requirement: low, medium, high, default medium)
    urgency = body.get("urgency", "medium")
    if urgency not in ("low", "medium", "high"):
        errors.append("Urgency must be one of: low, medium, high")

    if errors:
        return response.json({"errors": errors}, 400)

    submission = {
        "id": next_id,
        "name": name,
        "email": email,
        "subject": subject,
        "message": message,
        "urgency": urgency,
        "status": "new",
        "created_at": datetime.now().isoformat()
    }
    next_id += 1
    submissions.append(submission)

    return response.json({
        "message": "Contact form submitted successfully",
        "submission": submission
    }, 201)


@get("/api/contact/submissions")
async def list_submissions(request, response):
    # use request.params for query parameters (gotcha #1)
    status = request.params.get("status")

    if status:
        filtered = [s for s in submissions if s["status"] == status]
        return response.json({"submissions": filtered, "count": len(filtered)})

    return response.json({"submissions": submissions, "count": len(submissions)})

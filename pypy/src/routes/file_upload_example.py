from tina4_python.core.router import post
import os
import uuid

# chapter 5: real-world example: file upload with validation
# implementing exactly as documented to verify behavior

UPLOAD_DIR = "src/public/uploads"
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "application/pdf": ".pdf"
}

@post("/api/files/upload")
async def upload_file(request, response):
    # check for file in request.files (documented)
    if "file" not in request.files:
        return response.json({"error": "No file provided. Send a file with field name 'file'"}, 400)

    file = request.files["file"]

    # Check file type
    if file["type"] not in ALLOWED_TYPES:
        return response.json({
            "error": f"File type '{file['type']}' not allowed",
            "allowed": list(ALLOWED_TYPES.keys())
        }, 400)

    # Check file size
    if file["size"] > MAX_FILE_SIZE:
        return response.json({
            "error": f"File too large. Maximum size is {MAX_FILE_SIZE // (1024 * 1024)} MB",
            "size": file["size"]
        }, 400)

    # Generate a unique filename
    ext = ALLOWED_TYPES[file["type"]]
    unique_name = f"{uuid.uuid4().hex}{ext}"

    # Save the file
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    save_path = os.path.join(UPLOAD_DIR, unique_name)
    with open(save_path, "wb") as f:
        f.write(file["content"])

    return response.json({
        "message": "File uploaded successfully",
        "file": {
            "original_name": file["filename"],
            "saved_as": unique_name,
            "url": f"/uploads/{unique_name}",
            "size": file["size"],
            "content_type": file["type"]
        }
    }, 201)

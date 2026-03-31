require "securerandom"
require "fileutils"

 # exercise solution: image upload api - ch03 section 12

 # post: upload an image, validate type and size, save and return url
Tina4::Router.post("/api/images") do |request, response|
  if request.files["image"].nil?
    return response.json({ error: "No image file provided. Use field name 'image'." }, 400)
  end

  file = request.files["image"]

  allowed_types = ["image/jpeg", "image/png", "image/webp"]
  unless allowed_types.include?(file.type)
    return response.json({
      error: "Invalid file type",
      received: file.type,
      allowed: allowed_types
    }, 400)
  end

  max_size = 2 * 1024 * 1024
  if file.size > max_size
    return response.json({
      error: "File too large",
      size_bytes: file.size,
      max_bytes: max_size
    }, 400)
  end

  extension = File.extname(file.name).downcase
  saved_name = "img_#{SecureRandom.hex(8)}#{extension}"
  upload_dir = File.join(__dir__, "../../public/uploads")
  destination = File.join(upload_dir, saved_name)

  FileUtils.mkdir_p(upload_dir) unless Dir.exist?(upload_dir)
  FileUtils.mv(file.tmp_path, destination)

  response.json({
    message: "Image uploaded successfully",
    original_name: file.name,
    saved_name: saved_name,
    size_kb: (file.size / 1024.0).round(1),
    type: file.type,
    url: "/uploads/#{saved_name}"
  }, 201)
end

 # get: serve an uploaded image by filename
Tina4::Router.get("/api/images/{filename}") do |request, response|
  filename = request.params["filename"]

  if filename.include?("..") || filename.include?("/")
    return response.json({ error: "Invalid filename" }, 400)
  end

  filepath = File.join(__dir__, "../../public/uploads", filename)

  unless File.exist?(filepath)
    return response.json({ error: "Image not found", filename: filename }, 404)
  end

  response.file(filepath)
end

require "securerandom"
require "fileutils"

 # testing file uploads (single, with validation, and multiple) - ch03 sections 7

 # single file upload - inspect metadata only, no saving
Tina4::Router.post("/api/upload") do |request, response|
  if request.files["image"].nil?
    return response.json({ error: "No file uploaded" }, 400)
  end

  file = request.files["image"]

  response.json({
    name: file.name,
    type: file.type,
    size: file.size,
    tmp_path: file.tmp_path
  })
end

 # single file upload with type + size validation and saving to public/uploads
Tina4::Router.post("/api/upload/save") do |request, response|
  if request.files["image"].nil?
    return response.json({ error: "No file uploaded" }, 400)
  end

  file = request.files["image"]

  allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
  unless allowed_types.include?(file.type)
    return response.json({ error: "Invalid file type. Allowed: JPEG, PNG, GIF, WebP" }, 400)
  end

  max_size = 5 * 1024 * 1024
  if file.size > max_size
    return response.json({ error: "File too large. Maximum size: 5MB" }, 400)
  end

  extension = File.extname(file.name)
  filename = "img_#{SecureRandom.hex(8)}#{extension}"
  upload_dir = File.join(__dir__, "../../public/uploads")
  destination = File.join(upload_dir, filename)

  FileUtils.mkdir_p(upload_dir) unless Dir.exist?(upload_dir)
  FileUtils.mv(file.tmp_path, destination)

  response.json({
    message: "File uploaded successfully",
    filename: filename,
    url: "/uploads/#{filename}",
    size: file.size
  }, 201)
end

 # multiple file upload - iterate all uploaded files
Tina4::Router.post("/api/upload-many") do |request, response|
  results = []

  request.files.each do |key, file|
    extension = File.extname(file.name)
    filename = "file_#{SecureRandom.hex(8)}#{extension}"
    upload_dir = File.join(__dir__, "../../public/uploads")
    destination = File.join(upload_dir, filename)

    FileUtils.mkdir_p(upload_dir) unless Dir.exist?(upload_dir)
    FileUtils.mv(file.tmp_path, destination)

    results << {
      original_name: file.name,
      saved_as: filename,
      url: "/uploads/#{filename}"
    }
  end

  response.json({ uploaded: results, count: results.length }, 201)
end

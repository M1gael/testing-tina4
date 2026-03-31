# testing query and path parameters with a book api
# in-memory data store
books = [
  { id: 1, title: "Dune", author: "Frank Herbert", year: 1965 },
  { id: 2, title: "Neuromancer", author: "William Gibson", year: 1984 },
  { id: 3, title: "Snow Crash", author: "Neal Stephenson", year: 1992 }
]

Tina4::Router.get("/api/books") do |request, response|
  # list all books. supports ?author= filter and ?sort=year.
  author = request.params["author"] || ""
  sort_by = request.params["sort"] || ""

  result = books

  # filter by author if the query param is present
  unless author.empty?
    result = result.select { |b| b[:author].downcase.include?(author.downcase) }
  end

  # sort by year if requested
  if sort_by == "year"
    result = result.sort_by { |b| b[:year] }
  end

  response.json({ books: result, count: result.length })
end

Tina4::Router.get("/api/books/{id:int}") do |request, response|
  # get a single book by id. returns 404 if not found.
  id = request.params["id"]
  book = books.find { |b| b[:id] == id }

  if book.nil?
    return response.json({ error: "Book with id #{id} not found" }, 404)
  end

  response.json(book)
end

Tina4::Router.post("/api/books") do |request, response|
  # create a new book from the json body. returns 201 on success.
  title = request.body["title"] || ""
  author = request.body["author"] || ""
  year = request.body["year"] || 0

  if title.empty? || author.empty?
    return response.json({ error: "title and author are required" }, 400)
  end

  new_book = {
    id: books.map { |b| b[:id] }.max + 1,
    title: title,
    author: author,
    year: year
  }
  books << new_book

  response.json(new_book, 201)
end

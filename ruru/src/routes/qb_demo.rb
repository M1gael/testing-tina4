 # query builder verification routes - ch07
Tina4::Router.get("/api/qb-test") do |request, response|
  begin
    # 1. Join query
    results = Tina4::QueryBuilder.from("posts")
      .select("posts.id", "posts.title", "authors.name AS author_name")
      .join("authors", "authors.id = posts.author_id")
      .where("posts.status = ?", ["published"])
      .order_by("posts.id DESC")
      .get

    # 2. Aggregation with group_by and having
    stats = Tina4::QueryBuilder.from("notes")
      .select("tag", "COUNT(*) AS note_count")
      .group_by("tag")
      .having("COUNT(*) > ?", [0])
      .get

    response.json({
      posts: results,
      stats: stats
    })
  rescue => e
    response.json({ error: e.message, backtrace: e.backtrace.first(5) }, 500)
  end
end

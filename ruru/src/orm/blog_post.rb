 # blog post model - ch06 section 6
class BlogPost < Tina4::ORM
  integer_field :id, primary_key: true, auto_increment: true
  integer_field :author_id, nullable: false
  string_field :title, nullable: false
  string_field :slug, nullable: false
  string_field :content, default: ""
  string_field :status, default: "draft"
  datetime_field :created_at
  datetime_field :updated_at

  table_name "posts"

  belongs_to :author, class_name: "Author", foreign_key: "author_id"

  def self.published
    where("status = ?", ["published"])
  end

  def self.drafts
    where("status = ?", ["draft"])
  end

  def self.recent(days = 7)
    where(
      "created_at > datetime('now', ?)",
      ["-#{days} days"]
    )
  end
end

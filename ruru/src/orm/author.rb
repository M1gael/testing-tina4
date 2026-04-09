 # author model - ch06 section 6
class Author < Tina4::ORM
  integer_field :id, primary_key: true, auto_increment: true
  string_field :name, nullable: false
  string_field :email, nullable: false
  string_field :bio, default: ""
  datetime_field :created_at

  has_many :posts, class_name: "BlogPost", foreign_key: "author_id"
end

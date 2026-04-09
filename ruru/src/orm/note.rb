 # note model - ch06 section 2
class Note < Tina4::ORM
  self.field_mapping = {
    "category" => "tag"
  }

  integer_field :id, primary_key: true, auto_increment: true
  string_field :title, nullable: false
  string_field :content, default: ""
  string_field :category, default: "general"
  integer_field :pinned, default: 0
  datetime_field :created_at
  datetime_field :updated_at
end

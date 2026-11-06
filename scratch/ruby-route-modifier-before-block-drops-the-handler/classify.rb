# Usage: ruby classify.rb FILE.md... -> one line per Route modifier that is handed a block or an
# argument the API does not take, in any ```ruby fence. A route block must go to Router.<verb>;
# Route#no_auth/secure/no_csrf/cache take no block (and cache/no_auth/secure/no_csrf no argument).
require "prism"
MODS = %w[no_auth secure no_csrf cache middleware role can].freeze
NOARG = %w[no_auth secure no_csrf cache].freeze
VERBS = %w[get post put patch delete any head options].freeze
def route_chain?(n)
  while n.is_a?(Prism::CallNode)
    return true if VERBS.include?(n.name.to_s) && n.receiver && n.receiver.slice =~ /\A(Tina4::)?Router\z/
    return false unless MODS.include?(n.name.to_s)
    n = n.receiver
  end
  false
end
class V < Prism::Visitor
  attr_reader :hits
  def initialize(f, base) = (@f, @base, @hits = f, base, [])
  def visit_call_node(n)
    if MODS.include?(n.name.to_s) && route_chain?(n.receiver)
      why = []
      why << "block on .#{n.name}" if n.block.is_a?(Prism::BlockNode)
      why << ".#{n.name} takes no argument" if NOARG.include?(n.name.to_s) && n.arguments
      @hits << "#{@f}:#{@base + n.location.start_line - 1}\t#{why.join(', ')}\t#{n.slice.lines.first.strip}" unless why.empty?
    end
    super
  end
end
ARGV.each do |f|
  lines = File.readlines(f); i = 0
  while i < lines.size
    if lines[i] =~ /\A\s*```ruby\s*\z/
      s = i; i += 1; i += 1 until i >= lines.size || lines[i] =~ /\A\s*```\s*\z/
      src = lines[(s + 1)...i].join
      r = Prism.parse(src)
      v = V.new(File.basename(f), s + 1); r.value.accept(v); v.hits.each { |h| puts h }
    end
    i += 1
  end
end

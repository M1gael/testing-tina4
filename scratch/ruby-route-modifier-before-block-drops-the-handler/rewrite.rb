# Usage: ruby rewrite.rb FILE.md... -> rewrites in place every `Router.<verb>(p)<mods> do |..| .. end`
# in a ```ruby fence to `Router.<verb>(p) do |..| .. end<mods>` (the block goes to the verb, the
# modifiers chain after `end`, as router.rb documents). Prints each change.
require "prism"
MODS = %w[no_auth secure no_csrf cache middleware role can].freeze
VERBS = %w[get post put patch delete any head options].freeze
def verb_call(n)
  while n.is_a?(Prism::CallNode)
    return n if VERBS.include?(n.name.to_s) && n.receiver && n.receiver.slice =~ /\A(Tina4::)?Router\z/
    return nil unless MODS.include?(n.name.to_s)
    n = n.receiver
  end
end
class V < Prism::Visitor
  attr_reader :edits
  def initialize = @edits = []
  def visit_call_node(n)
    if MODS.include?(n.name.to_s) && n.block.is_a?(Prism::BlockNode) && (v = verb_call(n.receiver))
      b = n.block.location
      mods = [v.location.end_offset, b.start_offset]   # ".no_auth.middleware(X) " incl. trailing space
      @edits << [mods, b.end_offset]
    end
    super
  end
end
ARGV.each do |f|
  lines = File.readlines(f); i = 0; out = lines.dup
  while i < lines.size
    if lines[i] =~ /\A\s*```ruby\s*\z/
      s = i; i += 1; i += 1 until i >= lines.size || lines[i] =~ /\A\s*```\s*\z/
      src = lines[(s + 1)...i].join; bsrc = src.b
      v = V.new; Prism.parse(src).value.accept(v)
      v.edits.sort_by { |(a, _), _| -a }.each do |(a, z), e|
        mod = bsrc[a...z].rstrip
        bsrc = bsrc[0...e] + mod + bsrc[e..] ; bsrc = bsrc[0...a] + " " + bsrc[z..]
        puts "#{File.basename(f)}: moved #{mod.strip} after `end`"
      end
      out[(s + 1)...i] = bsrc.force_encoding("UTF-8").lines unless v.edits.empty?
      lines = out.dup if false
    end
    i += 1
  end
  File.write(f, out.join)
end

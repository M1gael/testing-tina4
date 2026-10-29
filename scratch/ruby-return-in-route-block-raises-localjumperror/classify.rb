# Usage: ruby classify.rb FILE.md...  -> prints "kind<TAB>file:line<TAB>source line" for every `return`
# Parses every ```ruby fence with Prism (ruby's own parser) and classifies each ReturnNode by
# its innermost enclosing scope: def, lambda, route-block, other-block, top.
require "prism"
VERBS = %w[get post put patch delete any].freeze

def block_kind(call)
  name = call.name.to_s
  return "lambda" if name == "lambda"
  return "proc" if name == "proc" || (name == "new" && call.receiver&.slice == "Proc")
  r = call.receiver
  if VERBS.include?(name)
    return "route-block" if r.nil? || r.slice =~ /(\A|::)Router\z/ || r.is_a?(Prism::LocalVariableReadNode) || r.is_a?(Prism::CallNode) && r.name.to_s =~ /\A(group|no_auth|secure)\z/
  end
  "other-block:#{r ? r.slice + '.' : ''}#{name}"
end

def walk(node, stack, out)
  return unless node
  case node
  when Prism::ReturnNode
    s = stack.last || "top"
    out << [s, node.location.start_line]
  end
  pushed = nil
  if node.is_a?(Prism::DefNode) then pushed = "def"
  elsif node.is_a?(Prism::LambdaNode) then pushed = "lambda"
  elsif node.is_a?(Prism::CallNode) && node.block.is_a?(Prism::BlockNode)
    node.child_nodes.each { |c| walk(c, stack, out) unless c.equal?(node.block) }
    stack.push(block_kind(node)); walk(node.block, stack, out); stack.pop
    return
  end
  stack.push(pushed) if pushed
  node.child_nodes.each { |c| walk(c, stack, out) }
  stack.pop if pushed
end

ARGV.each do |f|
  lines = File.readlines(f)
  i = 0
  while i < lines.size
    if lines[i] =~ /\A\s*```ruby\s*\z/
      start = i + 1; j = start
      j += 1 while j < lines.size && lines[j] !~ /\A\s*```\s*\z/
      code = lines[start...j].join
      res = Prism.parse(code)
      warn "PARSE-ERR #{f}:#{start + 1} #{res.errors.first.message}" unless res.errors.empty?
      out = []; walk(res.value, [], out)
      out.each { |k, l| puts [k, "#{f}:#{start + l}", lines[start + l - 1].strip].join("\t") }
      i = j
    end
    i += 1
  end
end

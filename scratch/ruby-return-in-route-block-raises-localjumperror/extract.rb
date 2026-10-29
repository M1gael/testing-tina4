# Usage: ruby extract.rb FILE.md ANCHOR -> prints, verbatim, the ```ruby fence containing ANCHOR
f, anchor = ARGV
l = File.readlines(f)
n = l.index { |x| x.include?(anchor) } or abort("anchor not found: #{anchor} in #{f}")
s = n; s -= 1 until l[s] =~ /\A\s*```ruby/
e = n; e += 1 until l[e] =~ /\A\s*```\s*\z/
print l[(s + 1)...e].join

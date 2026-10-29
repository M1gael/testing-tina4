# Usage: ruby patchlines.rb PATCH -> "file:line" (stock numbering) of every removed line
f=nil; ln=0
File.foreach(ARGV[0]) do |l|
  if l.start_with?("--- a/") then f=l[6..].strip
  elsif l =~ /\A@@ -(\d+)/ then ln=$1.to_i
  elsif l.start_with?("+++") then next
  elsif l.start_with?("-") then puts "#{f}:#{ln}"; ln+=1
  elsif l.start_with?("+") then next
  else ln+=1 end
end

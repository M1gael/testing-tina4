# Usage: ruby probe_rb.rb <tina4-ruby src root> <latest|earliest>
# Same scenario as probe_py.py, through Tina4::QueueBackends::KafkaBackend (rdkafka).
root, reset = ARGV
$LOAD_PATH.unshift(File.join(root, "lib"))
require "tina4"
brokers = ENV.fetch("TINA4_KAFKA_BROKERS")
topic = "frq01_rb_#{rand(1 << 32).to_s(16)}"
ENV.delete("TINA4_KAFKA_AUTO_OFFSET_RESET")
prod = Tina4::QueueBackends::KafkaBackend.new(brokers: brokers, group_id: "frq01_prod")
job = ->(n) { Tina4::Job.new(topic: topic, payload: { "n" => n }) }
3.times { |i| prod.enqueue(job.call("old-#{i}")) }
ENV["TINA4_KAFKA_AUTO_OFFSET_RESET"] = reset
cons = Tina4::QueueBackends::KafkaBackend.new(brokers: brokers, group_id: "frq01_grp_#{rand(1 << 32).to_s(16)}")
name = ->(j) { j && (j.payload["n"] || j.payload[:n]) }
seen = [name.call(cons.dequeue(topic))]
prod.enqueue(job.call("new"))
6.times { v = name.call(cons.dequeue(topic)); seen << v; break if v == "new" }
puts "rb[rdkafka] reset=#{reset} seen=#{seen.inspect}"
old = seen.compact.select { |s| s.start_with?("old") }
if reset == "latest"
  puts "VERDICT " + (old.empty? && seen.include?("new") ? "PASS" : old.any? ? "FAIL (replayed backlog)" : "ERROR (new not seen)")
else
  puts "VERDICT " + (seen[0] == "old-0" ? "PASS" : "FAIL")
end

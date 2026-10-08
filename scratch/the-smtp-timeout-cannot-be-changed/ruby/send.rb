# One Messenger send to a host that accepts the TCP connection and never speaks.
# Usage: ruby -I<tree>/lib send.rb PORT [ctor-timeout]
require "tina4"
port = Integer(ARGV[0])
opts = { host: "127.0.0.1", port: port, from_address: "app@localhost", encryption: "none" }
opts[:timeout] = Integer(ARGV[1]) if ARGV[1]
t0 = Process.clock_gettime(Process::CLOCK_MONOTONIC)
begin
  result = Tina4::Messenger.new(**opts).send(to: "someone@localhost", subject: "test", body: "hello")
  outcome = result.is_a?(Hash) ? "success=#{result[:success].inspect} message=#{result[:message] || result[:error]}" : result.inspect
rescue Exception => e
  outcome = "#{e.class}: #{e.message}"
end
printf("ELAPSED=%.1f OUTCOME=%s\n", Process.clock_gettime(Process::CLOCK_MONOTONIC) - t0, outcome)

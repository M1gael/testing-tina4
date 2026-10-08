# Does the database layer accept a pgsql:// URL the way it accepts postgres://?
# PORT is a listener that counts connections (listener.py): a URL the driver can
# use reaches it; one that fails before the network does not.
require "tina4"
port = Integer(ARGV[0])
%w[pgsql postgres postgresql].each do |scheme|
  url = "#{scheme}://127.0.0.1:#{port}/x"
  engine = begin
    Tina4::DatabaseUrl.new(url).engine
  rescue => e
    e.class.to_s
  end
  db = nil
  outcome = begin
    db = Tina4::Database.new(url)
    db.fetch("SELECT 1")
    "connected?!"
  rescue Exception => e
    "#{e.class}: #{e.message.sub(/\A.*?: (?=PG::)/, '')[0, 90]}"
  end
  sleep 0.3
  puts "#{scheme.ljust(10)} DatabaseUrl engine=#{engine}; driver=#{db&.instance_variable_get(:@driver_name).inspect}; listener connections so far=#{File.read(ARGV[1]).split.last.to_i}; #{outcome}"
end

# port_busy <port>: true if something listens on 127.0.0.1:<port>. wait_port_free <port>: block (<=15s) until it is free.
port_busy(){ (exec 3<>/dev/tcp/127.0.0.1/$1) 2>/dev/null; }
wait_port_free(){ local i; for i in $(seq 60); do port_busy $1 || return 0; sleep 0.25; done; echo "  PORT $1 still busy after stop" >&2; return 1; }

import socket
import time

HOST = "127.0.0.1"
PORT = 5003

# Client setup

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
    client.connect((HOST, PORT))
    print(f"Connected to server at {HOST}:{PORT}")
    
    
    # Send and measure RTT
    
    message_id = 1
    delay_ms = 100
    message = f"PING {message_id} {delay_ms}\n"

    with client.makefile("r", encoding="utf-8") as replies:
        # Measure time
        start_time = time.perf_counter()
        client.sendall(message.encode("utf-8"))

        reply = replies.readline()
        end_time = time.perf_counter()

        if reply.strip() == f"PONG {message_id}":
            rtt_ms = (end_time - start_time) * 1000
            print(f"Added server delay: {delay_ms} ms")
            print(f"Round-trip time: {rtt_ms:.2f} ms")
        else:
            print(f"Unexpected reply or disconnected server: {reply!r}")
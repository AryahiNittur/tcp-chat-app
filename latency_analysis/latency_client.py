import socket
import time

HOST = "127.0.0.1"
PORT = 5003

# Client setup

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
    client.connect((HOST, PORT))
    print(f"Connected to server at {HOST}:{PORT}")
    
    
    # Send and measure RTT
    
    message_id = 0

    with client.makefile("r", encoding="utf-8") as replies:
        for delay_ms in [0, 100, 300]:
            measurements = []
            print(f"\nTesting {delay_ms} ms added delay")

            for trial in range(10):
                message_id += 1
                message = f"PING {message_id} {delay_ms}\n"

                start_time = time.perf_counter()
                client.sendall(message.encode("utf-8"))

                reply = replies.readline()
                end_time = time.perf_counter()

                if reply.strip() != f"PONG {message_id}":
                    raise RuntimeError(
                        f"Unexpected reply or disconnected server: {reply!r}"
                    )

                rtt_ms = (end_time - start_time) * 1000
                measurements.append(rtt_ms)

                print(f"Trial {trial + 1}: {rtt_ms:.2f} ms")

            average_rtt = sum(measurements) / len(measurements)

            print(
                f"Summary for {delay_ms} ms delay: "
                f"average={average_rtt:.2f} ms, "
                f"min={min(measurements):.2f} ms, "
                f"max={max(measurements):.2f} ms"
            )
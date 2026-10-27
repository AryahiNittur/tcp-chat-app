import socket
import time

HOST = "127.0.0.1"
PORT = 5003

# Creates the tcp socket and starts listening

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()

    print(f"Latency server is listening on {HOST}:{PORT}")
    
    # Wait until a client connects
    connectionSocket, addr = server.accept()
    print(f"Client is connected: {addr}")
    
    # Close the client connection automatically
    with connectionSocket:
        with connectionSocket.makefile("r", encoding="utf-8") as messages:
            # Extract delay
            for message in messages:
                print(f"Received: {message.strip()}")
                parts = message.strip().split()

                try:
                    if len(parts) != 3 or parts[0] != "PING":
                        raise ValueError

                    message_id = int(parts[1])
                    delay_ms = int(parts[2])

                    if not 0 <= delay_ms <= 1000:
                        raise ValueError

                except ValueError:
                    connectionSocket.sendall(b"ERROR Use: PING <id> <delay_ms:0-1000>\n")
                    continue
                
                # Introduce artificial delay
                time.sleep(delay_ms / 1000)

                reply = f"PONG {message_id}\n"
                connectionSocket.sendall(reply.encode("utf-8"))

                print(f"Sent PONG {message_id} after {delay_ms} ms added delay")
                
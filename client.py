"""Broadcast chat client (CSE 3461 Project, Feature 1).

Connects to the chat server over TCP.

"""

import os
import socket
import sys
import threading

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 12345
BUFFER_SIZE = 1024


def receive_messages(sock):
    """Print messages from the server until the connection closes.

    Runs in a background thread.

    Args:
        sock: The socket connected to the server.
    """
    # Messages end with "\n"; buffer the byte stream and split on it.
    buffer = b""
    while True:
        try:
            data = sock.recv(BUFFER_SIZE)
        except OSError:
            break  # Socket was closed locally.
        if not data:  # Empty read means the server closed the connection.
            print("\n[!] Server disconnected.")
            break
        buffer += data
        while b"\n" in buffer:
            line, buffer = buffer.split(b"\n", 1)
            print(line.decode(errors="replace"))
    # The main thread is blocked on input(), so exit the process directly.
    os._exit(0)


def main():
    """Connect to the server and send user input until /quit."""
    host = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_HOST
    port = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_PORT

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((host, port))
    except OSError as e:
        print(f"Could not connect to {host}:{port}: {e}")
        sys.exit(1)

    local_ip, local_port = sock.getsockname()
    print(f"Connected to server {host}:{port}")
    print(f"My local address: {local_ip}:{local_port}")
    print("Type a message and press Enter to send. Type /quit to exit.\n")

    threading.Thread(target=receive_messages, args=(sock,), daemon=True).start()

    try:
        while True:
            message = input()
            if message.strip() == "/quit":
                break
            if message.strip():
                # "\n" marks the end of the message for the server.
                sock.sendall((message + "\n").encode())
    except (EOFError, KeyboardInterrupt):
        pass
    except OSError:
        print("[!] Lost connection to the server.")
    finally:
        sock.close()
        print("Disconnected.")


if __name__ == "__main__":
    main()
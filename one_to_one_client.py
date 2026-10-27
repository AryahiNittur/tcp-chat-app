"""One-to-one chat client (CSE 3461 Project, Feature 2).

Connects to one_to_one_server.py, registers a username, then sends
private messages typed as:

    @username message text

Simulation:  python one_to_one_client.py
Over the air: python one_to_one_client.py <server LAN IP>
"""

import os
import socket
import sys
import threading

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 12345
BUFFER_SIZE = 1024

# Set before this client closes its own socket, so the receive thread
# does not treat a local /quit as "the server disconnected".
shutting_down = threading.Event()


def recv_line(sock, buffer):
    """Read one newline-terminated line from the server.

    Args:
        sock: Socket connected to the server.
        buffer: Bytes already read but not yet consumed.

    Returns:
        (text, buffer). text has the trailing newline removed.

    Raises:
        ConnectionError: The server closed the connection.
    """
    while b"\n" not in buffer:
        try:
            data = sock.recv(BUFFER_SIZE)
        except OSError as exc:
            raise ConnectionError("Lost connection to the server.") from exc
        if not data:
            raise ConnectionError("Server disconnected.")
        buffer += data
    line, buffer = buffer.split(b"\n", 1)
    return line.decode(errors="replace").rstrip("\r"), buffer


def register(sock):
    """Answer username prompts until the server sends a welcome line.

    The receive thread is not running yet, so this function is the only
    reader on the socket. Leftover bytes are returned for that thread.

    Args:
        sock: Socket connected to the server.

    Returns:
        Bytes read past the welcome line, usually empty.
    """
    buffer = b""
    while True:
        line, buffer = recv_line(sock, buffer)
        print(line, flush=True)
        if line.startswith("Enter username"):
            name = input().strip()
            # "\n" is the message boundary. Extra spaces were stripped.
            sock.sendall((name + "\n").encode())
        elif line.startswith("Welcome,"):
            return buffer


def receive_messages(sock, buffer):
    """Print server lines until the connection closes.

    Runs as a daemon thread. On a real server disconnect, the process
    exits so the main thread is not left blocked inside input().

    Args:
        sock: Socket connected to the server.
        buffer: Bytes already read during username registration.
    """
    while not shutting_down.is_set():
        try:
            data = sock.recv(BUFFER_SIZE)
        except OSError:
            break
        if not data:
            break
        buffer += data
        while b"\n" in buffer:
            line, buffer = buffer.split(b"\n", 1)
            print(line.decode(errors="replace").rstrip("\r"), flush=True)
    if not shutting_down.is_set():
        print("\n[!] Server disconnected.", flush=True)
        os._exit(0)


def main():
    """Connect, register a username, then send keyboard input."""
    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        print("Usage: python one_to_one_client.py [host] [port]")
        sys.exit(0)

    host = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_HOST
    if len(sys.argv) > 2:
        try:
            port = int(sys.argv[2])
        except ValueError:
            print("Usage: python one_to_one_client.py [host] [port]")
            sys.exit(1)
    else:
        port = DEFAULT_PORT

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((host, port))
    except OSError as exc:
        print(f"Could not connect to {host}:{port}: {exc}")
        sys.exit(1)

    local_ip, local_port = sock.getsockname()
    print(f"Connected to server {host}:{port}")
    print(f"My local address: {local_ip}:{local_port}")
    print("Type @username message to send. Type /quit to exit.\n")

    try:
        buffer = register(sock)
        threading.Thread(
            target=receive_messages,
            args=(sock, buffer),
            daemon=True,
        ).start()

        while True:
            message = input()
            if message.strip() == "/quit":
                break
            sock.sendall((message + "\n").encode())
    except (EOFError, KeyboardInterrupt):
        pass
    except OSError:
        print("[!] Lost connection to the server.")
    except ConnectionError as exc:
        print(f"[!] {exc}")
    finally:
        shutting_down.set()
        try:
            sock.close()
        except OSError:
            pass
        print("Disconnected.")


if __name__ == "__main__":
    main()

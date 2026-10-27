"""Broadcast chat server (CSE 3461 Project, Feature 1).

Accepts multiple TCP clients and relays each message a client sends to
every other connected client. Each client is handled in its own thread.

"""

import socket
import sys
import threading

HOST = "0.0.0.0"  # Accept connections from other machines
DEFAULT_PORT = 12345
BUFFER_SIZE = 1024

# Shared across client threads
clients = []
clients_lock = threading.Lock()


def get_lan_ip():
    """Return this machine's LAN IP address.

    Connecting a UDP socket asks the OS
    which network interface it would use, which gives us the LAN IP.

    Returns:
        The LAN IP as a string, or "127.0.0.1" if no network is available.
    """
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.connect(("8.8.8.8", 80))
        return probe.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        probe.close()


def remove_client(client_sock):
    """Remove a client from the active list and close its socket.

    Args:
        client_sock: The client's socket.
    """
    with clients_lock:
        if client_sock in clients:
            clients.remove(client_sock)
    try:
        client_sock.close()
    except OSError:
        pass


def broadcast(message, sender_sock):
    """Send a message to every connected client except the sender.

    Args:
        message: The text to send, ending in a newline.
        sender_sock: The socket of the client who sent the message.
    """
    # doesn't block the other threads.
    with clients_lock:
        recipients = [c for c in clients if c is not sender_sock]

    for client_sock in recipients:
        try:
            client_sock.sendall(message.encode())
        except OSError:
            remove_client(client_sock)


def handle_client(client_sock, client_addr):
    """Receive messages from one client and broadcast them to the others.

    Runs in its own thread until the client disconnects.

    Args:
        client_sock: The connected client's socket.
        client_addr: The client's (ip, port) tuple.
    """
    label = f"{client_addr[0]}:{client_addr[1]}"
    with clients_lock:
        online = len(clients)
    print(f"[+] {label} connected ({online} client(s) online)")
    broadcast(f"*** {label} joined the chat ***\n", client_sock)

    # TCP is a byte stream, so one recv() can contain part of a message or
    # several messages. Messages end with "\n", so we buffer and split on it.
    buffer = b""
    try:
        while True:
            data = client_sock.recv(BUFFER_SIZE)
            if not data:  # Empty read means the client closed the connection.
                break
            buffer += data
            while b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)
                text = line.decode(errors="replace").strip()
                if text:
                    print(f"[{label}] {text}")
                    broadcast(f"[{label}] {text}\n", client_sock)
    except OSError:
        pass  # Client disconnected unexpectedly.
    finally:
        remove_client(client_sock)
        with clients_lock:
            online = len(clients)
        print(f"[-] {label} disconnected ({online} client(s) online)")
        broadcast(f"*** {label} left the chat ***\n", client_sock)


def main():
    """Start the server and accept clients until Ctrl+C is pressed."""
    port = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT

    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Lets the server restart right away without "address already in use".
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((HOST, port))
    server_sock.listen()
    # accept() ignores it on Windows.
    server_sock.settimeout(1.0)

    print(f"Broadcast server listening on port {port}")
    print(f"  Same computer: connect to 127.0.0.1:{port}")
    print(f"  Same network:  connect to {get_lan_ip()}:{port}")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            try:
                client_sock, client_addr = server_sock.accept()
            except socket.timeout:
                continue
            client_sock.settimeout(None)  # Client sockets should block normally.
            with clients_lock:
                clients.append(client_sock)
            threading.Thread(
                target=handle_client,
                args=(client_sock, client_addr),
                daemon=True,  # Don't keep the program alive after main() exits.
            ).start()
    except KeyboardInterrupt:
        print("\nShutting down server...")
    finally:
        with clients_lock:
            for c in clients:
                try:
                    c.close()
                except OSError:
                    pass
        server_sock.close()


if __name__ == "__main__":
    main()
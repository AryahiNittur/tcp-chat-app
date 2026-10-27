"""One-to-one chat server (CSE 3461 Project, Feature 2).

Clients register a username, then send private messages as:

    @username message text

The server delivers each message only to that username's socket.
Feature 1 (broadcast) stays in server.py so the two demos stay separate.

Simulation:  python one_to_one_server.py
Over the air: same command. It binds 0.0.0.0 and prints the LAN IP
other machines should connect to. Everyone must be on the same network.
"""

import socket
import sys
import threading

HOST = "0.0.0.0"  # Accept connections from other machines on the LAN
DEFAULT_PORT = 12345
BUFFER_SIZE = 1024

# username -> socket. Every read and write takes clients_lock.
clients = {}
clients_lock = threading.Lock()

# Two threads must not write one socket at the same time. TCP would
# mix the bytes and the client would see a merged or torn line.
# Lock order is clients_lock, then send_lock. Never the reverse.
send_lock = threading.Lock()


def get_lan_ip():
    """Return this machine's LAN IP address.

    Connecting a UDP socket asks the OS which interface it would use
    to reach the Internet. That interface address is the LAN IP
    teammates should type. No packet is actually sent.

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


def send_line(sock, text):
    """Send one newline-terminated line.

    Messages end with \\n because TCP has no message boundaries.
    A later recv may return part of a line or several lines at once.

    Args:
        sock: Destination socket.
        text: Line contents, without the trailing newline.

    Raises:
        OSError: The peer is already gone.
    """
    with send_lock:
        sock.sendall((text + "\n").encode())


def send_to_user(username, text):
    """Deliver one line to a registered user.

    The socket is looked up under the lock, then the lock is released
    before sendall so a slow client cannot stall the other threads.
    If the target disconnects between the lookup and the send, sendall
    raises and the username is removed.

    Args:
        username: Registered name.
        text: Line contents, without the trailing newline.

    Returns:
        True if the line was written to the socket.
    """
    with clients_lock:
        sock = clients.get(username)
    if sock is None:
        return False
    try:
        send_line(sock, text)
        return True
    except OSError:
        with clients_lock:
            # A new login may already have reused this username.
            if clients.get(username) is sock:
                del clients[username]
        try:
            sock.close()
        except OSError:
            pass
        return False


def recv_line(sock, buffer):
    """Read one newline-terminated line from a TCP byte stream.

    Args:
        sock: Connected socket.
        buffer: Bytes already read but not yet consumed.

    Returns:
        (text, buffer). text is None when the peer closes the connection.
        Surrounding whitespace is removed so "  alice  " is "alice".
    """
    while b"\n" not in buffer:
        data = sock.recv(BUFFER_SIZE)
        if not data:
            return None, buffer
        buffer += data
    line, buffer = buffer.split(b"\n", 1)
    text = line.decode(errors="replace").strip()
    return text, buffer


def claim_username(client_sock, requested):
    """Reserve a username if it is non-empty, has no spaces, and is free.

    On failure the client is told why and prompted again. The socket is
    published in the dictionary only after the checks pass, and only
    while holding clients_lock, so two clients cannot take one name.

    Args:
        client_sock: Socket that asked for the name.
        requested: Username line, already stripped.

    Returns:
        The accepted username, or None if the client must try again.
    """
    if not requested:
        send_line(client_sock, "Username cannot be empty.")
        send_line(client_sock, "Enter username: ")
        return None
    # "@alice   hello" splits on whitespace, so a name cannot contain it.
    if any(ch.isspace() for ch in requested):
        send_line(client_sock, "Username cannot contain spaces.")
        send_line(client_sock, "Enter username: ")
        return None

    with clients_lock:
        if requested in clients:
            taken = True
        else:
            clients[requested] = client_sock
            taken = False
    if taken:
        send_line(client_sock, "Username already taken.")
        send_line(client_sock, "Enter username: ")
        return None
    return requested


def handle_message(sender, text):
    """Route one chat line from sender, or explain what was wrong.

    Accepted form is "@username message". The message may contain
    spaces. Extra spaces around the username and the message are
    ignored. An empty message is not delivered.

    Args:
        sender: Username of the client who sent the line.
        text: One stripped line, without the newline.
    """
    if not text:
        return

    if not text.startswith("@"):
        print(f"[{sender}] bad format")
        send_to_user(sender, "Use @username message")
        return

    # split(None, 1) breaks on the first span of whitespace, so
    # "@bob    hello   there" has target bob and text "hello   there".
    parts = text[1:].split(None, 1)
    if len(parts) < 2 or not parts[1].strip():
        print(f"[{sender}] empty message")
        send_to_user(sender, "Use @username message")
        return

    target = parts[0]
    message = parts[1].strip()
    if target == sender:
        print(f"[{sender}] tried to message self")
        send_to_user(sender, "You cannot message yourself.")
        return

    if send_to_user(target, f"[{sender}]: {message}"):
        print(f"[{sender} -> {target}] {message}")
    else:
        print(f"[{sender}] user not found: {target}")
        send_to_user(sender, "user not found")


def handle_client(client_sock, client_addr):
    """Register one client, then route that client's private messages.

    Runs in its own thread. The username is removed in finally so a
    dropped connection cannot leave a dead socket in the dictionary.

    Args:
        client_sock: The connected client's socket.
        client_addr: The client's (ip, port) tuple.
    """
    username = None
    buffer = b""
    where = f"{client_addr[0]}:{client_addr[1]}"
    try:
        send_line(client_sock, "Enter username: ")
        while username is None:
            requested, buffer = recv_line(client_sock, buffer)
            if requested is None:
                return
            username = claim_username(client_sock, requested)

        with clients_lock:
            online = len(clients)
        print(f"[+] {username} connected from {where} ({online} online)")
        send_line(
            client_sock,
            f"Welcome, {username}. "
            "Send private messages as @username message",
        )

        while True:
            text, buffer = recv_line(client_sock, buffer)
            if text is None:
                break
            handle_message(username, text)
    except OSError:
        pass  # Client disconnected, or we closed the socket ourselves.
    finally:
        with clients_lock:
            # Identity check: do not delete a newer login with this name.
            if username is not None and clients.get(username) is client_sock:
                del clients[username]
            online = len(clients)
        if username is not None:
            print(f"[-] {username} disconnected ({online} online)")
        try:
            client_sock.close()
        except OSError:
            pass


def main():
    """Listen until Ctrl+C, and start one thread per accepted client."""
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("Usage: python one_to_one_server.py [port]")
            sys.exit(1)
    else:
        port = DEFAULT_PORT

    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Lets the server restart right away without "address already in use".
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server_sock.bind((HOST, port))
    except OSError as exc:
        print(f"Could not bind to port {port}: {exc}")
        sys.exit(1)
    server_sock.listen()
    # Wakes accept() once a second so Ctrl+C is noticed on Windows.
    server_sock.settimeout(1.0)

    print(f"One-to-one server listening on port {port}")
    print(f"  Same computer: connect to 127.0.0.1:{port}")
    print(f"  Same network:  connect to {get_lan_ip()}:{port}")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            try:
                client_sock, client_addr = server_sock.accept()
            except socket.timeout:
                continue
            client_sock.settimeout(None)
            # Username registration runs in the thread. Doing it here
            # would block every other client until this one typed a name.
            threading.Thread(
                target=handle_client,
                args=(client_sock, client_addr),
                daemon=True,
            ).start()
    except KeyboardInterrupt:
        print("\nShutting down server...")
    finally:
        with clients_lock:
            open_sockets = list(clients.values())
            clients.clear()
        for sock in open_sockets:
            try:
                sock.close()
            except OSError:
                pass
        server_sock.close()


if __name__ == "__main__":
    main()

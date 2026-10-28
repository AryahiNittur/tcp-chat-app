# TCP Chat App

CSE 3461 final project using Python TCP sockets and threading.
Includes broadcast messaging, private messaging, and a latency experiment.

Requires Python 3. No extra packages are needed. Run commands from
the main project folder.

## Broadcast chat

Start the server:

```bash
python3 server.py
```

Run a client in two or more separate terminals:

```bash
python3 client.py
```

Messages are forwarded through the server to all other clients.

## Private messaging

Stop the broadcast server first since both servers use port 12345.

```bash
python3 one_to_one_server.py
```

In separate terminals:

```bash
python3 one_to_one_client.py
```

Choose different usernames, then send a private message:

```text
@bob Hello Bob
```

Only the named recipient receives it. Type `/quit` to exit either
chat client. Use Ctrl+C to stop a server.

## Testing across computers

Start the appropriate server and use its printed LAN IP on the
other computers:

```bash
python3 client.py SERVER_IP 12345
```

Or for private messaging:

```bash
python3 one_to_one_client.py SERVER_IP 12345
```

All computers must be on the same network with connections to the
server's port allowed.

## Latency experiment

Feature 3 adds a delay before the broadcast server forwards messages.
The test measures delivery time from one client through the server
to another client.

Run the server and test in separate terminals:

| Delay | Server | Test |
|---|---|---|
| 0 ms | `python3 server.py 12345 0` | `python3 latency_analysis/broadcast_latency_test.py 0` |
| 100 ms | `python3 server.py 12345 100` | `python3 latency_analysis/broadcast_latency_test.py 100` |
| 300 ms | `python3 server.py 12345 300` | `python3 latency_analysis/broadcast_latency_test.py 300` |

Restart the server between settings. The test argument labels the
results and must match the server's delay.

Each run measures 10 messages and saves a CSV in `latency_analysis`.
Repeating a setting overwrites its results.

### Local results

| Added delay | Average delivery latency |
|---|---:|
| 0 ms | 0.09 ms |
| 100 ms | 104.75 ms |
| 300 ms | 305.12 ms |

The results show how added delay affects chat responsiveness.
These are delivery latency measurements, not RTT.

The original `latency_server.py` and `latency_client.py` files are
our standalone RTT prototype. The broadcast test is the final
integrated experiment.

## AI use

We used ChatGPT to help design and implement Feature 3 and interpret
the results. We tested the code locally and checked the CSV output.
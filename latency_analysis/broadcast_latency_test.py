import csv
import socket
import sys
import time
import uuid
from pathlib import Path

HOST = "127.0.0.1"
PORT = 12345
TRIALS = 10

# This labels the results. Set the same delay when starting server.py
delay_ms = int(sys.argv[1]) if len(sys.argv) > 1 else 0


def wait_for_message(stream, expected):
    """Skip join notices and other messages until our message arrives"""
    while True:
        line = stream.readline()

        if not line:
            raise ConnectionError("The server disconnected.")

        # Server messages have the format: [ip:port] message
        _, separator, text = line.rstrip("\n").partition("] ")

        if separator and text == expected:
            return


results = []
run_id = uuid.uuid4().hex

# Both clients run in this process so they share the same timer
with socket.create_connection((HOST, PORT), timeout=5) as sender:
    with socket.create_connection((HOST, PORT), timeout=5) as receiver:
        with sender.makefile("r", encoding="utf-8") as sender_messages:
            with receiver.makefile("r", encoding="utf-8") as receiver_messages:

                # Confirm both clients are registered before testing
                ready_message = f"READY_{run_id}"
                receiver.sendall((ready_message + "\n").encode())
                wait_for_message(sender_messages, ready_message)

                print(f"Testing broadcast delivery with {delay_ms} ms delay")

                for trial in range(1, TRIALS + 1):
                    message = f"LATENCY_{run_id}_{trial}"

                    start_time = time.perf_counter()
                    sender.sendall((message + "\n").encode())

                    wait_for_message(receiver_messages, message)
                    delivery_ms = (time.perf_counter() - start_time) * 1000

                    results.append([delay_ms, trial, delivery_ms])
                    print(f"Trial {trial}: {delivery_ms:.2f} ms")

measurements = [row[2] for row in results]
average = sum(measurements) / len(measurements)

print(
    f"\nAdded delay: {delay_ms} ms | "
    f"Average: {average:.2f} ms | "
    f"Min: {min(measurements):.2f} ms | "
    f"Max: {max(measurements):.2f} ms"
)

output_path = (
    Path(__file__).parent / f"broadcast_results_{delay_ms}ms.csv"
)

with output_path.open("w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["configured_delay_ms", "trial", "delivery_latency_ms"])
    writer.writerows(results)

print(f"Saved results to {output_path}")
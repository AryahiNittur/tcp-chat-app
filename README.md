# Feature 3: Latency Analysis

This part of the project tests how adding a delay at the server affects
round-trip time (RTT). It uses Python's built-in libraries.

## How to run

Run these commands from the main project folder.

Start the server in one terminal:

```bash
python3 latency_analysis/latency_server.py
```

Then run the client in another terminal:

```bash
python3 latency_analysis/latency_client.py
```

Both programs run on localhost using port 5003.

## How it works

The client sends a message like `PING 1 100`, which asks the server
to wait 100 ms before replying with `PONG 1`. Each message ends
with a newline so we can tell where it ends.

The client tests delays of 0, 100, and 300 ms, with 10 trials for
each setting. It measures the time from sending the message to
receiving the reply. This does not include connection setup.

The average, minimum, and maximum RTT are printed in the terminal.
Individual measurements are saved to `latency_results.csv` in this
folder. Running the client again overwrites the previous results.

## Results

Adding more delay increased the RTT, as expected. The measured time
was slightly higher than the requested delay because it also includes
processing, local communication, and scheduling overhead.

The delay is added in the server code to simulate slower communication.

## Still to do

This currently runs as a separate experiment and handles one client
at a time. We still need to integrate it into the chat application's
message forwarding when Features 1 and 2 are ready.

## AI use

I used ChatGPT to help plan the experiment, build and understand the
code step by step, and explain the results. I ran the tests locally
and checked that the server replies, RTT measurements, and CSV
export worked.
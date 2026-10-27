# Python HTTP Server from Scratch

A minimal, educational HTTP/1.1 server built entirely from scratch using Python's built-in `socket` module—no external frameworks (no Flask, FastAPI, or `http.server`). 

This project demonstrates how HTTP operates at the network level as structured text transmitted over raw TCP byte streams.

---

## Features

- **Pure Sockets**: Uses only Python's standard `socket` module.
- **TCP Stream Handling**: Listens on `127.0.0.1:8080`, handles the TCP handshake, reads raw bytes, and tears down connections cleanly.
- **HTTP Request Parsing**: Parses the HTTP request line to extract the method, path, and version (`GET /hello HTTP/1.1`).
- **HTTP Response Construction**: Manually builds valid HTTP/1.1 responses with status lines, headers (`Content-Type`, `Content-Length`, `Connection: close`), and bodies.
- **Route Handling**:
  - `GET /` — Returns a welcome message.
  - `GET /hello` — Returns a greeting message.
  - Any unknown path — Returns `404 Not Found`.
- **Live Terminal Logging**: Displays raw incoming HTTP requests and parsed details in real time.

---

## Project Structure

```text
.
├── server.py             # The core socket HTTP server implementation
├── HTTP_SERVER_GUIDE.md  # In-depth guide: internals & interview Q&As
└── README.md             # Project documentation
```

---

## Getting Started

### Prerequisites

Python 3.8+ (no `pip install` required).

### 1. Run the Server

```bash
python3 server.py
```

You should see:
```text
HTTP Server listening on http://127.0.0.1:8080
Waiting for incoming connections... (Press Ctrl+C to stop)
=======================================================
```

---

## Testing Endpoints with `curl`

In another terminal, test the endpoints using `curl -i` (the `-i` flag includes HTTP response headers):

### 1. Root Endpoint (`GET /`)
```bash
curl -i http://127.0.0.1:8080/
```
**Response:**
```http
HTTP/1.1 200 OK
Content-Type: text/plain; charset=utf-8
Content-Length: 43
Connection: close

Welcome to our custom Python HTTP server!
```

### 2. Hello Endpoint (`GET /hello`)
```bash
curl -i http://127.0.0.1:8080/hello
```
**Response:**
```http
HTTP/1.1 200 OK
Content-Type: text/plain; charset=utf-8
Content-Length: 51
Connection: close

Hello, world! HTTP is just text over a TCP stream.
```

### 3. Unknown Path (`404 Not Found`)
```bash
curl -i http://127.0.0.1:8080/unknown
```
**Response:**
```http
HTTP/1.1 404 Not Found
Content-Type: text/plain; charset=utf-8
Content-Length: 55
Connection: close

404 Not Found: Path '/unknown' not found on this server.
```

---

## Detailed Guide & Interview Preparation

For an in-depth breakdown of socket programming concepts, network layers, the TCP `TIME_WAIT` state, `Content-Length` byte mechanics, and **top technical interview questions**, check out:

👉 **[HTTP_SERVER_GUIDE.md](HTTP_SERVER_GUIDE.md)**
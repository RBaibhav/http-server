# Complete Guide: Building an HTTP Server from Scratch & Technical Interview Preparation

---

## 1. What is HTTP at the Network Level?

HTTP (Hypertext Transfer Protocol) is an **Application Layer (Layer 7)** protocol that sits directly on top of TCP (Transmission Control Protocol), which operates at the **Transport Layer (Layer 4)**.

```
+-------------------------------------------------------+
|  Application Layer (Layer 7)                          |
|  HTTP / HTTPS / WebSockets / DNS / FTP                |
|  -> Formats and semantic meaning of data (Plain text) |
+-------------------------------------------------------+
                           |
+-------------------------------------------------------+
|  Transport Layer (Layer 4)                            |
|  TCP / UDP                                            |
|  -> Reliable stream delivery, packet ordering, ports  |
+-------------------------------------------------------+
                           |
+-------------------------------------------------------+
|  Network Layer (Layer 3)                              |
|  IP (IPv4 / IPv6)                                     |
|  -> Addressing and routing across the internet        |
+-------------------------------------------------------+
                           |
+-------------------------------------------------------+
|  Data Link & Physical Layer (Layers 1 & 2)            |
|  Ethernet, Wi-Fi, Fiber optics, Physical wires        |
+-------------------------------------------------------+
```

### The Key Takeaway
**HTTP does not know about network cables, IP addresses, or packet loss.**  
TCP abstracts the chaotic network into a **reliable, in-order stream of raw bytes**. HTTP simply defines the grammar rules for how those bytes must be formatted so that clients and servers understand each other.

---

## 2. Anatomy of the HTTP Protocol

### 2.1 The Request Structure

Every HTTP request sent over a TCP connection consists of three distinct parts:

```http
GET /hello HTTP/1.1\r\n                <--- 1. Request Line
Host: 127.0.0.1:8080\r\n              <--- 2. Headers (Key: Value)
User-Agent: curl/7.88.1\r\n
Accept: */*\r\n
\r\n                                  <--- 3. Blank Line (CRLF delimiter)
[Optional Request Body Bytes]          <--- 4. Body (e.g. POST JSON data)
```

1. **Request Line**:
   - `METHOD`: Action to perform (`GET`, `POST`, `PUT`, `DELETE`, etc.).
   - `PATH`: Target resource (`/`, `/hello`, `/api/users?id=1`).
   - `VERSION`: Protocol version (`HTTP/1.0`, `HTTP/1.1`, `HTTP/2`).
2. **Headers**: Metadata (encoding, host, authentication, cookies, content types).
3. **CRLF (`\r\n\r\n`) Boundary**: The critical delimiter separating metadata from data.
4. **Body**: Payload bytes (absent in standard `GET` requests, present in `POST`/`PUT`).

### 2.2 The Response Structure

```http
HTTP/1.1 200 OK\r\n                   <--- 1. Status Line
Content-Type: text/plain\r\n          <--- 2. Headers
Content-Length: 51\r\n
Connection: close\r\n
\r\n                                  <--- 3. Blank Line (CRLF delimiter)
Hello, world! HTTP is just text...    <--- 4. Response Body
```

1. **Status Line**:
   - `VERSION`: Protocol version (`HTTP/1.1`).
   - `STATUS CODE`: 3-digit numerical result (`200`, `404`, `500`).
   - `REASON PHRASE`: Human-readable status description (`OK`, `Not Found`).
2. **Headers**: Details describing the body and connection behavior.
3. **CRLF (`\r\n\r\n`) Boundary**: Signals end of response headers.
4. **Body**: The actual response content.

---

## 3. Deep Dive: Code Breakdown & Internal Mechanics

### 3.1 What is a Socket?
In Unix-like systems, **"everything is a file."** A socket is an abstraction provided by the Operating System kernel that represents an endpoint for network communication. To the application code, reading and writing to a socket looks almost identical to reading and writing to an open file on disk.

```python
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
```
- **`AF_INET`**: Address Family for IPv4 (use `AF_INET6` for IPv6).
- **`SOCK_STREAM`**: Socket type for TCP (continuous byte stream). For UDP, you would use `SOCK_DGRAM`.

---

### 3.2 The `SO_REUSEADDR` Flag and the `TIME_WAIT` State
```python
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
```
#### Why is this necessary?
When a TCP connection closes, the side that initiated the active close enters a kernel state called **`TIME_WAIT`** for typically 1 to 2 minutes (2 × MSL — Maximum Segment Lifetime).
- During `TIME_WAIT`, the operating system prevents any other socket from binding to the same `(IP, Port)` tuple to ensure that lingering, delayed duplicate packets on the internet are not accidentally delivered to a new application.
- Without `SO_REUSEADDR`, restarting your Python server immediately after killing it raises:
  `OSError: [Errno 98] Address already in use`.
- Setting `SO_REUSEADDR = 1` tells the OS kernel to allow binding to the port even if existing connections are in `TIME_WAIT`.

---

### 3.3 `bind()` vs `listen()` vs `accept()`

```python
server_socket.bind(("127.0.0.1", 8080))
server_socket.listen(5)
client_socket, client_address = server_socket.accept()
```

These three steps follow a strict sequence:

1. **`bind(address)`**:
   - Binds the socket to a specific network interface IP and port number.
   - `127.0.0.1` binds exclusively to the loopback interface (local machine only).
   - `0.0.0.0` binds to all available network interfaces (accessible across LAN / Internet).
2. **`listen(backlog)`**:
   - Converts the active socket into a **passive socket** ready to receive connections.
   - The `backlog` argument (`5`) defines the size of the kernel queue for **unaccepted connections** (clients that have finished the TCP 3-way handshake but have not yet been picked up by `accept()`).
3. **`accept()`**:
   - A **blocking system call**. It pauses program execution until a client connects.
   - When a connection arrives, it returns a **new socket** (`client_socket`) and the client's address.
   - **Crucial Distinction**: `server_socket` continues listening on port 8080 for future clients. `client_socket` is dedicated solely to reading and writing data with this specific connected client.

---

### 3.4 Why `\r\n` (CRLF) instead of `\n`?
- **CR** = Carriage Return (`\r`, ASCII 13, returns cursor to column 0).
- **LF** = Line Feed (`\n`, ASCII 10, advances cursor to next line).
- Unix text files use `\n`, Windows files use `\r\n`.
- The official HTTP specification ([RFC 2616](https://datatracker.ietf.org/doc/html/rfc2616) & [RFC 7230](https://datatracker.ietf.org/doc/html/rfc7230)) strictly mandates **CRLF (`\r\n`)** as the end-of-line marker for all request lines and header fields.

---

### 3.5 Why Headers Matter

#### 1. `Content-Length` (The Stream Framing Problem)
- TCP is a stream of bytes without message boundaries. When receiving bytes from a socket, how does the client know when the HTTP body ends?
- **With `Content-Length: 51`**: The client reads headers until `\r\n\r\n`, parses the number `51`, reads exactly 51 bytes of body, and finishes.
- **The UTF-8 Trap**:
  ```python
  # WRONG: Character count
  content_length = len("Hello 🌍")  # Returns 7 characters

  # CORRECT: Byte count
  content_length = len("Hello 🌍".encode("utf-8"))  # Returns 10 bytes (🌍 takes 4 bytes!)
  ```
  If you use character length instead of byte length, multi-byte Unicode strings will truncate your response, corrupting data.

#### 2. `Content-Type`
- Instructs the browser or client parser how to render or deserialize the payload:
  - `text/plain`: Raw text without formatting.
  - `text/html`: Web page DOM tree.
  - `application/json`: JSON data structures.

#### 3. `Connection: close` vs `Connection: keep-alive`
- **`Connection: close`**: Instructs the client/server to tear down the TCP socket immediately after sending this single response.
- **`Connection: keep-alive`** (HTTP/1.1 default): Keeps the underlying TCP socket open so subsequent HTTP requests to the same host can reuse the existing connection, avoiding repeated 3-way TCP handshakes.

---

## 4. Architectural Limitations of this Basic Server

1. **Single-Threaded / Synchronous Blocking**:
   - Because `accept()` and `recv()` are blocking calls, if Client A connects and transmits data slowly, Client B is blocked in the backlog queue.
2. **Buffer Truncation**:
   - `client_socket.recv(1024)` reads at most 1,024 bytes. If a client sends large headers or a POST body > 1 KB, the remaining bytes remain stuck in the TCP buffer unread.
3. **No Keep-Alive / Persistent Connection Support**:
   - Every request requires a new TCP handshake and teardown, adding latency.

---

## 5. Top Interview Questions & Model Answers

### Category 1: Computer Networking & Sockets

#### Q1: What happens under the hood when a browser visits `http://127.0.0.1:8080/hello`?
**Answer:**
1. **URL Parsing**: Browser extracts protocol (`http`), host (`127.0.0.1`), port (`8080`), and path (`/hello`).
2. **DNS Resolution**: Since `127.0.0.1` is an IP literal, DNS lookup is skipped (otherwise it queries OS resolver/DNS cache).
3. **TCP 3-Way Handshake**:
   - Client sends `SYN` (Synchronize sequence number).
   - Server returns `SYN-ACK`.
   - Client returns `ACK` (Connection established).
4. **HTTP Request Transmission**: Browser formats and sends raw HTTP text (`GET /hello HTTP/1.1\r\nHost: ...\r\n\r\n`) through the TCP socket.
5. **Server Processing**: Server OS places connection in the socket backlog; Python's `accept()` returns the client socket; `recv()` reads the bytes; router matches `/hello`.
6. **HTTP Response Transmission**: Server writes response bytes (`HTTP/1.1 200 OK...`) via `sendall()`.
7. **TCP Teardown (4-Way Handshake)**: Connection closes with `FIN`/`ACK` exchange.
8. **Rendering**: Browser parses response status, headers, and renders body text.

---

#### Q2: What is the purpose of `server_socket.listen(backlog)` and what does `backlog` do?
**Answer:**
`listen()` transitions a socket from an active connecting socket to a passive listening socket.
The `backlog` argument specifies the maximum number of established, fully handshook TCP connections that the OS kernel can queue in memory waiting for the application to invoke `accept()`. If the queue is full and new clients attempt to connect, the OS will reject or drop incoming `SYN` packets (clients receive `Connection Refused` or timeout).

---

#### Q3: What is the difference between `server_socket` and `client_socket` in `accept()`?
**Answer:**
- `server_socket` is the **listening socket**. It stays bound to `127.0.0.1:8080` for the entire lifetime of the server process. It never transmits application data; its sole job is to accept new connection requests.
- `client_socket` is a **data-transfer socket** instantiated dynamically by the OS kernel for each newly accepted client. It is uniquely bound to the 4-tuple:
  `(Local IP, Local Port, Remote IP, Remote Port)`. Data exchange occurs exclusively over this socket.

---

#### Q4: What is the TCP `TIME_WAIT` state, and why is `SO_REUSEADDR` important?
**Answer:**
The `TIME_WAIT` state occurs on whichever side of a TCP connection sends the first `FIN` packet to initiate a clean disconnect. It persists for 2 × MSL (Maximum Segment Lifetime, typically 30-120 seconds).
Its purposes are:
1. To ensure the final `ACK` is reliably received by the peer (if lost, the peer retransmits `FIN`, which can only be handled properly in `TIME_WAIT`).
2. To allow lingering packets belonging to this connection to expire in network transit rather than corrupting a subsequent connection that reuses the same port.
`SO_REUSEADDR` allows a server process to bind immediately to a local address/port even if previous sockets on that port are currently in the `TIME_WAIT` state.

---

### Category 2: HTTP Protocol Fundamentals

#### Q5: Why is HTTP called a "stateless" protocol? How do modern apps maintain state?
**Answer:**
HTTP is stateless because each request-response transaction is completely independent. The server retains no memory of previous requests from the same client by default.
Modern web applications simulate state using Application-Layer mechanisms:
- **Cookies & Session IDs**: The server sends a `Set-Cookie: session_id=xyz` header; the client includes `Cookie: session_id=xyz` in subsequent requests.
- **Tokens (e.g., JWT)**: Stateless cryptographically signed tokens included in the `Authorization: Bearer <token>` header.

---

#### Q6: What is the difference between HTTP/1.0, HTTP/1.1, HTTP/2, and HTTP/3?
**Answer:**
- **HTTP/1.0**: Closes TCP connection after every single request-response cycle (1 request = 1 TCP handshake).
- **HTTP/1.1**: Introduced persistent connections (`Connection: keep-alive` by default), pipelining, chunked transfer encoding, and mandatory `Host` header. Still suffers from **Head-of-Line (HoL) Blocking** at the HTTP level (requests over a single connection must be responded to sequentially).
- **HTTP/2**: Binary framing instead of plain text, **multiplexing** (multiple parallel streams over a single TCP connection), header compression (HPACK), and server push. Solves HTTP HoL blocking, but still suffers from TCP HoL blocking (packet loss stalls all streams).
- **HTTP/3**: Replaces TCP with **QUIC** (built on top of UDP). Eliminates TCP Head-of-Line blocking entirely, provides built-in TLS 1.3 encryption, and allows faster zero-RTT handshakes.

---

#### Q7: What are Safe and Idempotent HTTP methods?
**Answer:**
- **Safe Methods**: Do not modify server state (read-only).
  - Examples: `GET`, `HEAD`, `OPTIONS`.
- **Idempotent Methods**: Making multiple identical requests produces the exact same server state as making a single request:
  - `GET`: Safe and idempotent.
  - `PUT`: Idempotent (replacing a resource 1 time or 10 times results in the same resource state).
  - `DELETE`: Idempotent (deleting resource ID 5 multiple times leaves resource 5 deleted).
  - `POST`: **NOT** idempotent (submitting a form twice creates two separate records).
  - `PATCH`: Generally **NOT** guaranteed to be idempotent (e.g., `PATCH /cart` with `{ "add": 1 }`).

---

#### Q8: What happens if `Content-Length` is missing in an HTTP response?
**Answer:**
- In **HTTP/1.0** or with `Connection: close`: If `Content-Length` is absent, the client continues reading bytes until the server closes the TCP socket (`EOF`). Socket closure signals the end of the body.
- In **HTTP/1.1 with persistent connections (`keep-alive`)**: The client cannot determine when the body ends without `Content-Length` or `Transfer-Encoding: chunked`. The client will hang indefinitely waiting for bytes until an I/O timeout triggers.

---

### Category 3: Scalability & Concurrency (Systems Design)

#### Q9: Our `server.py` processes one request at a time. How would you scale it to handle 10,000 concurrent clients?
**Answer:**
1. **Thread-per-connection (`threading`)**:
   - Spawn a worker thread per `client_socket`.
   - *Limitation*: High memory consumption per thread stack; context-switching overhead degrades performance past ~1,000–5,000 threads.
2. **Process Pool (`multiprocessing`)**:
   - Worker processes share the listening socket.
   - Bypasses Python's Global Interpreter Lock (GIL) and utilizes multi-core CPUs.
3. **I/O Multiplexing (Event Loop / `epoll` / `select` / `asyncio`)**:
   - The production standard (used by Nginx, Node.js, and Python's `asyncio`).
   - Uses OS notification facilities (`epoll` on Linux, `kqueue` on macOS) to monitor thousands of file descriptors in a single thread without blocking. When a socket has bytes ready to read, the event loop triggers a callback.

---

#### Q10: What is the "Slowloris" attack and is our basic server vulnerable to it?
**Answer:**
Yes, our basic server is completely vulnerable.
**How it works**: An attacker opens a connection and sends headers extremely slowly (e.g., one header byte every 10 seconds, never sending the final `\r\n\r\n`).
Because `recv(1024)` blocks waiting for incoming bytes on a single thread, the entire server process freezes waiting for the attacker, starving all legitimate users.
**Mitigation**:
- Non-blocking asynchronous I/O.
- Strict read timeouts on connection headers (e.g., abort if headers take > 5 seconds).
- Limiting the maximum number of connections per IP address.

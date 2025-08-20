# Basic Python HTTP Server

This is a minimal HTTP server built using Python's built-in `socket` library.  
It listens for incoming requests on port **8080** and serves static files (`index.html` and `book.json`) for `GET` requests.

---

## Features
- Handles **basic HTTP GET requests**.
- Serves:
  - `index.html` at `/`
  - `book.json` at `/book`
- Responds with `405 Method Not Allowed` for unsupported methods.

---

## How It Works
1. The server binds to `0.0.0.0:8080` and starts listening.
2. When a client connects:
   - The request is parsed.
   - If the method is `GET` and the path is valid, the corresponding file is returned.
   - Otherwise, a `405 Method Not Allowed` response is sent.

---

## Usage

### Run the server
```bash
python3 server.py
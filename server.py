import socket

# Server configuration
HOST = "127.0.0.1"
PORT = 8080


def create_response(status_code: int, status_text: str, body: str) -> bytes:
    """Construct an HTTP/1.1 response string with headers and encoded body."""
    body_bytes = body.encode("utf-8")
    content_length = len(body_bytes)

    # HTTP responses require CRLF (\r\n) line endings
    status_line = f"HTTP/1.1 {status_code} {status_text}\r\n"
    headers = (
        f"Content-Type: text/plain; charset=utf-8\r\n"
        f"Content-Length: {content_length}\r\n"
        f"Connection: close\r\n"
        f"\r\n"
    )

    return (status_line + headers).encode("utf-8") + body_bytes


def main():
    # 1. Create a TCP socket: AF_INET = IPv4, SOCK_STREAM = TCP
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # 2. Allow immediate reuse of the port when restarting the server
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # 3. Bind the socket to the host and port
    server_socket.bind((HOST, PORT))

    # 4. Listen for incoming client connections (queue size 5)
    server_socket.listen(5)
    print(f"HTTP Server listening on http://{HOST}:{PORT}", flush=True)
    print("Waiting for incoming connections... (Press Ctrl+C to stop)\n" + "=" * 55, flush=True)

    try:
        while True:
            # 5. Accept connection from a client (blocking call)
            client_socket, client_address = server_socket.accept()
            print(f"\n[+] Accepted connection from {client_address[0]}:{client_address[1]}", flush=True)

            # 6. Read raw request bytes and decode to text
            raw_request = client_socket.recv(1024).decode("utf-8", errors="replace")

            # Handle edge case: empty request (client closed connection before sending data)
            if not raw_request:
                client_socket.close()
                continue

            # 7. Print raw HTTP request
            print("--- RAW HTTP REQUEST ---", flush=True)
            print(raw_request, flush=True)
            print("------------------------", flush=True)

            # 8. Parse the request line (the first line: METHOD PATH VERSION)
            request_lines = raw_request.split("\r\n")
            request_line = request_lines[0]
            parts = request_line.split()

            if len(parts) >= 3:
                method, path, version = parts[0], parts[1], parts[2]
            else:
                method, path, version = "UNKNOWN", "", "HTTP/1.1"

            print(f"[Parsed] Method: {method} | Path: {path} | Version: {version}", flush=True)

            # 9. Route matching and response generation
            if method == "GET" and path == "/":
                response = create_response(200, "OK", "Welcome to our custom Python HTTP server!\n")
            elif method == "GET" and path == "/hello":
                response = create_response(200, "OK", "Hello, world! HTTP is just text over a TCP stream.\n")
            else:
                response = create_response(404, "Not Found", f"404 Not Found: Path '{path}' not found on this server.\n")

            # 10. Send the raw response bytes back across the TCP socket
            client_socket.sendall(response)

            # 11. Cleanly close the client socket
            client_socket.close()
            print(f"[-] Closed connection with {client_address[0]}:{client_address[1]}", flush=True)

    except KeyboardInterrupt:
        print("\nShutting down server...", flush=True)
    finally:
        server_socket.close()


if __name__ == "__main__":
    main()

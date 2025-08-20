import socket 
import time 

SERVER_PORT = 8080
SERVER_HOST = "0.0.0.0" 

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_socket.bind((SERVER_HOST, SERVER_PORT))

server_socket.listen(5)

print(f"Listening on port {SERVER_PORT} ...")

while True:
  client_socket, client_adress = server_socket.accept()
  request = client_socket.recv(1500).decode()
  print(request);
  headers = request.split('\n')
  first_header_componets = headers[0].split()
  
  http_method = first_header_componets[0]
  http_path = first_header_componets[1]

  if http_method == 'GET' :
    if http_path == '/':
      file_input = open('index.html') 
    elif http_path == '/book':
      file_input = open("book.json");
    
    content = file_input.read() # type: ignore
    file_input.close() # type: ignore
    
    response = "  HTTP/1.1 200 OK\n\n" + content
    
    
    
  else:
    response = '  HTTP/1.1 405 Method Not Allowed\n\nAllow: GET'

  client_socket.sendall(response.encode())
  client_socket.close();

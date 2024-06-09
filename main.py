import datetime
import mimetypes
import json
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import socket
from threading import Thread

BASE_DIR = Path()
BUFFER_SIZE = 1024
HTTP_HOST = SOCKET_HOST = '127.0.0.1'
SOCKET_PORT = 5000
HTTP_PORT = 3000


class HttpHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        
        # Create a UDP socket
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.sendto(data, (HTTP_HOST, SOCKET_PORT))

        # Close the connection
        client_socket.close()

        self.send_response(302)
        self.send_header('Location', '/message')
        self.end_headers()

    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        match pr_url.path:
            case '/':
                self.send_html_file('index.html')
            case '/message':
                self.send_html_file('message.html')
            case _:
                if BASE_DIR.joinpath(pr_url.path[1:]).exists():
                    self.send_static()
                else:
                    self.send_html_file('error.html', 404)

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())


def save_data_from_form(data):
        timer = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data_parse = urllib.parse.unquote_plus(data.decode())
        data_dict = {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}
        data_dict_json = {timer: data_dict}
        with open('storage/data.json', 'a', encoding='utf-8') as file:
            json.dump(data_dict_json, file, ensure_ascii=False, indent=4)

def run_socket_server(host=SOCKET_HOST, port=SOCKET_PORT):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((host, port))
    print(f"Socket server listening on {host}:{port}")

    try:
        while True:
            msg, address = server_socket.recvfrom(BUFFER_SIZE)
            save_data_from_form(msg)
    except KeyboardInterrupt:
        print("Server shutting down.")
        server_socket.close()

def run_http_server(host=HTTP_HOST, port=HTTP_PORT):
    server_address = (host, port)
    http = HTTPServer(server_address, HttpHandler)

    print(f"HTTP server starting on {host}:{port}")
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


if __name__ == '__main__':

    server = Thread(target=run_http_server, args=(HTTP_HOST, HTTP_PORT))
    server.start()

    server_socket = Thread(target=run_socket_server, args=(SOCKET_HOST, SOCKET_PORT))
    server_socket.start()



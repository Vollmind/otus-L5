import logging
import os
import socket
import threading
from datetime import datetime
from optparse import OptionParser
from urllib.parse import unquote
import concurrent.futures

INDEX_PAGE = 'index.html'
MIME_TYPES = {
    'html': 'text/html',
    'css': 'text/css',
    'js': 'application/javascript',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
    'gif': 'image/gif',
    'swf': 'application/x-shockwave-flash',
    'webp': 'image/webp',
    'txt': 'text/plain',
}


def fill_file_info(path, need_body):
    file_stat = os.stat(path)
    response_headers = {
        'Date': datetime.fromtimestamp(file_stat.st_mtime).strftime('%d.%m.%Y'),
        'Content-Length':  file_stat.st_size,
        'Content-Type': MIME_TYPES[path.split('.')[-1].lower()],
    }
    response_body = b''
    if need_body:
        with open(path, 'rb') as file:
            response_body = file.read()
    return response_headers, response_body


def check_folder_level(address):
    folder_counter = 0
    for i in address.split('/'):
        if i == '..':
            folder_counter -= 1
        else:
            folder_counter += 1
        if folder_counter < 0:
            raise PermissionError


def connection_handling(client_socket, base_folder):
    data = b""
    partlen = 1024
    while True:
        part = client_socket.recv(partlen)
        data += part
        if len(part) < partlen:
            break
    request = data.decode('UTF8').splitlines()
    method, address, http = request[0].split(' ')
    response_headers = {
        'Connection': 'keep-alive',
        'Server': 'Python socket'
    }
    response_status = 200
    response_mnem = 'OK'
    response_body = b''
    if method not in ['GET', 'HEAD']:
        response_status = 405
        response_mnem = 'METHOD NOT ALLOWED'
        response_headers['Allow'] = 'GET, HEAD'
    else:
        address = unquote(address)
        if '?' in address:
            address = address[:address.index('?')]
        if address[-1] == '/':
            address = address + INDEX_PAGE
        if base_folder:
            address = f'/{base_folder}{address}'
        address = f'.{address}'

        try:
            check_folder_level(address)
            file_head, file_body = fill_file_info(address, method != 'HEAD')
            response_headers.update(file_head)
            response_body = file_body
        except (FileNotFoundError, NotADirectoryError):
            response_status = 404
            response_mnem = 'NOT FOUND'
        except PermissionError:
            response_status = 403
            response_mnem = 'FORBIDDEN'
        except Exception as e:
            response_status = 500
            response_mnem = e

    # logging.info(f'{http} {response_status} {response_mnem}\r\n'.encode())
    client_socket.send(f'{http} {response_status} {response_mnem}\r\n'.encode())
    client_socket.send('\r\n'.join([f'{k}: {v}' for k, v in response_headers.items()]).encode())
    client_socket.send(b'\r\n\r\n')
    client_socket.send(response_body)
    client_socket.close()


if __name__ == "__main__":
    op = OptionParser()
    op.add_option("-p", "--port", action="store", type=int, default=8080)
    op.add_option("-w", "--workers", action="store", default=1)
    op.add_option("-r", "--root", action="store", default="")
    (opts, args) = op.parse_args()
    logging.basicConfig(filename=None, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    # Start server
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    server.bind(('', opts.port))
    # logging.info(f'Start server on port {opts.port}')
    server.listen(50000)
    with concurrent.futures.ThreadPoolExecutor(max_workers=int(opts.workers)) as executor:
        while True:
            client, addr = server.accept()
            executor.submit(connection_handling, client, opts.root)

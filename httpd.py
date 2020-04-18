import concurrent.futures
import logging
import mimetypes
import os
import socket
from datetime import datetime
from optparse import OptionParser
from urllib.parse import unquote

INDEX_PAGE = 'index.html'


def fill_file_info(path, need_body):
    file_stat = os.stat(path)
    response_headers = {
        'Date': datetime.fromtimestamp(file_stat.st_mtime).strftime('%d.%m.%Y'),
        'Content-Length':  file_stat.st_size,
        'Content-Type': mimetypes.guess_type(path)[0],
    }
    if response_headers['Content-Type'] is None:
        response_headers['Content-Type'] = 'application/octet-stream'
    response_body = b''
    if need_body:
        with open(path, 'rb') as file:
            response_body = file.read()
    return response_headers, response_body


def check_access(address):
    if address.startswith('..'):
        raise PermissionError


def read_http_request(client_socket):
    data = b''
    partlen = 1024
    while True:
        part = client_socket.recv(partlen)
        data += part
        if b'\r\n\r\n' in data:
            split = data.split(b'\r\n\r\n')
            body = split[1]
            request_splitted = split[0].decode().splitlines()
            request = request_splitted[0]
            request_headers = {y[0]: y[1] for y in [x.split(': ') for x in request_splitted[1:]]}
            break
        if not part:
            raise RuntimeError
    if 'Content-Length' in request_headers.keys():
        while len(body) < int(request_headers['Content-Length']):
            part = client_socket.recv(partlen)
            body += part
    return request, request_headers, body.decode()


def prepare_address(address, base_folder):
    address = unquote(address)
    if '?' in address:
        address = address[:address.index('?')]
    if address[-1] == '/':
        address = address + INDEX_PAGE
    if base_folder:
        address = f'/{base_folder}{address}'
    address = f'.{address}'
    address = os.path.normpath(address)
    return address


def create_http_response(http, code, mnemonic, headers={}, body=b''):
    # Add base headers
    headers.update({
        'Connection': 'keep-alive',
        'Server': 'Python socket'
    })
    response = f'{http} {code} {mnemonic}\r\n'
    response += '\r\n'.join([f'{k}: {v}' for k, v in headers.items()])
    response += '\r\n\r\n'
    return response.encode() + body


def connection_handling(client_socket, base_folder):
    http = 'HTTP/1.1'
    try:
        request, _, _ = read_http_request(client_socket)
        method, address, http = request.split(' ')
        if method not in ['GET', 'HEAD']:
            response = create_http_response(
                http,
                405,
                'METHOD NOT ALLOWED',
                {'Allow': 'GET, HEAD'}
            )
        else:
            address = prepare_address(address, base_folder)
            check_access(address)
            file_head, file_body = fill_file_info(address, method != 'HEAD')
            response = create_http_response(
                http,
                200,
                'OK',
                file_head,
                file_body
            )
    except (FileNotFoundError, NotADirectoryError):
        response = create_http_response(http, 404, 'NOT FOUND')
    except PermissionError:
        response = create_http_response(http, 403, 'FORBIDDEN')
    except RuntimeError:
        response = create_http_response(http, 400, 'BAD REQUEST')
    except Exception as e:
        response = create_http_response(http, 500, e)
    client_socket.send(response)
    client_socket.close()


if __name__ == "__main__":
    op = OptionParser()
    op.add_option("-p", "--port", action="store", type=int, default=8080)
    op.add_option("-w", "--workers", action="store", default=1)
    op.add_option("-r", "--root", action="store", default="")
    (opts, args) = op.parse_args()
    logging.basicConfig(filename=None, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    server.bind(('', opts.port))
    server.listen(50000)
    with concurrent.futures.ThreadPoolExecutor(max_workers=int(opts.workers)) as executor:
        while True:
            client, addr = server.accept()
            executor.submit(connection_handling, client, opts.root)

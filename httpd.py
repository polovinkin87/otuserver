# -*- coding: utf-8 -*-

import os
import sys
import socket
import logging
import logging.handlers
import argparse
import threading
import multiprocessing
import re
from typing import Tuple
from http_response import generate_response

CHUNK_SIZE = 8192
PROTOCOL = "HTTP/1.0"

OK = 200
BAD_REQUEST = 400
FORBIDDEN = 403
NOT_FOUND = 404
METHOD_NOT_ALLOWED = 405
INTERNAL_ERROR = 500
ERRORS = {
    OK: "OK",
    BAD_REQUEST: "Bad Request",
    FORBIDDEN: "Forbidden",
    NOT_FOUND: "Not Found",
    METHOD_NOT_ALLOWED: "Method Not Allowed",
    INTERNAL_ERROR: "Internal Server Error"
}

HEXDIG = '0123456789ABCDEFabcdef'
HEXTOBYTE = None


class HTTPRequestParser:
    methods = ["GET", "HEAD"]

    @classmethod
    def parse(cls, request, root_dir):
        try:
            method, url, *_ = request.split(" ")

            code = cls.validate_method(method)
            if code != OK:
                url = cls.get_error_file_path(code)
                return code, method, url

            code, url = cls.validate_url(url, root_dir)
            if code != OK:
                uri = cls.get_error_file_path(code)

            return code, method, url
        except ValueError:
            return INTERNAL_ERROR, "", ""

    @classmethod
    def validate_method(cls, method):
        if method not in cls.methods:
            return METHOD_NOT_ALLOWED
        return OK

    @classmethod
    def unquote_url(cls, url):
        global HEXTOBYTE
        if HEXTOBYTE is None:
            HEXTOBYTE = {
                ("%" + a + b).encode(): bytes([int(a + b, 16)])
                for a in HEXDIG for b in HEXDIG
            }

        url_encoded = url.encode()
        for match, sub in HEXTOBYTE.items():
            url_encoded = url_encoded.replace(match, sub)

        return url_encoded.decode(errors="replace")

    @classmethod
    def normalize_url(cls, url: str, root_dir: str):
        if "../" in url:
            return FORBIDDEN, url

        url_path = url.split("#")[0].split("?")[0]

        url_pattern = r"^\/[\/\.a-zA-Z0-9\-\_\%]+$"
        if not re.match(url_pattern, url_path):
            return BAD_REQUEST, url

        url_path = cls.unquote_url(url_path).lstrip("/")
        url_path = os.path.join(root_dir, url_path).replace("\\", "/")
        return OK, url_path

    @classmethod
    def validate_url(cls, url: str, root_dir: str):
        try:
            code, url_path = cls.normalize_url(url, root_dir)
            if code != OK:
                return code, url_path

            # Check if path is dir
            if os.path.isdir(url_path) and not url_path.endswith("/"):
                url_path += "/"

            if url_path.endswith("/"):
                url_path = os.path.join(url_path, "index.html")
                if not os.path.isfile(url_path):
                    return FORBIDDEN, url_path

            # Check if path exists
            if not os.path.isfile(url_path):
                return NOT_FOUND, url_path

            return OK, url_path
        except (TypeError, ValueError):
            return INTERNAL_ERROR, url

    @classmethod
    def get_error_file_path(cls, code: int):
        error_file_name = "{}.html".format(code)
        dir_path = os.path.dirname(os.path.abspath(__file__))
        dir_path = os.path.abspath(os.path.join(dir_path, "error_pages"))
        file_path = os.path.abspath(os.path.join(dir_path, error_file_name))
        return file_path


class HTTPServer:
    def __init__(self, host, port, doc_root, backlog=5, chunk_size=CHUNK_SIZE):
        self.host = host
        self.port = port
        self.root = doc_root
        self.backlog = backlog
        self.chunk_size = chunk_size

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self):
        try:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

            self.socket.bind((self.host, self.port))
        except (OSError, TypeError):
            logging.error("Server don't start", exc_info=True)
            self.shutdown()
            sys.exit(1)

        logging.info("Server started on {}:{}".format(self.host, self.port))
        self.socket.listen(self.backlog)

    def shutdown(self):
        try:
            self.socket.shutdown(socket.SHUT_RDWR)
            logging.info("Server's socket closed")
        except OSError:
            return

    def listen(self):
        try:
            while True:
                client_socket = None
                client_addr = ""
                try:
                    client_socket, client_addr = self.socket.accept()
                    logging.debug("Request from {}".format(client_addr))
                    client_handler = threading.Thread(
                        target=self.handle,
                        args=(client_socket, client_addr)
                    )
                    client_handler.start()
                except OSError:
                    logging.warning("Can't handle request from {}".format(
                        client_addr
                    ))
                    if client_socket:
                        client_socket.close()
        finally:
            self.shutdown()

    def handle(self, client_socket: socket.socket, client_addr: Tuple):
        try:
            request = self.receive(client_socket)
            if not request:
                logging.warning("Empty request from {}".format(client_addr))
                return
            logging.debug("Request from {}. Status_line: {}".format(
                client_addr, request.split("\n")[0]
            ))

            code, method, url = HTTPRequestParser.parse(request, self.root)
            if code != OK:
                url = "error_pages/{}.html".format(code)

            response = generate_response(code, method, url)
            client_socket.sendall(response)
            logging.debug("Send response to {}: {}, {}, {}".format(
                client_addr, code, method, url
            ))
        except ConnectionError:
            logging.exception("Can't send response to {}".format(client_addr))
        finally:
            client_socket.close()

    def receive(self, client_socket: socket.socket):
        result = ""
        try:
            while True:
                chunk = client_socket.recv(self.chunk_size)
                result += chunk.decode()
                if "\r\n\r\n" in result:
                    break
                if not chunk:
                    break
        except ConnectionError:
            logging.exception("Can't read response")

        return result


def parse_args():
    parser = argparse.ArgumentParser(description='HTTP server')

    parser.add_argument(
        '-hs', '--host', type=str, default="localhost",
        help='listened host, default - localhost'
    )
    parser.add_argument(
        '-p', '--port', type=int, default=8080,
        help='listened port, default - 8080'
    )
    parser.add_argument(
        '-w', '--workers', type=int, default=5,
        help='server workers count, default - 5'
    )
    parser.add_argument(
        '-r', '--root', type=str, default='',
        help='DIRECTORY_ROOT with site files, default - ""'
    )

    return parser.parse_args()


if __name__ == '__main__':
    logging.basicConfig(filename='http.log', level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s',
                        datefmt='%Y.%m.%d %H:%M:%S')
    args = parse_args()
    server = HTTPServer(host=args.host, port=args.port, doc_root=args.root)
    server.start()

    workers = []
    try:
        for i in range(args.workers):
            worker = multiprocessing.Process(target=server.listen)
            workers.append(worker)
            worker.start()
            logging.info("{} worker started".format(i + 1))
        for worker in workers:
            worker.join()
    except KeyboardInterrupt:
        for worker in workers:
            if worker:
                worker.terminate()
    finally:
        logging.info("Server shutdown")
        server.shutdown()

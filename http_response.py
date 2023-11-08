# -*- coding: utf-8 -*-

import os
import mimetypes
from datetime import datetime
from collections import OrderedDict
from typing import Union

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


def generate_response(code, method, url):
    response = "{status_line}\r\n{headers}\r\n\r\n".format(
        status_line=generate_start_line(code),
        headers=generate_headers(url)
    )
    response = response.encode(encoding="UTF-8")

    body = generate_body(code, method, url)
    if body:
        response += body

    return response


def generate_start_line(code):
    return "{proto} {code} {msg}".format(
        proto=PROTOCOL,
        code=code,
        msg=ERRORS[code]
    )


def generate_headers(url):
    headers = OrderedDict({
        "Date": get_date(),
        "Server": "HTTP server",
        "Content-Length": get_file_size(url),
        "Content-Type": mimetypes.guess_type(url)[0],
        "Connection": "close"
    })
    headers = "\r\n".join("{}: {}".format(k, v) for k, v in headers.items())
    return headers


def generate_body(code, method, url):
    if code == OK and method != "GET":
        return None

    with open(url, "rb") as file:
        body = file.read()

    return body


def get_date():
    now = datetime.utcnow()
    weekday = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][now.weekday()]
    month = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep",
             "Oct", "Nov", "Dec"][now.month - 1]
    rfc_fmt_dt = "%s, %02d %s %04d %02d:%02d:%02d GMT" % (
        weekday, now.day, month, now.year, now.hour, now.minute, now.second
    )
    return rfc_fmt_dt


def get_file_size(url):
    return os.path.getsize(url)

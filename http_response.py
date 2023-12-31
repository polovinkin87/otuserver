# -*- coding: utf-8 -*-

import os
import mimetypes
from datetime import datetime
from collections import OrderedDict
from typing import Union
from config import *


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

    try:
        with open(url, "rb") as file:
            body = file.read()
    except FileNotFoundError:
        return None
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
    try:
        return os.path.getsize(url)
    except FileNotFoundError:
        return None

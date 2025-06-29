# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from mo_dots import (
    Data,
    Null,
    coalesce,
    is_data,
    is_list,
    to_data,
    is_many,
    unwraplist,
    is_null,
)
from mo_future import is_text, text, unichr, urlparse, is_binary
from mo_logs import Log


class URL:
    """
    JUST LIKE urllib.parse() [1], BUT CAN HANDLE JSON query PARAMETERS

    [1] https://docs.python.org/3/library/urllib.parse.html
    """

    def __new__(cls, value, *args, **kwargs):
        if isinstance(value, URL):
            return value
        else:
            return object.__new__(cls)

    def __init__(self, value, port=None, path=None, query=None, fragment=None):
        if isinstance(value, URL):
            return
        try:
            self.scheme = None
            self.host = None
            self.port = port
            self.path = path
            self.query = query
            self.fragment = fragment

            if value == None:
                return

            if value.startswith("file://") or value.startswith("//"):
                # urlparse DOES NOT WORK IN THESE CASES
                scheme, suffix = value.split("//", 1)
                self.scheme = scheme.rstrip(":")
                parse(self, suffix, 0, 1)
                self.query = to_data(url_param2value(self.query))
            else:
                output = urlparse(value)
                self.scheme = output.scheme
                self.port = coalesce(port, output.port)
                self.host = output.netloc.split(":")[0]
                self.path = coalesce(path, output.path)
                self.query = coalesce(query, to_data(url_param2value(output.query)))
                self.fragment = coalesce(fragment, output.fragment)
        except Exception as e:
            Log.error("problem parsing {value} to URL", value=value, cause=e)

    def __nonzero__(self):
        if self.scheme or self.host or self.port or self.path or self.query or self.fragment:
            return True
        return False

    def __bool__(self):
        if self.scheme or self.host or self.port or self.path or self.query or self.fragment:
            return True
        return False

    def __truediv__(self, other):
        if self.scheme == "file" and not self.path:
            # keep relative path
            path = str(other).lstrip("/")
        else:
            path = f"{self.path.rstrip('/')}/{str(other).lstrip('/')}"

        parts = []
        for step in path.split("/"):
            if step == ".":  # IGNORE
                pass
            elif step == ".." and parts and (len(parts) > 1 or parts[0]):  # BACK UP
                parts.pop()
            else:
                parts.append(step)
        path = "/".join(parts)

        output = self.__copy__()
        output.path = path
        return output

    def set_scheme(self, new_scheme):
        output = self.__copy__()
        output.scheme = new_scheme
        return output

    def set_host(self, new_host):
        output = self.__copy__()
        output.host = new_host
        return output

    def set_port(self, new_port):
        output = self.__copy__()
        output.port = new_port
        return output

    def set_path(self, new_path):
        output = self.__copy__()
        output.path = new_path
        return output

    def set_query(self, new_query):
        if not is_data(new_query):
            Log.error("can only set query to data")
        output = self.__copy__()
        output.query = to_data(new_query)
        return output

    def set_fragment(self, new_fragment):
        if not is_data(new_fragment):
            Log.error("can only set fragment to data")
        output = self.__copy__()
        output.fragment = to_data(new_fragment)
        return output

    def __add__(self, other):
        if not is_data(other):
            Log.error("can only add data for query parameters")
        output = self.__copy__()
        output.query += other
        return output

    def __copy__(self):
        output = URL(None)
        output.scheme = self.scheme
        output.host = self.host
        output.port = self.port
        output.path = self.path
        output.query = Data(**self.query)
        output.fragment = self.fragment
        return output

    def decode(self, encoding=""):
        return str(self).decode(encoding)

    def __data__(self):
        return str(self)

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        return str(self) == str(other)

    def __str__(self):
        url = ""
        if self.host:
            url = self.host
        if self.scheme:
            url = self.scheme + "://" + url
        if self.port:
            url = url + ":" + str(self.port)
        if self.path:
            path = str(self.path)
            if self.host and path[0] != "/":
                url += "/" + path
            else:
                url += path
        if len(self.query):
            url = url + "?" + value2url_param(self.query)
        if self.fragment:
            url = url + "#" + value2url_param(self.fragment)
        return url


def int2hex(value, size):
    return (("0" * size) + hex(value)[2:])[-size:]


def hex2chr(hex):
    try:
        return unichr(int(hex, 16))
    except Exception as e:
        raise e


_map2url = {i: unichr(i) for i in range(32, 128)}
for c in b"{}<>;/?@&=+$%,+":
    _map2url[c] = "%" + int2hex(c, 2)
for i in range(128, 256):
    _map2url[i] = "%" + str(int2hex(i, 2))
_map2url[32] = "+"


names = ["path", "query", "fragment"]
indicator = ["/", "?", "#"]


def parse(output, suffix, curr, next):
    if next == len(indicator):
        output.__setattr__(names[curr], suffix)
        return

    e = suffix.find(indicator[next])
    if e == -1:
        parse(output, suffix, curr, next + 1)
    else:
        output.__setattr__(names[curr], suffix[:e:])
        parse(output, suffix[e + 1 : :], next, next + 1)


def hex2byte(v):
    return bytes([int(v, 16)])


def url_param2value(param):
    """
    CONVERT URL QUERY PARAMETERS INTO DICT
    """
    if param == None:
        return Null
    if param == None:
        return Null

    def _decode(vs):
        from mo_json import json2value

        results = []
        for v in vs.split(","):
            output = []
            i = 0
            # WE MUST TRACK THE STATE OF UTF* DECODING, IF ILLEGITIMATE ENCODING
            # THEN ASSUME LATIN1
            utf_remaining = 0
            start = 0
            while i < len(v):
                c = v[i]
                if utf_remaining:
                    if c == "%":
                        try:
                            hex = v[i + 1 : i + 3]
                            if hex.strip() == hex:
                                d = int(v[i + 1 : i + 3], 16)
                                if d & 0xC0 == 0x80:  # 10XX XXXX
                                    utf_remaining -= 1
                                    b = bytes([d])
                                    output.append(b)
                                    i += 3
                                    continue
                        except Exception:
                            pass
                    # missing continuation byte (# 10XX XXXX), try again
                    output = output[:-utf_remaining]
                    utf_remaining = 0
                    i = start
                    output.append(b"%")
                    i += 1
                else:
                    if c == "+":
                        output.append(b" ")
                        i += 1
                    elif c == "%":
                        try:
                            hex_pair = v[i + 1 : i + 3]
                            if hex_pair.strip() != hex_pair:
                                output.append(b"%")
                                i += 1
                                continue

                            d = int(hex_pair, 16)
                            if d & 0x80:
                                p = bin(d)[2:].find("0")
                                if p <= 1:
                                    output.append(b"%")
                                    i += 1
                                else:
                                    utf_remaining = p - 1
                                    start = i
                                    b = bytes([d])
                                    output.append(b)
                                    i += 3
                            else:
                                b = bytes([d])
                                output.append(b)
                                i += 3
                        except Exception:
                            output.append(b"%")
                            i += 1
                    else:
                        try:
                            output.append(c.encode("latin1"))
                        except Exception:
                            # WE EXPECT BYTES, BUT SOMEONE WILL GIVE US UNICODE STRINGS
                            output.append(c.encode("utf8"))
                        i += 1

            if utf_remaining:
                # missing continuation byte, try again
                output = output[:-utf_remaining] + [v[start:].encode("latin1")]

            output = b"".join(output).decode("utf8")
            try:
                output = json2value(output)
            except Exception:
                pass
            results.append(output)
        return unwraplist(results)

    query = Data()
    for p in param.split("&"):
        if not p:
            continue
        if "=" not in p:
            k = p
            v = True
        else:
            k, v = p.split("=", 1)
            k = _decode(k)
            v = _decode(v)

        u = query.get(k)
        if is_null(u):
            query[k] = v
        elif is_list(u):
            u += [v]
        else:
            query[k] = [u, v]

    return query


def from_paths(value):
    """
    CONVERT FROM SQUARE BRACKET LEAF FORM TO Data
    EXAMPLE: columns[1][name]
    :param value:
    :return:
    """
    output = Data()
    for k, v in value.items():
        path = k.split("[")
        if any(not p.endswith("]") for p in path[1:]):
            Log.error("expecting square brackets to be paired")
        path = [
            int(pp) if is_integer(pp) else pp for i, p in enumerate(path) for pp in [p.rstrip("]") if i > 0 else p]
        ]

        d = output
        for p, q in zip(path, path[1:]):
            if is_null(d[p]):
                if is_text(q):
                    d[p] = {}
                else:
                    d[p] = []
            elif is_text(q) == is_list(d[p]):
                Log.error(
                    "can not index {{type}} with {{key}}", type=type(d[p]).__name__, key=q,
                )

            d = d[p]
        d[path[-1]] = v

    return output


def value2url_param(value):
    """
    :param value:
    :return: ascii URL
    """
    from mo_json import value2json, json2value

    def _encode(value):
        return "".join(_map2url[c] for c in value.encode("utf8"))

    if value == None:
        return None

    if is_data(value):
        value_ = to_data(value)
        output = "&".join(
            kk + "=" + vv
            for k, v in sorted(value_.leaves(), key=lambda p: p[0])
            for kk, vv in [(value2url_param(k), value2url_param(v))]
            if vv or vv == 0
        )
    elif is_text(value):
        try:
            # IF STRING LOOKS LIKE JSON, THEN IT IS AMBIGUOUS, ENCODE IT
            json2value(value)
            output = _encode(value2json(value))
        except Exception:
            output = _encode(value)
    elif is_binary(value):
        output = "".join(_map2url[c] for c in value)
    elif is_many(value):
        if any(is_data(v) or is_many(v) for v in value):
            output = _encode(value2json(value))
        else:
            output = ",".join(vv for v in value for vv in [value2url_param(v)] if vv or vv == 0)
    else:
        output = _encode(value2json(value))
    return output


def is_integer(s):
    if s is True or s is False:
        return False

    try:
        if float(s) == round(float(s), 0):
            return True
        return False
    except Exception:
        return False

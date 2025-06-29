# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
import base64
import io
import os
import re
import shutil
from datetime import datetime
from mimetypes import MimeTypes
from tempfile import NamedTemporaryFile, mkdtemp

from mo_dots import Null, coalesce, get_module, is_list, to_data, is_sequence, is_data, is_missing, from_data
from mo_future import text, is_text, ConfigParser, StringIO
from mo_json import json2value
from mo_logs import Except, logger
from mo_logs.exceptions import get_stacktrace
from mo_math import randoms

from mo_files import mimetype
from mo_files.url import URL

windows_drive = re.compile(r"^/[a-zA-Z]:[/\\]")


class File:
    """
    ASSUMES ALL FILE CONTENT IS UTF8 ENCODED STRINGS
    """

    def __new__(cls, filename, key=None, buffering=2 ** 14, suffix=None):
        if filename == None:
            return Null
        elif isinstance(filename, File):
            return filename
        else:
            return object.__new__(cls)

    def __init__(self, filename, key=None, suffix=None, mime_type=None):
        """
        :param filename: STRING
        :param key: BASE64 AES KEY USED ON ENCRYPTED FILES
        :param mime_type: IN THE UNLIKELY CASE YOU WISH TO DICTATE THE mimetype
        """
        if isinstance(filename, File):
            return
        elif not is_text(filename):
            logger.error("Expecting str, not {type}", type=type(filename).__name__)

        self.key = base642bytearray(key)
        self._mime_type = mime_type

        if filename in (".", "/", ""):
            self._filename = filename or "."
        elif os.sep == "\\" and windows_drive.match(filename):
            self._filename = filename[1:]
        else:
            if filename.startswith("~"):
                home_path = os.path.expanduser("~").replace(os.sep, "/").rstrip("/")
                rel_path = filename[1::].replace(os.sep, "/").lstrip("/")
                filename = home_path + "/" + rel_path
            self._filename = filename.replace(os.sep, "/").rstrip("/")

        while self._filename.find(".../") >= 0:
            # LET ... REFER TO GRANDPARENT, .... REFER TO GREAT-GRAND-PARENT, etc...
            self._filename = self._filename.replace(".../", "../../")

    @classmethod
    def new_instance(cls, *path):
        return File(join_path(*path))

    def __div__(self, other):
        return File(join_path(self, other))

    def __truediv__(self, other):
        return File(join_path(self, other))

    def __rtruediv__(self, other):
        return File(join_path(other, self))

    @property
    def timestamp(self):
        output = os.path.getmtime(self.os_path)
        return output

    @property
    def rel_path(self):
        return self._filename

    @property
    def abs_path(self):
        if self._filename.startswith("~"):
            home_path = os.path.expanduser("~")
            if os.sep == "\\":
                home_path = home_path.replace(os.sep, "/")
            if home_path.endswith("/"):
                home_path = home_path[:-1]

            return home_path + self._filename[1::]
        else:
            if os.sep == "\\":
                return "/" + os.path.abspath(self._filename).replace(os.sep, "/")
            else:
                return os.path.abspath(self._filename)

    @property
    def os_path(self):
        """
        :return: OS-specific path
        """
        if os.sep == "/":
            return self.abs_path
        return str(self.abs_path).lstrip("/")

    def add_suffix(self, suffix):
        """
        ADD suffix TO THE filename (NOT INCLUDING THE FILE EXTENSION)
        """
        return add_suffix(self._filename, suffix)

    @property
    def extension(self):
        parts = self.name.split(".")
        if len(parts) == 1:
            return ""
        else:
            return parts[-1]

    @property
    def stem(self):
        parts = self.name.split(".")
        if len(parts) == 1:
            return parts[0]
        else:
            return ".".join(parts[0:-1])

    @property
    def name(self):
        return self._filename.split("/")[-1]

    @property
    def mime_type(self):
        if not self._mime_type:
            if self.abs_path.endswith(".js"):
                self._mime_type = "application/javascript"
            elif self.abs_path.endswith(".css"):
                self._mime_type = "text/css"
            elif self.abs_path.endswith(".json"):
                self._mime_type = mimetype.JSON
            else:
                mime = MimeTypes()
                self._mime_type, _ = mime.guess_type(self.abs_path)
                if not self._mime_type:
                    self._mime_type = mimetype.BINARY
        return self._mime_type

    def find(self, pattern):
        """
        :param pattern: REGULAR EXPRESSION TO MATCH NAME (NOT INCLUDING PATH)
        :return: LIST OF File OBJECTS THAT HAVE MATCHING NAME
        """

        def _find(dir):
            if re.match(pattern, dir._filename.split("/")[-1]):
                yield dir
            if dir.is_directory():
                for c in dir.children:
                    yield from _find(c)

        yield from _find(self)

    def set_extension(self, ext):
        """
        RETURN NEW FILE WITH GIVEN EXTENSION
        """
        path = self._filename.split("/")
        parts = path[-1].split(".")
        if len(parts) == 1:
            parts.append(ext)
        elif is_missing(ext):
            parts.pop()
        else:
            parts[-1] = ext

        path[-1] = ".".join(parts)
        return File("/".join(path))

    def add_extension(self, ext):
        """
        RETURN NEW FILE WITH EXTENSION ADDED (OLD EXTENSION IS A SUFFIX)
        """
        return File(self._filename + "." + str(ext))

    def set_name(self, name):
        """
        RETURN NEW FILE WITH GIVEN EXTENSION
        """
        path = self._filename.split("/")
        parts = path[-1].split(".")
        if len(parts) == 1:
            path[-1] = name
        else:
            path[-1] = name + "." + parts[-1]
        return File("/".join(path))

    def backup_name(self, timestamp=None):
        """
        RETURN A FILENAME THAT CAN SERVE AS A BACKUP FOR THIS FILE
        """
        suffix = datetime2string(coalesce(timestamp, datetime.utcnow()), "%Y%m%d_%H%M%S")
        return add_suffix(self._filename, suffix)

    def read(self, encoding="utf8") -> str:
        """
        :param encoding:
        :return:
        """
        with open(self._filename, "rb") as f:
            if self.key:
                return get_module("mo_math.crypto").decrypt(f.read(), self.key)
            else:
                content = f.read().decode(encoding)
                return content

    def read_zipfile(self, encoding="utf8"):
        """
        READ FIRST FILE IN ZIP FILE
        :param encoding:
        :return: STRING
        """
        from zipfile import ZipFile

        with ZipFile(self.abs_path) as zipped:
            for num, zip_name in enumerate(zipped.namelist()):
                return zipped.open(zip_name).read().decode(encoding)

    def read_lines(self, encoding="utf8"):
        with open(self._filename, "rb") as f:
            for line in f:
                yield line.decode(encoding).rstrip()

    def read_json(self, encoding="utf8", flexible=True, leaves=True):
        content = self.read(encoding=encoding)
        value = json2value(content, flexible=flexible)
        if '"$concat"' in content:
            return to_data(apply_functions(value))
        return value

    def is_directory(self):
        return os.path.isdir(self._filename)

    def read_bytes(self):
        try:
            if not self.parent.exists:
                self.parent.create()
            with open(self._filename, "rb") as f:
                if self.key:
                    return get_module("mo_math.crypto").decrypt(f.read(), self.key)
                else:
                    return f.read()
        except Exception as e:
            logger.error("Problem reading file {filename}", filename=self.abs_path, cause=e)

    def write_bytes(self, content):
        if not self.parent.exists:
            self.parent.create()
        with open(self._filename, "wb") as f:
            if self.key:
                f.write(get_module("mo_math.crypto").encrypt(content, self.key))
            else:
                f.write(content)

    def write(self, content):
        """
        :param content: text, or iterable of text
        :return:
        """
        if not self.parent.exists:
            self.parent.create()
        with open(self._filename, "wb") as f:
            if is_list(content) and self.key:
                logger.error("list of data and keys are not supported, encrypt before sending to file")

            if is_list(content):
                pass
            elif isinstance(content, text):
                content = [content]
            elif hasattr(content, "__iter__"):
                pass

            for d in content:
                if not is_text(d):
                    logger.error("Expecting unicode data only")
                if self.key:
                    from mo_math.aes_crypto import encrypt

                    f.write(encrypt(d, self.key).encode("utf8"))
                else:
                    f.write(d.encode("utf8"))

    def read_ini(self, encoding="utf8"):
        buff = StringIO(self.read(encoding))
        config = ConfigParser()
        config._read(buff, "dummy")

        output = {}
        for section in config.sections():
            output[section] = s = {}
            for k, v in config.items(section):
                s[k] = v
        return to_data(output)

    def write_ini(self, data, encoding="utf8"):
        config = ConfigParser()

        # Populate ConfigParser with the dictionary
        for section, keys in data.items():
            config.add_section(section)
            for key, value in keys.items():
                config.set(section, key, value)

        with open(self.os_path, "w") as configfile:
            config.write(configfile)

    def __iter__(self):
        # NOT SURE HOW TO MAXIMIZE FILE READ SPEED
        # http://stackoverflow.com/questions/8009882/how-to-read-large-file-line-by-line-in-python
        # http://effbot.org/zone/wide-finder.htm
        def output():
            try:
                path = self._filename
                if path.startswith("~"):
                    home_path = os.path.expanduser("~")
                    path = home_path + path[1::]

                with io.open(path, "rb") as f:
                    for line in f:
                        yield line.decode("utf8").rstrip()
            except Exception as e:
                logger.error(
                    "Can not read line from {{filename}}", filename=self._filename, cause=e,
                )

        return output()

    def append(self, content, encoding="utf8"):
        """
        add a line to file
        """
        if not self.parent.exists:
            self.parent.create()
        with open(self._filename, "ab") as output_file:
            if not is_text(content):
                logger.error("expecting to write unicode only")
            output_file.write(content.encode(encoding))
            output_file.write(b"\n")

    def __len__(self):
        return os.path.getsize(self.abs_path)

    def add(self, content):
        return self.append(content)

    def extend(self, content):
        try:
            if not self.parent.exists:
                self.parent.create()
            with open(self._filename, "ab") as output_file:
                for c in content:
                    if not isinstance(c, text):
                        logger.error("expecting to write unicode only")

                    output_file.write(c.encode("utf8"))
                    output_file.write(b"\n")
        except Exception as e:
            logger.error("Could not write to file", e)

    def delete(self):
        try:
            if os.path.isdir(self._filename):
                shutil.rmtree(self._filename)
            elif os.path.isfile(self._filename):
                os.remove(self._filename)
            return self
        except Exception as cause:
            cause = Except.wrap(cause)
            if (
                "The system cannot find the path specified" in cause
                or "The system cannot find the file specified" in cause
            ):
                return
            logger.error("Could not remove file", cause)

    def backup(self, format=" %Y%m%d %H%M%S"):
        path = self._filename.split("/")
        names = path[-1].split(".")
        backup_name = f"backup{datetime.utcnow().strftime(format)}"
        if len(names) == 1 or names[0] == "":
            names.append(backup_name)
        else:
            names.insert(-1, backup_name)
        backup_file = File.new_instance("/".join(path[:-1]), ".".join(names))
        File.copy(self, backup_file)
        return backup_file

    def create(self):
        try:
            os.makedirs(self.os_path)
        except FileExistsError:
            pass
        except Exception as e:
            logger.error(
                "Could not make directory {{dir_name}}", dir_name=self._filename, cause=e,
            )

    @property
    def children(self):
        try:
            return [File(self._filename + "/" + c) for c in os.listdir(self.rel_path)]
        except FileNotFoundError:
            return []

    @property
    def descendants(self):
        yield self
        if self.is_directory():
            for c in os.listdir(self.os_path):
                yield from File(self._filename + "/" + c).descendants

    @property
    def leaves(self):
        for c in os.listdir(self.os_path):
            child = File(self._filename + "/" + c)
            if child.is_directory():
                yield from child.leaves
            else:
                yield child

    @property
    def parent(self):
        if not self._filename or self._filename == ".":
            return File("..")
        elif self._filename.endswith(".."):
            return File(self._filename + "/..")
        else:
            return File("/".join(self._filename.split("/")[:-1]))

    def __bool__(self):
        return os.path.exists(self._filename)

    __nonzero__ = __bool__
    exists = property(__bool__)

    @property
    def length(self):
        return os.path.getsize(self._filename)

    size = length


    @classmethod
    def copy(cls, from_, to_):
        _copy(File(from_), File(to_))

    def __data__(self):
        return self._filename

    def __eq__(self, other):
        return isinstance(other, File) and other.abs_path == self.abs_path

    def __hash__(self):
        return self.abs_path.__hash__()

    def __str__(self):
        return self.abs_path


class TempDirectory(File):
    """
    A CONTEXT MANAGER FOR AN ALLOCATED, BUT UNOPENED TEMPORARY DIRECTORY
    WILL BE DELETED WHEN EXITED
    """

    def __new__(cls):
        return object.__new__(cls)

    def __init__(self):
        File.__init__(self, mkdtemp())

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        from mo_threads import Thread

        Thread.run("delete dir " + self.stem, delete_daemon, file=self, caller_stack=get_stacktrace(1)).release()


class TempFile(File):
    """
    A CONTEXT MANAGER FOR AN ALLOCATED, BUT UNOPENED TEMPORARY FILE
    WILL BE DELETED WHEN EXITED
    """

    def __new__(cls, *args, **kwargs):
        return object.__new__(cls)

    def __init__(self, filename=None):
        if isinstance(filename, File):
            return
        self.temp = NamedTemporaryFile(prefix=randoms.filename(), delete=False)
        self.temp.close()
        File.__init__(self, self.temp.name)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        from mo_threads import Thread

        Thread.run("delete file " + self.rel_path, delete_daemon, file=self, caller_stack=get_stacktrace(1),).release()


def _copy(from_, to_):
    if from_.is_directory():
        for c in os.listdir(from_.os_path):
            _copy(from_ / c, to_ / c)
    else:
        File.new_instance(to_).write_bytes(File.new_instance(from_).read_bytes())


def base642bytearray(value):
    if value == None:
        return bytearray(b"")
    else:
        return bytearray(base64.b64decode(value))


def datetime2string(value, format="%Y-%m-%d %H:%M:%S"):
    try:
        return value.strftime(format)
    except Exception as e:
        logger.error(
            "Can not format {{value}} with {{format}}", value=value, format=format, cause=e,
        )


def join_path(*path):
    def scrub(i, p):
        p = p.replace(os.sep, "/")
        if p in ("", "/"):
            return "."
        if p[-1] == "/":
            p = p[:-1]
        if i > 0 and p[0] == "/":
            p = p[1:]
        return p

    path = [p._filename if isinstance(p, File) else p for p in path]
    abs_prefix = ""
    if path and path[0]:
        if path[0][0] == "/":
            abs_prefix = "/"
            path[0] = path[0][1:]
        elif os.sep == "\\" and path[0][1:].startswith(":/"):
            # If windows, then look for the "c:/" prefix
            abs_prefix = path[0][0:3]
            path[0] = path[0][3:]

    scrubbed = []
    for i, p in enumerate(path):
        scrubbed.extend(scrub(i, p).split("/"))
    simpler = []
    for s in scrubbed:
        if s == ".":
            pass
        elif s == "..":
            if simpler:
                if simpler[-1] == "..":
                    simpler.append(s)
                else:
                    simpler.pop()
            elif abs_prefix:
                raise Exception("can not get parent of root")
            else:
                simpler.append(s)
        else:
            simpler.append(s)

    if not simpler:
        if abs_prefix:
            joined = abs_prefix
        else:
            joined = "."
    else:
        joined = abs_prefix + "/".join(simpler)

    return joined


def delete_daemon(file, caller_stack, please_stop):
    # WINDOWS WILL HANG ONTO A FILE FOR A BIT AFTER WE CLOSED IT
    from mo_threads import Till

    num_attempts = 0
    while not please_stop:
        try:
            if file.exists:
                return
            file.delete()
            return
        except Exception as e:
            e = Except.wrap(e)
            e.trace = e.trace[0:2] + caller_stack
            if num_attempts:
                logger.warning("problem deleting file {file}", file=file.abs_path, cause=e)
            (Till(seconds=10) | please_stop).wait()
        num_attempts += 1


def add_suffix(filename, suffix):
    """
    ADD .suffix TO THE filename (NOT INCLUDING THE FILE EXTENSION)
    """
    path = filename.split("/")
    parts = path[-1].split(".")
    i = max(len(parts) - 2, 0)
    parts[i] = parts[i] + "." + str(suffix).strip(".")
    path[-1] = ".".join(parts)
    return File("/".join(path))


def apply_functions(node):
    node = from_data(node)
    if is_data(node):
        output = {}
        diff = False
        for k, v in node.items():
            if k == "$concat":
                diff = True
                if not is_sequence(v):
                    logger.error("$concat expects an array of strings")
                return coalesce(node.get("separator"), "").join(apply_functions(vv) for vv in v)
            elif is_missing(v):
                diff = True
                continue
            else:
                vv = apply_functions(v)
                diff = diff or vv is not v
                output[k] = vv
        return output if diff else node
    elif is_list(node):
        output = []
        diff = False
        for v in node:
            vv = apply_functions(v)
            diff = diff or vv is not v
            output.append(vv)
        return output if diff else node
    return node

# More Files!

[![PyPI Latest Release](https://img.shields.io/pypi/v/mo-files.svg)](https://pypi.org/project/mo-files/)
[![Build Status](https://github.com/klahnakoski/mo-files/actions/workflows/build.yml/badge.svg?branch=master)](https://github.com/klahnakoski/mo-files/actions/workflows/build.yml)
[![Coverage Status](https://coveralls.io/repos/github/klahnakoski/mo-files/badge.svg?branch=dev)](https://coveralls.io/github/klahnakoski/mo-files?branch=dev)
[![Downloads](https://static.pepy.tech/badge/mo-files/month)](https://pepy.tech/project/mo-files)

The `File` class makes the default assumption all files have cr-delimited unicode content that is UTF-8 encoded. This is great for JSON files. It also provides better operators over some common file manipulations.




## Recent changes

**Version 6.x**

Get a little closer to Python's pathlib module standards

* `stem` - to refer file name without extension
* `os_path` - to get the os-specific absolute path for use in other Python modules
* `rel_path` - the given path 
* `abs_path` - was `abspath`, added underscore for consistency 




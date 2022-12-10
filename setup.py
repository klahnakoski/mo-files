# encoding: utf-8
# THIS FILE IS AUTOGENERATED!
from __future__ import unicode_literals
from setuptools import setup
setup(
    author='Kyle Lahnakoski',
    author_email='kyle@lahnakoski.com',
    classifiers=["Development Status :: 4 - Beta","Programming Language :: Python :: 3.7","Programming Language :: Python :: 3.8","Programming Language :: Python :: 3.9","Topic :: Software Development :: Libraries","Topic :: Software Development :: Libraries :: Python Modules","License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)"],
    description='More Files! Steamlined for UTF8 and JSON.',
    extras_require={"tests":["mo-testing"]},
    include_package_data=True,
    install_requires=["mo-dots==9.279.22339","mo-future==6.265.22338","mo-json==6.281.22341","mo-logs==7.279.22339","mo-math==7.280.22341"],
    license='MPL 2.0',
    long_description="# More Files!\n\nThe `File` class makes the default assumption all files have cr-delimited unicode content that is UTF-8 encoded. This is great for JSON files. It also provides better operators over some common file manipulations.\n\n\n\n\n\n\n\n## Recent changes\n\n**Version 6.x**\n\nGet a little closer to Python's pathlib module standards\n\n* `stem` - to refer file name without extension\n* `os_path` - to get the os-specific absolute path for use in other Python modules\n* `rel_path` - the given path \n* `abs_path` - added underscore for consistency \n\n\n\n",
    long_description_content_type='text/markdown',
    name='mo-files',
    packages=["mo_files"],
    url='https://github.com/klahnakoski/mo-files',
    version='6.292.22344',
    zip_safe=False
)
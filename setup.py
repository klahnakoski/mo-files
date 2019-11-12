# encoding: utf-8
# THIS FILE IS AUTOGENERATED!
from __future__ import unicode_literals
from setuptools import setup
setup(
    description=str(u'More Files! Steamlined for UTF8 and JSON.'),
    license=str(u'MPL 2.0'),
    author=str(u'Kyle Lahnakoski'),
    author_email=str(u'kyle@lahnakoski.com'),
    long_description_content_type=str(u'text/markdown'),
    include_package_data=True,
    classifiers=["Development Status :: 4 - Beta","Topic :: Software Development :: Libraries","Topic :: Software Development :: Libraries :: Python Modules","License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)"],
    install_requires=["mo-dots>=3.2.19316","mo-future>=3.1.19316","mo-logs>=3.2.19316"],
    version=str(u'3.4.19316'),
    url=str(u'https://github.com/klahnakoski/mo-files'),
    zip_safe=False,
    packages=["mo_files"],
    long_description=str(u'More Files!\n==========\n\nThe `File` class makes the default assumption all files have cr-delimited unicode content that is UTF-8 encoded. This is great for JSON files. It also provides better OO over some common file manipulations.\n\n'),
    name=str(u'mo-files')
)
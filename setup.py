# encoding: utf-8
# THIS FILE IS AUTOGENERATED!
from __future__ import unicode_literals
from setuptools import setup
setup(
    author='Kyle Lahnakoski',
    author_email='kyle@lahnakoski.com',
    classifiers=["Development Status :: 4 - Beta","Programming Language :: Python :: 3.7","Programming Language :: Python :: 3.9","Topic :: Software Development :: Libraries","Topic :: Software Development :: Libraries :: Python Modules","License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)"],
    description='More Files! Steamlined for UTF8 and JSON.',
    extras_require={"tests":["mo-testing"]},
    include_package_data=True,
    install_requires=["mo-dots==9.113.22021","mo-future==6.2.21303","mo-json==6.121.22022","mo-logs==7.121.22022","mo-math==7.121.22022"],
    license='MPL 2.0',
    long_description='More Files!\n==========\n\nThe `File` class makes the default assumption all files have cr-delimited unicode content that is UTF-8 encoded. This is great for JSON files. It also provides better OO over some common file manipulations.\n\n\n\n',
    long_description_content_type='text/markdown',
    name='mo-files',
    packages=["mo_files"],
    url='https://github.com/klahnakoski/mo-files',
    version='4.121.22022',
    zip_safe=False
)
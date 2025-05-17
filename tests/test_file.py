import os
from datetime import time
from unittest import TestCase

from mo_dots import Data
from mo_testing import FuzzyTestCase
from mo_times import Date

from mo_files import File


class TestFile(FuzzyTestCase):

    def test_read_file(self):
        self.assertEqual(File("tests/resources/test-file.txt").read(), 'Hello, World!')

    def test_read_lines0(self):
        self.assertEqual(list(File("tests/resources/test-file0.txt").read_lines()), ['Hello, World!'])

    def test_read_lines1(self):
        self.assertEqual(list(File("tests/resources/test-file1.txt").read_lines()), ['Hello, World!'])

    def test_read_lines2(self):
        self.assertEqual(list(File("tests/resources/test-file2.txt").read_lines()), ['Hello, World!', ''])

    def test_write_file(self):
        File("tests/resources/test-file.txt").write("Hello, World!")
        self.assertEqual(File("tests/resources/test-file.txt").read(), 'Hello, World!')

    def test_read_json(self):
        self.assertEqual(File("tests/resources/test-file.json").read_json(), {"hello": "world"})

    def test_write_json(self):
        File("tests/resources/test-file.json").write('{"hello": "world"}')
        self.assertEqual(File("tests/resources/test-file.json").read_json(), {"hello": "world"})

    def test_read_ini(self):
        File("tests/resources/test-file.ini").write("[hello]\nworld=world\n\n[world]\nhello=42")
        self.assertEqual(File("tests/resources/test-file.ini").read_ini(), {"hello": {"world":"world"}, "world": {"hello":"42"}})

    def test_concat1(self):
        result = File("tests/resources/test-concat1.json").read_json()
        self.assertEqual(result, "hello world")

    def test_concat2(self):
        result = File("tests/resources/test-concat2.json").read_json()
        self.assertEqual(result, {"a": "hello world"})
        self.assertIsInstance(result, Data)

    def test_file_timestamp(self):
        file = File("tests/__init__.py")
        mod_time_epoch = Date(1568322216).unix
        os.utime(file.os_path, (mod_time_epoch, mod_time_epoch))
        self.assertEqual(File("tests/__init__.py").timestamp, 1568322216)

    def test_leaves(self):
        files = list(f.name for f in File("tests/resources/").leaves)
        self.assertAlmostEqual(files, {
            "test-concat1.json",
            "test-concat2.json",
            "test-file.ini",
            "test-file.json",
            "test-file.txt",
            "test-file0.txt",
            "test-file1.txt",
            "test-file2.txt",
        })

    def test_backup(self):
        file = File("tests/resources/test-file.txt")
        now = Date.now().format("%Y%m%d %H%M%S")
        backup_file = file.backup()
        self.assertTrue(backup_file.exists)
        self.assertEqual(backup_file.name, f"test-file.backup {now}.txt")
        self.assertEqual(backup_file.read(), "Hello, World!")
        backup_file.delete()

    def test_backup_filename(self):
        file = File("tests/resources/test-file.txt")
        now = Date.now().format("-%Y-%m")
        backup_file = file.backup("-%Y-%m")
        self.assertTrue(backup_file.exists)
        self.assertEqual(backup_file.name, f"test-file.backup{now}.txt")
        self.assertEqual(backup_file.read(), "Hello, World!")
        backup_file.delete()

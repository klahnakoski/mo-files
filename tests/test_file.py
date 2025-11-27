import os
from unittest import skipIf

from mo_dots import Data, Null
from mo_testing import FuzzyTestCase
from mo_times import Date

from mo_files import File, is_windows


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
            "empty.json",
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

    def test_none_file(self):
        file = File(None)
        self.assertEqual(file, Null)

    def test_not_a_name(self):
        with self.assertRaises(Exception):
            File(12345)

    def test_div(self):
        file = File("tests/resources")
        self.assertEqual(file / "test-file.txt", File("tests/resources/test-file.txt"))
        self.assertEqual(file / "test-file2.txt", File("tests/resources/test-file2.txt"))
        self.assertEqual(file / "subdir" / "test-file2.txt", File("tests/resources/subdir/test-file2.txt"))

        with self.assertRaises(Exception):
            file / 12345

    def test_truediv(self):
        file = File("tests/resources")
        self.assertEqual(file / "test-file.txt", File("tests/resources/test-file.txt"))
        self.assertEqual(file / "test-file2.txt", File("tests/resources/test-file2.txt"))
        self.assertEqual(file / "subdir" / "test-file2.txt", File("tests/resources/subdir/test-file2.txt"))

        with self.assertRaises(Exception):
            file / 12345

    def test_stem(self):
        file = File("tests/resources/test-file.txt")
        self.assertEqual(file.stem, "test-file")

        file = File("tests/resources/test-file.json")
        self.assertEqual(file.stem, "test-file")

        file = File("tests/resources/subdir/test-file2.txt")
        self.assertEqual(file.stem, "test-file2")

        file = File("tests/resources/subdir/test-file2")
        self.assertEqual(file.stem, "test-file2")

    def test_extension(self):
        file = File("tests/resources/test-file.txt")
        self.assertEqual(file.extension, "txt")

        file = File("tests/resources/test-file.json")
        self.assertEqual(file.extension, "json")

        file = File("tests/resources/subdir/test-file2.txt")
        self.assertEqual(file.extension, "txt")

        file = File("tests/resources/subdir/test-file2")
        self.assertEqual(file.extension, "")

    def test_mime_type(self):
        file = File("tests/resources/test-file.txt")
        self.assertEqual(file.mime_type, "text/plain")

        file = File("tests/resources/test-file.json")
        self.assertEqual(file.mime_type, "application/json; charset=utf-8")

        file = File("tests/resources/subdir/test-file2.txt")
        self.assertEqual(file.mime_type, "text/plain")

        file = File("tests/resources/subdir/test-file2")
        self.assertEqual(file.mime_type, "application/octet-stream")

        file = File("test.xls")
        self.assertEqual(file.mime_type, "application/vnd.ms-excel")

    def test_set_extension(self):
        file = File("tests/resources/test-file.txt")
        new_file = file.set_extension("json")
        self.assertEqual(new_file.name, "test-file.json")

        new_file = file.set_extension("")
        self.assertEqual(new_file.name, "test-file")

        file = File("tests/resources/test-file")
        new_file = file.set_extension("xml")
        self.assertEqual(new_file.name, "test-file.xml")

    def test_descendants(self):
        file = File("tests/resources")
        descendants = list(file.descendants)
        self.assertEqual(len(descendants), 11)
        self.assertIn(File("tests/resources/test-file.txt"), descendants)
        self.assertIn(File("tests/resources/test-file.json"), descendants)
        self.assertIn(File("tests/resources/test-file2.txt"), descendants)
        self.assertIn(File("tests/resources/deep/empty.json"), descendants)
        self.assertIn(file, descendants)

    def test_leaves(self):
        file = File("tests/resources")
        leaves = list(file.leaves)
        self.assertEqual(len(leaves), 9)
        self.assertIn(File("tests/resources/test-file.txt"), leaves)
        self.assertIn(File("tests/resources/test-file.json"), leaves)
        self.assertIn(File("tests/resources/test-file2.txt"), leaves)
        self.assertIn(File("tests/resources/deep/empty.json"), leaves)

    def test_children(self):
        file = File("tests/resources")
        children = list(file.children)
        self.assertEqual(len(children), 9)
        self.assertIn(File("tests/resources/test-file.txt"), children)
        self.assertIn(File("tests/resources/deep"), children)

    def test_windows_root(self):
        file = File("C:/")
        refile = File(file.abs_path)
        self.assertEqual(file.abs_path, refile.abs_path)

    def test_exists(self):
        file = File("tests/resources/test-file.txt")
        self.assertTrue(file.exists)
        self.assertTrue(file)
        self.assertTrue(bool(file))
        non_existent_file = File("tests/resources/non_existent.txt")
        self.assertFalse(non_existent_file.exists)
        self.assertFalse(non_existent_file)
        self.assertFalse(bool(non_existent_file))

    @skipIf(is_windows, "This test is only for Windows")
    def test_os_path_on_windows(self):
        file = File("tests/resources/test-file.txt")
        self.assertTrue(file.os_path.endswith("tests\\resources\\test-file.txt"))
        self.assertTrue(file.os_path.startswith("C:\\"))

    @skipIf(is_windows, "This test is only for Windows")
    def test_home_dir(self):
        file = File("~")
        self.assertTrue(file.os_path.startswith("C:\\"))

    def test_home_dir(self):
        file = File("~")
        self.assertTrue(file.abs_path.startswith("/"))

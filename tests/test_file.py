from unittest import TestCase

from mo_files import File


class TestFile(TestCase):

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





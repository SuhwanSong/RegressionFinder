import unittest

from modules import CrossVersion
from helper import IOQueue

class TestCrossVersion(unittest.TestCase):
    def test_cross_version_test_html(self):
        vers = (921581, 921617, 100000)
        inputs = ['./testcases/bug_1270713.html']

        ioq = IOQueue(vers, inputs)
        cv = CrossVersion(ioq)
        cv.start()
        cv.join()

        ioq.move_to_preqs()
        html_file, hashes = ioq.pop_from_queue()
        self.assertEqual(html_file, inputs[0])
        self.assertNotEqual(hashes[0], hashes[1])


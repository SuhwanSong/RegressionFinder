import unittest

from modules import CrossVersion
from modules import Oracle
from helper import IOQueue

class TestModules(unittest.TestCase):
    def test_cross_version_test_html(self):
        vers = (921581, 921617, 94)
        inputs = ['./testcases/bug_1270713.html']

        ioq = IOQueue(vers, inputs)
        cv = CrossVersion(ioq)
        cv.start()
        cv.join()

        ioq.move_to_preqs()
        html_file, hashes = ioq.pop_from_queue()
        self.assertEqual(html_file, inputs[0])
        self.assertNotEqual(hashes[0], hashes[1])

    def test_oracle_test_html(self):
        vers = (921581, 921617, 94)
        inputs = ['./testcases/bug_1270713_oracle.html']

        ioq = IOQueue(vers, inputs)
        cv = CrossVersion(ioq)
        cv.start()
        cv.join()
        ioq.move_to_preqs()
        oc = Oracle(ioq)
        oc.start()
        oc.join()
        ioq.move_to_preqs()
        html_file, hashes = ioq.pop_from_queue()
        self.assertEqual(html_file, inputs[0])
        self.assertNotEqual(hashes[0], hashes[1])

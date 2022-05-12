import unittest

from modules import CrossVersion
from modules import Oracle
from helper import IOQueue

class TestModules(unittest.TestCase):
    def test_cross_version_with_correct_versions(self):

        # bug commit is 921604
        base_commit_of_chrome = 921581
        target_commit_of_chrome = 921617

        versions = (base_commit_of_chrome, 
                    target_commit_of_chrome, 
                    None)
        inputs = ['./testcases/bug_1270713.html']

        ioq = IOQueue(versions, inputs)
        cv = CrossVersion(ioq)
        cv.start()
        cv.join()
        ioq.move_to_preqs()

        html_file, hashes = ioq.pop_from_queue()
        self.assertEqual(html_file, inputs[0])
        self.assertNotEqual(hashes[0], hashes[1])

    def test_cross_version_with_incorrect_versions(self):

        # bug commit is 921604
        base_commit_of_chrome = 921617
        target_commit_of_chrome = 921660

        versions = (base_commit_of_chrome, 
                    target_commit_of_chrome, 
                    None)
        inputs = ['./testcases/bug_1270713.html']

        ioq = IOQueue(versions, inputs)
        cv = CrossVersion(ioq)
        cv.start()
        cv.join()
        ioq.move_to_preqs()
    
        """
        This should be None because CrossVersion discards the testcase
        that generates the same results.
        """
        self.assertIsNone(ioq.pop_from_queue())

    def test_oracle(self):

        # bug commit is 921604
        base_commit_of_chrome = 921581
        target_commit_of_chrome = 921617
        firefox_version = 94

        versions = (base_commit_of_chrome, 
                    target_commit_of_chrome, 
                    firefox_version)
        inputs = ['./testcases/bug_1270713_oracle.html']

        ioq = IOQueue(versions, inputs)
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

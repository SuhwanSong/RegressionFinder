import unittest

from modules import CrossVersion
from modules import Oracle
from modules import Bisecter

from helper import IOQueue

class TestModules(unittest.TestCase):
    def test_cross_version_with_correct_versions(self):

        # bug commit is 921604
        base_commit_of_chrome = 921581
        target_commit_of_chrome = 921617

        versions = (base_commit_of_chrome, 
                    target_commit_of_chrome, 
                    None)
        input_version_pair = {'./testcases/bug_1270713.html': versions}

        ioq = IOQueue(input_version_pair)
        cv = CrossVersion(ioq)
        cv.start()
        cv.join()
        ioq.move_to_preqs()

        for inp in input_version_pair:
            html_file, hashes = ioq.pop_from_queue()
            self.assertEqual(html_file, inp)
            self.assertNotEqual(hashes[0], hashes[1])

    def test_cross_version_with_incorrect_versions(self):

        # bug commit is 921604
        base_commit_of_chrome = 921617
        target_commit_of_chrome = 921660

        versions = (base_commit_of_chrome, 
                    target_commit_of_chrome, 
                    None)
        input_version_pair = {'./testcases/bug_1270713.html': versions}

        ioq = IOQueue(input_version_pair)
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
        input_version_pair = {'./testcases/bug_1270713_oracle.html': versions}

        ioq = IOQueue(input_version_pair)
        cv = CrossVersion(ioq)
        cv.start()
        cv.join()
        ioq.move_to_preqs()

        oc = Oracle(ioq)
        oc.start()
        oc.join()
        ioq.move_to_preqs()

        for inp in input_version_pair:
            html_file, hashes = ioq.pop_from_queue()
            self.assertEqual(html_file, inp)
            self.assertNotEqual(hashes[0], hashes[1])

    def test_bisect_analysis(self):

        # bug commit is 921604
        base_commit_of_chrome = 921547
        target_commit_of_chrome = 921852

        base_answer  = 921581
        target_answer = 921617

        versions = (base_commit_of_chrome, 
                    target_commit_of_chrome, 
                    None)

        input_version_pair = {
                './testcases/bug_1270713_oracle.html': versions,
        }

        ioq = IOQueue(input_version_pair)
        cv = CrossVersion(ioq)
        cv.start()
        cv.join()
        ioq.move_to_preqs()

        bi = Bisecter(ioq)
        bi.start()
        bi.join()
        ioq.move_to_preqs()

        vers = ioq.get_vers()
        for inp in input_version_pair:
            html_file, hashes = ioq.pop_from_queue()
            self.assertEqual(html_file, inp)
            self.assertNotEqual(hashes[0], hashes[1])
            self.assertEqual(base_answer, vers[0])
            self.assertEqual(target_answer, vers[1])




class TestRespins(unittest.TestCase):
    def test_2020_post_stable_regressions(self):

        input_version_pair = {
            './testcases/bug_1151858.html': (802513, 802538, 83),
            './testcases/bug_1151295.html': (802513, 802538, 83)
        }

        ioq = IOQueue(input_version_pair)
        cv = CrossVersion(ioq)
        cv.start()
        cv.join()
        ioq.move_to_preqs()

        oc = Oracle(ioq)
        oc.start()
        oc.join()
        ioq.move_to_preqs()

        for inp in input_version_pair:
            html_file, hashes = ioq.pop_from_queue()
            self.assertEqual(html_file, inp)
            self.assertNotEqual(hashes[0], hashes[1])


import os
import unittest

from helper import VersionManager
from driver import Browser

EXPECT_SIZE = [800, 300]

class TestDriver(unittest.TestCase):
    def test_viewport_of_chrome(self):
        vm = VersionManager()
        rev = vm.get_revision(90)
        browser = Browser('chrome', rev)
        browser.setup_browser()
        size = browser.exec_script('return [window.innerWidth, window.innerHeight]')
        self.assertEqual(size, EXPECT_SIZE)
        browser.kill_browser()

    def test_viewport_of_firefox(self):
        browser = Browser('firefox', '101.0')
        browser.setup_browser()
        size = browser.exec_script('return [window.innerWidth, window.innerHeight]')
        self.assertEqual(size, EXPECT_SIZE)
        browser.kill_browser()


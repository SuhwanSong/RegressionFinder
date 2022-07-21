import os
import unittest
import tempfile

from helper import FileManager
from helper import VersionManager

from chrome_binary import ChromeBinary
from firefox_binary import FirefoxBinary

class TestBinary(unittest.TestCase):
    def test_chrome_binary(self):
        vm = VersionManager()
        rev = vm.get_revision(90)

        with tempfile.TemporaryDirectory() as outdir:
            cb = ChromeBinary()
            cb.ensure_chrome_binaries(outdir, rev)
            browser_path = cb.get_browser_path(outdir, rev)
            driver_path = cb.get_driver_path(outdir, rev)

            self.assertTrue(os.path.exists(browser_path))
            self.assertTrue(os.path.exists(driver_path))

    def test_firefox_binary(self):
        with tempfile.TemporaryDirectory() as outdir:
            ver = '101.0'
            fb = FirefoxBinary()
            fb.ensure_firefox_binaries(outdir, ver)
            browser_path = fb.get_browser_path(outdir, ver)
            driver_path = fb.get_driver_path(outdir, ver)

            self.assertTrue(os.path.exists(browser_path))
            self.assertTrue(os.path.exists(driver_path))

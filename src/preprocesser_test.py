import os
import unittest

import tempfile

from helper import FileManager
from modules import Preprocesser

class TestPreprocesser(unittest.TestCase):
    def test_html_generation_if_input_dir_is_empty(self):
        num_of_thread = 4
        ver1 = 90
        ver2 = 91
        with tempfile.TemporaryDirectory() as indir:
            with tempfile.TemporaryDirectory() as outdir:
                Preprocesser(indir, outdir, num_of_thread, ver1, ver2)
            self.assertTrue(len(FileManager.get_all_files(indir, '.html')), num_of_thread * 1000)

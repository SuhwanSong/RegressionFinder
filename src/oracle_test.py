import os
import unittest

import tempfile

from helper import IOQueue
from helper import FileManager
from helper import VersionManager
from modules import CrossVersion
from modules import Oracle

BUG_HTML = """
<!DOCTYPE html>
<style>
polygon { transform: translate3d(0px, 10px, 0); }
</style>
<svg>
  <polygon points="0 10 0 7 1 38" stroke="currentColor">
  </polygon>
</svg>
"""

NONBUG_HTML = """
<body>
"""

def oracle_(html):
    with tempfile.TemporaryDirectory() as outdir:
        vm = VersionManager()
        rev1 = vm.get_revision(90)
        rev2 = vm.get_revision(91)

        firefox_version = '101.0'

        input_html_path = os.path.join(outdir, 'input.html')
        FileManager.write_file(input_html_path, html)

        ioq = IOQueue([input_html_path], [rev1, rev2], firefox_version)

        cv = CrossVersion(ioq)
        cv.start()
        cv.join()
        ioq.move_to_preqs()

        oc = Oracle(ioq)
        oc.start()
        oc.join()
        ioq.move_to_preqs()

        return input_html_path, ioq.pop_from_queue()

class TestOracle(unittest.TestCase):
    def test_bug_html(self):
        input_html_path, ref = oracle_(BUG_HTML)

        html_file, hashes = ref
        self.assertEqual(html_file, input_html_path)


    def test_nonbug_html(self):
        input_html_path, ref = oracle_(NONBUG_HTML)
        self.assertEqual(ref, None)

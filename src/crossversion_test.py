import os
import unittest

import tempfile

from helper import IOQueue
from helper import FileManager
from helper import VersionManager
from modules import CrossVersion

CHANGE_HTML = """
<!DOCTYPE html>
<style>
  div { columns: 42; }
  dt { overflow: clip; }
</style>
<div>
  <dt>1rjd\ID=P@3</dt>
</div>
"""

NOCHANGE_HTML = """
<body>
"""

def cross_version_(html):
    with tempfile.TemporaryDirectory() as outdir:
        vm = VersionManager()
        rev1 = vm.get_revision(90)
        rev2 = vm.get_revision(91)

        temp_input = os.path.join(outdir, 'input.html')
        FileManager.write_file(temp_input, html)

        ioq = IOQueue([temp_input], [rev1, rev2], None)

        cv = CrossVersion(ioq)
        cv.start()
        cv.join()

        ioq.move_to_preqs()
        return temp_input, ioq.pop_from_queue()

class TestCrossVersion(unittest.TestCase):
    def test_change_html(self):
        temp_input, ref = cross_version_(CHANGE_HTML)

        html_file, hashes = ref
        self.assertEqual(html_file, temp_input)
        self.assertEqual(hashes[0], '483b7a717c3eaa17a82598a1f55ff9a14cebd8f0')
        self.assertEqual(hashes[1], 'c4f3fd1c798d3521832d7d8e67000f20c2a80ad7')

    def test_nochange_html(self):
        temp_input, ref = cross_version_(NOCHANGE_HTML)
        self.assertEqual(ref, None)

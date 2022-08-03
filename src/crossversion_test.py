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

        input_html_path = os.path.join(outdir, 'input.html')
        FileManager.write_file(input_html_path, html)

        ioq = IOQueue([input_html_path], [rev1, rev2], None)

        cv = CrossVersion(ioq)
        cv.start()
        cv.join()

        ioq.move_to_preqs()
        return input_html_path, ioq.pop_from_queue()

class TestCrossVersion(unittest.TestCase):
    def test_change_html(self):
        input_html_path, popped = cross_version_(CHANGE_HTML)
        ref, _ = popped

        html_file, hashes = ref
        self.assertEqual(html_file, input_html_path)

        # The hash may be different depending on OS and/or font rendering. The
        # following were calculated on linux and macos.
        good_hashes_0 = [
            '6aa88f6b651e9c74adee34b3da0730df6c0fd472',
            '483b7a717c3eaa17a82598a1f55ff9a14cebd8f0',
        ]
        good_hashes_1 = [
            'c4f3fd1c798d3521832d7d8e67000f20c2a80ad7',
            '31b8c25bc35a62774a7e5d1527e2fee074891b11',
        ]
        self.assertIn(hashes[0], good_hashes_0)
        self.assertIn(hashes[1], good_hashes_1)

    def test_nochange_html(self):
        input_html_path, ref = cross_version_(NOCHANGE_HTML)
        self.assertEqual(ref, None)

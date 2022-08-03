import os
import re
import time

from datetime import timedelta
from pyvirtualdisplay import Display
from os.path import basename, join, dirname

from driver import Browser
from typing import Optional, Tuple

from helper import IOQueue
from helper import ImageDiff
from helper import FileManager
from helper import VersionManager

from threading import Thread
from threading import current_thread

from bisect import bisect

from pathlib import Path
from shutil import copyfile
from bs4 import BeautifulSoup
from collections import defaultdict


class CrossVersion(Thread):
    def __init__(self, helper: IOQueue) -> None:
        super().__init__()
        self.br_list = []

        self.helper = helper
        self.saveshot = False

        self.baseflag = os.getenv('BASEFLAG', '')
        self.targetflag = os.getenv('TARGETFLAG', '')

    def report_mode(self) -> None:
        self.saveshot = True

    def get_newer_browser(self) -> Browser:
        return self.br_list[-1] if self.br_list else None

    def start_browsers(self, vers: Tuple[int, int, int]) -> bool:
        self.stop_browsers()
        self.helper.download_chrome(vers[0])
        self.helper.download_chrome(vers[1])

        self.br_list.append(Browser('chrome', vers[0], self.baseflag))
        self.br_list.append(Browser('chrome', vers[1], self.targetflag))
        for br in self.br_list:
            if not br.setup_browser():
                return False
        return True

    def stop_browsers(self) -> None:
        for br in self.br_list:
            br.kill_browser()
        self.br_list.clear()

    def cross_version_test_html(self, html_file: str) -> Optional[list]:
        img_hashes = []

        thread_id = current_thread()
        for br in self.br_list:
            self.helper.record_current_test(thread_id, br, html_file)
            hash_v = br.get_hash_from_html(html_file, self.saveshot)
            if hash_v is None:
                return

            img_hashes.append(hash_v)
            self.helper.delete_record(thread_id, br, html_file)

        return img_hashes

    def cross_version_test_html_nth(self, html_file: str, nth: int = 0) -> Optional[list]:
        hashes = self.cross_version_test_html(html_file)
        # if not bug, just return hashes
        if hashes is None or not self.is_bug(hashes): return hashes

        # if bug, do more
        for _ in range(nth):
            new_hashes = self.cross_version_test_html(html_file)
            if hashes != new_hashes: return 
        return hashes

    def is_bug(self, hashes):
        return hashes and ImageDiff.diff_images(hashes[0], hashes[1])

    def run(self) -> None:
        start = time.time()
        cur_vers = None
        hpr = self.helper
        while True:

            popped = hpr.pop_from_queue()
            if not popped: break

            result, vers = popped
            html_file, _ = result

            if cur_vers != vers:
                cur_vers = vers
                if not self.start_browsers(cur_vers):
                    continue

            hashes = self.cross_version_test_html_nth(html_file, 2)
            if self.is_bug(hashes):
              hpr.update_postq(vers, html_file, hashes)

        self.stop_browsers()


class Oracle(Thread):
    def __init__(self, helper: IOQueue) -> None:
        super().__init__()
        self.helper = helper
        self.ref_br = None
        self.ref_br_type = 'firefox'

        self.saveshot = False

    def report_mode(self) -> None:
        self.saveshot = True

    def start_ref_browser(self, ver: str) -> bool:
        self.stop_ref_browser()
        self.ref_br = Browser(self.ref_br_type, ver)
        return self.ref_br.setup_browser()

    def stop_ref_browser(self):
        if self.ref_br:
            self.ref_br.kill_browser()
            self.ref_br = None

    def is_regression(self, hashes: tuple, ref_hash) -> bool:
        return not ImageDiff.diff_images(hashes[0], ref_hash)


    def run(self) -> None:

        cur_refv = None
        hpr = self.helper
        while True:
            popped = hpr.pop_from_queue()
            if not popped: break

            result, vers = popped
            html_file, hashes = result
            if len(hashes) != 2:
                raise ValueError('Something wrong in hashes...')

            refv = vers[-1]
            if cur_refv != refv:
                cur_refv = refv
                if not self.start_ref_browser(cur_refv):
                    continue

            ref_hash = self.ref_br.get_hash_from_html(html_file, self.saveshot)
            if ref_hash is not None and self.is_regression(hashes, ref_hash):
                hpr.update_postq(vers, html_file, hashes)

        self.stop_ref_browser()

class ChromeOracle(Oracle):
    def __init__(self, helper: IOQueue) -> None:
        super().__init__(helper)

        self.ref_br_type = 'chrome'


class Bisecter(Thread):
    def __init__(self, helper: IOQueue) -> None:
        super().__init__()
        self.helper = helper
        self.ref_br = None
        self.saveshot = False
        self.cur_mid = None

        self.build = False

    def start_ref_browser(self, ver: int) -> bool:
        self.stop_ref_browser()
        self.helper.download_chrome(ver)
        self.ref_br = Browser('chrome', ver)
        return self.ref_br.setup_browser()

    def stop_ref_browser(self) -> None:
        if self.ref_br:
            self.ref_br.kill_browser()
            self.ref_br = None

    def get_chrome(self, ver: int) -> None:
        pass

    def get_pixel_from_html(self, html_file):
        return self.ref_br.get_hash_from_html(html_file, self.saveshot)

    def run(self) -> None:
        cur_mid = None
        hpr = self.helper

        while True:
            popped = hpr.pop_from_queue()
            if not popped: break

            result, vers = popped
            html_file, hashes = result
            if len(hashes) != 2:
                raise ValueError('Something wrong in hashes...')

            hpr.set_version_list(html_file, self.build)

            start, end, ref = vers
            if start >= end:
                print (html_file, 'start and end are the same;')
                continue

            start_idx = hpr.convert_to_index(html_file, start)
            end_idx = hpr.convert_to_index(html_file, end)

            if start_idx + 1 == end_idx:
                hpr.update_postq(vers, html_file, hashes)
                continue

            mid_idx = (start_idx + end_idx) // 2
            mid = hpr.convert_to_ver(html_file, mid_idx)
            self.cur_mid = mid
            if cur_mid != mid:
                cur_mid = mid
                self.get_chrome(cur_mid)
                if not self.start_ref_browser(cur_mid):
                    continue

            ref_hash = self.get_pixel_from_html(html_file)
            if ref_hash is None:
                continue

            elif not ImageDiff.diff_images(hashes[0], ref_hash):
                if mid_idx + 1 == end_idx:
                    hpr.update_postq((mid, end, ref), html_file, hashes)
                    #print (html_file, mid, end, 'postq 1')
                    continue
                low = hpr.convert_to_ver(html_file, mid_idx)
                high = end

            elif not ImageDiff.diff_images(hashes[1], ref_hash):
                if mid_idx - 1 == start_idx:
                    hpr.update_postq((start, mid, ref), html_file, hashes)
                    #print (html_file, start, mid, 'postq 2')
                    continue
                low = start
                high = hpr.convert_to_ver(html_file, mid_idx)
            else:
                continue
            hpr.insert_to_queue((low, high, ref), html_file, hashes)
#            if ref_hash is None:
#                hpr.pop_index_from_list(html_file, mid_idx)
#                hpr.insert_to_queue((start, end, ref), html_file, hashes)
#                continue
#
#            elif not ImageDiff.diff_images(hashes[0], ref_hash):
#                if mid_idx + 1 == end_idx:
#                    hpr.update_postq((mid, end, ref), html_file, hashes)
#                    #print (html_file, mid, end, 'postq 1')
#                    continue
#                low = hpr.convert_to_ver(html_file, mid_idx)
#                high = end
#
#            else:
#            #elif not ImageDiff.diff_images(hashes[1], ref_hash):
#                if mid_idx - 1 == start_idx:
#                    hpr.update_postq((start, mid, ref), html_file, hashes)
#                    #print (html_file, start, mid, 'postq 2')
#                    continue
#                low = start
#                high = hpr.convert_to_ver(html_file, mid_idx)
#
#            hpr.insert_to_queue((low, high, ref), html_file, hashes)

        self.stop_ref_browser()


class BisecterBuild(Bisecter):
    def __init__(self, helper: IOQueue) -> None:
        super().__init__(helper)

        self.build = True

    def get_chrome(self, ver: int) -> None:
        self.helper.build_chrome(ver)


class Minimizer(CrossVersion):
    def __init__(self, helper: IOQueue) -> None:
        CrossVersion.__init__(self, helper)

        self.__min_html = None
        self.__html_file = None
        self.__temp_file = None
        self.__trim_file = None


    def __remove_temp_files(self):
        os.remove(self.__temp_file)
        os.remove(self.__trim_file)

    def __initial_test(self, html_file):

        self.__html_file = html_file
        self.__trim_file = join(dirname(html_file),
                'trim' + basename(html_file))
        self.__temp_file = join(dirname(html_file),
                'temp' + basename(html_file))

        copyfile(html_file, self.__trim_file)
        copyfile(html_file, self.__temp_file)

        self.__min_html = FileManager.read_file(html_file)
        hashes = self.cross_version_test_html_nth(html_file, 0) 
        return self.is_bug(hashes)


    def __minimize_sline(self, idx, style_lines):
        style_line = style_lines[idx]

        style_line = re.sub('{ ', '{ \n', style_line)
        style_line = re.sub(' }', ' \n}', style_line)
        style_line = re.sub('; ', '; \n', style_line)
        style_blocks = style_line.split('\n')

        min_blocks = style_blocks
        min_indices = range(len(style_blocks))

        trim_sizes = [ pow(2,i) for i in range(3,-1,-1) ]
        trim_sizes = [x for x in trim_sizes if x < len(style_blocks)]
        for trim_size in trim_sizes:
            for offset in range(1, len(style_blocks) - 2, trim_size):
                if offset not in min_indices:
                    continue

                trim_indices = range(offset, min(offset + trim_size, len(style_blocks) - 2))

                tmp_blocks = []
                tmp_indices = []
                for i, line in enumerate(style_blocks):
                    if i not in trim_indices and i in min_indices:
                        tmp_blocks.append(style_blocks[i])
                        tmp_indices.append(i)

                last_block =  tmp_blocks[-1]
                if last_block[-2:] == '; ':
                    tmp_blocks[-1] = last_block[:-2] + ' '

                tmp_line = ''.join(tmp_blocks) + '\n'

                style_lines[idx] = tmp_line

                tmp_html = re.sub(re.compile(r'<style>.*?</style>', re.DOTALL), \
                                  '<style>' + ''.join(style_lines) + '</style>', self.__cat_html)

                FileManager.write_file(self.__trim_file, tmp_html)

                hashes = self.cross_version_test_html_nth(self.__trim_file, 0)
                if self.is_bug(hashes):
                    min_blocks = tmp_blocks
                    min_indices = tmp_indices
                    FileManager.write_file(self.__temp_file, tmp_html)

        min_line = ''.join(min_blocks) + '\n'
        return min_line

    def __minimize_slines(self, style):
        style_content = style.contents[0]
        style_lines = [ line + '\n' for line in style_content.split('\n') if '{ }' not in line]

        min_lines = style_lines
        for i in range(len(style_lines)):
            if 'DO NOT REMOVE' in style_lines[i]: 
                break
            min_line = self.__minimize_sline(i, min_lines)
            min_lines[i] = min_line

        min_style = '<style>\n' + ''.join(min_lines) + '</style>'
        return min_style

    def __minimize_style(self):
        self.__cat_html = self.__min_html
        soup = BeautifulSoup(self.__cat_html, "lxml")
        if soup.style is not None and soup.style != " None":
            try:
                min_style = self.__minimize_slines(soup.style)
                self.__cat_html = re.sub(re.compile(r'<style>.*?</style>', re.DOTALL), \
                                       min_style, self.__cat_html)

                self.__min_html = self.__cat_html
            except:
                return
        else:
            return True

    def __minimize_dom(self):
        br = self.get_newer_browser()
        br.run_html(self.__temp_file)
        attrs = br.get_dom_tree_info()
        if not attrs: return

        for i in reversed(range(len(attrs))):
            br.run_html(self.__temp_file)
            br.exec_script(f'document.body.querySelectorAll(\'*\')[{i}].remove();')

            text = br.get_source()
            if not text: continue
            FileManager.write_file(self.__trim_file, text)
            br.clean_html()
            hashes = self.cross_version_test_html_nth(self.__trim_file, 0) 
            if self.is_bug(hashes):
                self.__min_html = text
                FileManager.write_file(self.__temp_file, self.__min_html)
            else:
                for attr in attrs[i]:
                    br.run_html(self.__temp_file)
                    br.exec_script(
                            f'document.body.querySelectorAll(\'*\')[{i}].removeAttribute(\'{attr}\');')
    
                    text = br.get_source()
                    if not text: continue
                    FileManager.write_file(self.__trim_file, text)
                    br.clean_html()
                    hashes = self.cross_version_test_html_nth(self.__trim_file, 0) 
                    if self.is_bug(hashes):
                        self.__min_html = text
                        FileManager.write_file(self.__temp_file, self.__min_html)

    def __minimize_inner_element(self):
        br = self.get_newer_browser()
        br.run_html(self.__temp_file)
        attrs = br.get_dom_tree_info()
        if not attrs: return

        for i in reversed(range(len(attrs))):
            br.run_html(self.__temp_file)
            br.exec_script(
                f'temp1 = document.body.querySelectorAll(\'*\')[{i}];'.format(i) +
                'if (temp1.nextElementSibling) {' +
                'temp1.parentNode.append(...temp1.childNodes, temp1.nextElementSibling);}' +
                'else { temp1.parentNode.append(...temp1.childNodes);} ' + 
                'temp1.remove();'
            )

            text = br.get_source()
            if not text: continue
            FileManager.write_file(self.__trim_file, text)
            br.clean_html()
            hashes = self.cross_version_test_html_nth(self.__trim_file, 0) 
            if self.is_bug(hashes):
                self.__min_html = text
                FileManager.write_file(self.__temp_file, self.__min_html)

    def __minimize_text(self):
        br = self.get_newer_browser()
        br.run_html(self.__temp_file)
        attrs = br.get_dom_tree_info()
        if not attrs: return

        for i in reversed(range(len(attrs))):
            br.run_html(self.__temp_file)
            br.exec_script(f'document.body.querySelectorAll(\'*\')[{i}].textContent = \'\';')
            text = br.get_source()
            if not text: continue
            FileManager.write_file(self.__trim_file, text)
            br.clean_html()
            hashes = self.cross_version_test_html_nth(self.__trim_file, 0) 
            if self.is_bug(hashes):
                self.__min_html = text
                FileManager.write_file(self.__temp_file, self.__min_html)

    def __minimizing(self):
        self.__minimize_style()
        self.__minimize_dom()
        self.__minimize_text()
        self.__minimize_inner_element()


    def run(self) -> None:
        cur_vers = None
        hpr = self.helper
        while True:
            popped = hpr.pop_from_queue()
            if not popped: break

            result, vers = popped
            html_file, _ = result

            if cur_vers != vers:
                cur_vers = vers
                if not self.start_browsers(cur_vers):
                    continue

            if self.__initial_test(html_file):
                self.__minimizing()
  
                hashes = self.cross_version_test_html_nth(self.__temp_file, 1)
                if self.is_bug(hashes):
                    min_html_file = os.path.splitext(html_file)[0] + '-min.html'
                    copyfile(self.__temp_file, min_html_file)
                    hpr.update_postq(vers, min_html_file, hashes)

            self.__remove_temp_files()

        self.stop_browsers()


class Preprocesser:
    def __init__(self, input_dir: str, output_dir: str, num_of_threads: int,
                 base_version: int, target_version: int) -> None:

        self.in_dir = input_dir
        self.out_dir = output_dir
        self.num_of_threads = num_of_threads
        self.base_ver = base_version
        self.target_ver = target_version

        self.experiment_result = {}
        self.tester = [
                CrossVersion,
                Minimizer,
        ]
        self.report = [
        ]

        self.oracle_br = {'type': None, 'ver': None}

    def skip_minimizer(self):
        self.tester.remove(Minimizer)


    def test_wrapper(self, test_class: object, report: bool = False) -> None:
        start = time.time()
        threads = []
        for i in range(self.num_of_threads):
            threads.append(test_class(self.ioq))
            threads[-1].saveshot = report

        class_name = type(threads[-1]).__name__
        print (f'{class_name} stage starts...')

        for th in threads:
            th.start()

        all_terminated = False
        while not all_terminated:
            self.ioq.monitoring()
            time.sleep(10)
            all_terminated = not any([th.is_alive() for th in threads])

        self.ioq.reset_lock()
        elapsed = time.time() - start
        elapsed_time = str(timedelta(seconds=elapsed))
        print (f'{class_name} stage ends...', elapsed_time)

        if not report:
            self.experiment_result[class_name] = [self.ioq.num_of_outputs, elapsed_time]
        self.ioq.move_to_preqs()
        if not report:
            dirname = class_name
            dir_path = os.path.join(self.out_dir, dirname)
            self.ioq.dump_queue(dir_path)


    def process(self) -> None:
        start = time.time()

        self.vm = VersionManager()
        testcases = FileManager.get_all_files(self.in_dir, '.html')
        rev_range = self.vm.get_rev_range(self.base_ver, self.target_ver)

        brtype = self.oracle_br['type']
        brver = self.oracle_br['ver']

        if not brtype or brtype == 'firefox':
            oracle_ver = brver
        elif brtype == 'chrome':
            oracle_ver = vm.get_revision(brver)
        else:
            raise ValueError('something wrong at self.oracle_br')

        num_of_tests = len(testcases)
        rev_a = rev_range[0]
        rev_b = rev_range[-1]

        print (f'# of tests: {num_of_tests}, rev_a: {rev_a}, rev_b: {rev_b}, rev_c: {oracle_ver}')

        self.ioq = IOQueue(testcases, rev_range, oracle_ver)

        disp = Display(size=(1200, 800))
        disp.start()

        for test in self.tester: 
            self.test_wrapper(test)

        elapsed = time.time() - start
        self.experiment_result['TOTAL TIME'] = str(timedelta(seconds=elapsed))

        if self.report:
            self.ioq.dump_queue_with_sort(os.path.join(self.out_dir, 'Report'))
            for test in self.report: 
                self.test_wrapper(test, True)

        disp.stop()
        print (self.experiment_result)


class ChromeRegression(Preprocesser):
    def __init__(self, input_dir: str, output_dir: str, num_of_threads: int,
                 base_version: int, target_version: int, oracle_version: int) -> None:
        super().__init__(input_dir, output_dir, num_of_threads, base_version, target_version)

        self.tester.extend([
                ChromeOracle,
                Bisecter,

        ])

        self.report.extend([
                CrossVersion,
                ChromeOracle
        ])
        self.oracle_br = {'type': 'chrome', 'ver': oracle_version}


class FirefoxRegression(Preprocesser):
    def __init__(self, input_dir: str, output_dir: str, num_of_threads: int,
                 base_version: int, target_version: int, oracle_version: int) -> None:
        super().__init__(input_dir, output_dir, num_of_threads, base_version, target_version)


        self.tester.extend([
                Oracle,
                Bisecter,
        ])

        self.report.extend([
                CrossVersion,
                Oracle,
        ])

        self.oracle_br = {'type': 'firefox', 'ver': oracle_version}
        if os.getenv('BASEFLAG', '') != os.getenv('TARGETFLAG', ''):
            self.skip_bisect()

    def skip_bisect(self):
        self.tester.remove(Bisecter)

    def answer(self, answer_version) -> None:
        print ('answer step')
        ref_br = Browser('chrome', self.vm.get_end_revision(answer_version))
        ref_br.setup_browser()

        hpr = self.ioq

        report_dict = defaultdict(list)
        bug_dict = defaultdict(int)
        nonbug_dict = defaultdict(int)
        while True:
            popped = hpr.pop_from_queue()
            if not popped: break

            result, vers = popped
            html_file, hashes = result
            if len(hashes) != 2:
                raise ValueError('Something wrong in hashes...')

            try:
                ref_hash = ref_br.get_hash_from_html(html_file, True)
            except Exception as e:
                print (e)
                continue

            culprit = vers[1]
            report_dict[culprit].append(html_file)

            if not ImageDiff.diff_images(hashes[0], ref_hash):
                bug_dict[culprit] += 1
                hpr.update_postq(vers, html_file, hashes)
            else:
                nonbug_dict[culprit] += 1

        ref_br.kill_browser()
        self.ioq.move_to_preqs()
        dir_path = os.path.join(self.out_dir, 'Report')
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        self.ioq.dump_queue_as_csv(dir_path)

        vers = list(report_dict.keys())
        vers.sort()
        data = []
        for ver in vers:
            ret = ''
            if ver in bug_dict and ver in nonbug_dict:
                ret = 'both'
            elif ver in bug_dict:
                ret = 'yes'
            else:
                ret = 'no'
            data.append(f'{ver} {ret}\n')
        FileManager.write_file(os.path.join(dir_path, 'overall.txt'), ''.join(data))

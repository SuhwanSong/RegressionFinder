import os
import re
import time
from datetime import timedelta

from driver import Browser
from typing import Optional

from helper import IOQueue
from helper import ImageDiff
from helper import FileManager

from threading import Thread

from bisect import bisect

from pathlib import Path
from shutil import copyfile
from bs4 import BeautifulSoup

from jshelper import GET_ATTRNAMES


class CrossVersion(Thread):
    def __init__(self, helper: IOQueue) -> None:
        super().__init__()
        self.__br_list = []

        self.helper = helper
        self.saveshot = False
        self.fnr = True

    def report_mode(self) -> None:
        self.saveshot = True
        self.fnr = True

    def get_newer_browser(self) -> Browser:
        return self.__br_list[-1] if self.__br_list else None

    def start_browsers(self, vers: tuple[int, int, int]) -> bool:
        self.stop_browsers()
        self.__br_list.append(Browser('chrome', vers[0]))
        self.__br_list.append(Browser('chrome', vers[1]))
        for br in self.__br_list:
            if not br.setup_browser():
                return False
        return True

    def stop_browsers(self) -> None:
        num_of_flake = 0
        num_of_flake2 = 0
        for br in self.__br_list: 
            #print (br.time)
            #print (br.count)
            num_of_flake += br.flak['BAD HTML']
            num_of_flake2 += br.flak['BAD HTML DIFF']
            br.kill_browser()
        self.__br_list.clear()
        #print ('NUM_OF_FLAKE', num_of_flake , num_of_flake2)

    def cross_version_test_html(self, html_file: str) -> Optional[list]:
        img_hashes = []
        for br in self.__br_list:
            hash_v = br.get_hash_from_html(html_file, self.saveshot, self.fnr)
            if hash_v is None: 
                return

            img_hashes.append(hash_v)

        return img_hashes

    def cross_version_test_html_nth(self, html_file: str) -> Optional[list]:
        hashes = self.cross_version_test_html(html_file)
        for _ in range(0):
            if not self.is_bug(hashes):
                return 
            hashes = self.cross_version_test_html(html_file)
        return hashes

    def is_bug(self, hashes):
        return hashes and ImageDiff.diff_images(hashes[0], hashes[1])

    def run(self) -> None:
        start = time.time()
        cur_vers = None
        hpr = self.helper
        while True:

            vers = hpr.get_vers()
            if not vers: break

            result = hpr.pop_from_queue()
            if not result: break
            html_file, _ = result

            if cur_vers != vers:
                cur_vers = vers

                hpr.download_chrome(cur_vers[0])
                hpr.download_chrome(cur_vers[1])
                if not self.start_browsers(cur_vers):
                    continue
            
            hashes = self.cross_version_test_html_nth(html_file)
            if self.is_bug(hashes): 
                hpr.update_postq(vers, html_file, hashes)

        self.stop_browsers()
        print ('total', time.time() - start)


class Oracle(Thread):
    def __init__(self, helper: IOQueue) -> None:
        super().__init__()
        self.helper = helper
        self.ref_br = None
        self.ref_br_type = 'firefox'

        self.saveshot = False
        self.fnr = True

    def report_mode(self) -> None:
        self.saveshot = True
        self.fnr = True

    def start_ref_browser(self, ver: int) -> bool:
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
            vers = hpr.get_vers()
            if not vers: break

            result = hpr.pop_from_queue()
            if not result: break
            html_file, hashes = result
            if len(hashes) != 2:
                raise ValueError('Something wrong in hashes...')

            refv = vers[-1]
            if cur_refv != refv:
                cur_refv = refv
                if not self.start_ref_browser(cur_refv):
                    continue

            ref_hash = self.ref_br.get_hash_from_html(html_file, self.saveshot, self.fnr)
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
        self.version_list = {}
        self.index_hash = {}
        self.saveshot = False
        self.cur_mid = None

    def start_ref_browser(self, ver: int) -> bool:
        self.stop_ref_browser()
        self.ref_br = Browser('chrome', ver)
        return self.ref_br.setup_browser()

    def stop_ref_browser(self) -> None:
        if self.ref_br:
            self.ref_br.kill_browser()
            self.ref_br = None

    def set_version_list(self, html_file) -> None:
        verlist = FileManager.get_bisect_csv()
        if html_file not in self.version_list:
            self.version_list[html_file] = list(verlist)
            self.index_hash[html_file] = {}
            for idx, ver in enumerate(self.version_list[html_file]):
                self.index_hash[html_file][ver] = idx

    def convert_to_ver(self, html_file, index: int) -> int:
        return self.version_list[html_file][index]

    def convert_to_index(self, html_file, ver: int) -> int:
        return self.index_hash[html_file][ver]

    def pop_ver_from_list(self, html_file, ver):
        self.version_list[html_file].remove(ver)
        self.index_hash[html_file] = {}
        for idx, ver in enumerate(self.version_list[html_file]):
            self.index_hash[html_file][ver] = idx

    def get_chrome(self, ver: int) -> None:
        self.helper.download_chrome(ver)

    def get_pixel_from_html(self, html_file): 
        return self.ref_br.get_hash_from_html(html_file, self.saveshot, True)

    def run(self) -> None:
        cur_mid = None
        hpr = self.helper

        while True:
            vers = hpr.get_vers()
            if not vers: 
                break
            #print (vers)

            result = hpr.pop_from_queue()
            if not result: 
                break
            html_file, hashes = result
            if len(hashes) != 2:
                raise ValueError('Something wrong in hashes...')

            self.set_version_list(html_file)

            start, end, ref = vers
            if start >= end: 
                print (html_file, 'start and end are the same;')
                continue

            start_idx = self.convert_to_index(html_file, start)
            end_idx = self.convert_to_index(html_file, end)

#            if start_idx + 1 == end_idx:
#                hpr.update_postq((start, end, ref), html_file, hashes)

            mid_idx = (start_idx + end_idx) // 2
            mid = self.convert_to_ver(html_file, mid_idx)
            self.cur_mid = mid
            if cur_mid != mid:
                cur_mid = mid
                self.get_chrome(cur_mid)
                if not self.start_ref_browser(cur_mid):
                    continue

            ref_hash = self.get_pixel_from_html(html_file)
            if ref_hash is None:
                self.pop_ver_from_list(html_file, mid)
                hpr.insert_to_queue((start, end, ref), html_file, hashes)
                continue

            elif not ImageDiff.diff_images(hashes[0], ref_hash):
                if mid_idx + 1 == end_idx:
                    hpr.update_postq((mid, end, ref), html_file, hashes)
                    #print (html_file, mid, end, 'postq 1')
                    continue
                low = self.convert_to_ver(html_file, mid_idx)
                high = end

            else:
            #elif not ImageDiff.diff_images(hashes[1], ref_hash):
                if mid_idx - 1 == start_idx:
                    hpr.update_postq((start, mid, ref), html_file, hashes)
                    #print (html_file, start, mid, 'postq 2')
                    continue
                low = start
                high = self.convert_to_ver(html_file, mid_idx)

            hpr.insert_to_queue((low, high, ref), html_file, hashes)

        self.stop_ref_browser()


class BisecterBuild(Bisecter):
    def __init__(self, helper: IOQueue) -> None:
        super().__init__(helper)

    def set_version_list(self) -> None:
        pass

    def convert_to_ver(self, index: int) -> int:
        return index

    def convert_to_index(self, ver: int) -> int:
        return ver

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
        self.__trim_file = os.path.join(os.path.dirname(html_file), 
                'trim' + os.path.basename(html_file))
        self.__temp_file = os.path.join(os.path.dirname(html_file), 
                'temp' + os.path.basename(html_file))

        copyfile(html_file, self.__trim_file)
        copyfile(html_file, self.__temp_file)

        self.__min_html = FileManager.read_file(html_file)
        hashes = self.cross_version_test_html_nth(html_file) 
        return self.is_bug(hashes)


    def __minimize_sline(self, idx, style_lines):
        style_line = style_lines[idx]

        style_line = re.sub('{ ', '{ \n', style_line)
        style_line = re.sub(' }', ' \n}', style_line)
        style_line = re.sub('; ', '; \n', style_line)
        style_blocks = style_line.split('\n')

        #print('> Minimizing style idx: {} ...'.format(idx))
        #print('> Initial style entries: {}'.format(len(style_blocks)))

        min_blocks = style_blocks
        min_indices = range(len(style_blocks))

        trim_sizes = [ pow(2,i) for i in range(3,-1,-1) ] # 8, 4, 2, 1
        trim_sizes = [x for x in trim_sizes if x < len(style_blocks)]
        for trim_size in trim_sizes:
            #print('> Setting trim size: {}'.format(trim_size))
            for offset in range(1, len(style_blocks) - 2, trim_size):
                if offset not in min_indices:
                    continue
                #print('> Current style entries: {}'.format(len(min_blocks)))

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
                                  '<style>\n' + ''.join(style_lines) + '\n</style>', self.__cat_html)

                FileManager.write_file(self.__trim_file, tmp_html)

                hashes = self.cross_version_test_html_nth(self.__trim_file)
                if self.is_bug(hashes):
                    min_blocks = tmp_blocks
                    min_indices = tmp_indices
                    FileManager.write_file(self.__temp_file, tmp_html)

        min_line = ''.join(min_blocks) + '\n'
        return min_line

    def __minimize_slines(self, style):
        style_content = style.contents[0]
        style_lines = [ line + '\n' for line in style_content.split('\n') if '{ }' not in line]
        #print (style_lines)

        min_lines = style_lines
        for i in range(len(style_lines)):
            min_line = self.__minimize_sline(i, min_lines)
            min_lines[i] = min_line

        min_style = '<style>\n' + ''.join(min_lines) + '\n</style>'
        return min_style

    def __minimize_style(self):
        self.__cat_html = self.__min_html
        soup = BeautifulSoup(self.__cat_html, "lxml")
        if soup.style is not None and soup.style != " None":
            try:
                min_style = self.__minimize_slines(soup.style)
                self.__cat_html = re.sub(re.compile(r'<style>.*?</style>', re.DOTALL), \
                                       min_style, self.__cat_html)

                self.__min_html = [ line + '\n' for line in self.__cat_html.split('\n') ]
            except:
                #print ('style is ', soup.style)
                return
        else:
            return True

    def __minimize_dom(self):
        br = self.get_newer_browser()
        br.run_html(self.__temp_file)
        attrs = br.exec_script(GET_ATTRNAMES)
        if not attrs: return

        for i in reversed(range(len(attrs))):
            br.run_html(self.__temp_file)
            br.exec_script(f'document.body.querySelectorAll(\'*\')[{i}].remove();')

            text = br.get_source()
            if not text: continue
            FileManager.write_file(self.__trim_file, text)
            hashes = self.cross_version_test_html_nth(self.__trim_file) 
            if self.is_bug(hashes):
                #print (f'{i}th element is removed')
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
                    hashes = self.cross_version_test_html_nth(self.__trim_file) 
                    if self.is_bug(hashes):
                        #print (f'{attr} attr is removed')
                        self.__min_html = text
                        FileManager.write_file(self.__temp_file, self.__min_html)

    def __minimize_line(self):
        self.__in_html = self.__min_html.split('\n')
        in_html_num_lines = len(self.__in_html)
        self.__min_indices = range(in_html_num_lines) 

#        self.__min_html = '\n'.join(self.__min_html)

        try_indices = []
        for i, line in enumerate(self.__in_html):
            try_indices.append(i)

        trim_sizes = [ pow(2, i) for i in range(7,-1,-1) ] # 128,64,32,16,8,4,2,1
        trim_sizes = [x for x in trim_sizes if x < in_html_num_lines]

        for trim_size in trim_sizes:
            for offset in range(1, len(try_indices), trim_size):
                if try_indices[offset] not in self.__min_indices:
                    continue

                trim_range = range(offset, min(offset + trim_size, len(try_indices)))
                trim_indices = [ try_indices[i] for i in trim_range ]

                min_html = []
                min_indices = []
                for i, line in enumerate(self.__in_html):
                    if i not in trim_indices and i in self.__min_indices:
                        min_html.append(line + '\n')
                        min_indices.append(i)
                
                min_html_str = ''.join(min_html)
                FileManager.write_file(self.__trim_file, min_html_str)
                hashes = self.cross_version_test_html_nth(self.__trim_file) 
                if self.is_bug(hashes):
                    self.__min_html = min_html_str
                    self.__min_indices = min_indices
                    FileManager.write_file(self.__temp_file, self.__min_html)

    def __minimizing(self):
        self.__minimize_line()
        self.__minimize_style()
        self.__minimize_dom()


    def run(self) -> None:
        cur_vers = None
        hpr = self.helper
        while True:
            vers = hpr.get_vers()
            if not vers: break

            result = hpr.pop_from_queue()
            if not result: break
            html_file, _ = result

            if cur_vers != vers:
                cur_vers = vers
                if not self.start_browsers(cur_vers):
                    continue


            if self.__initial_test(html_file):
                self.__minimizing()
  
                hashes = self.cross_version_test_html_nth(self.__temp_file)
                if self.is_bug(hashes):
                    min_html_file = os.path.splitext(html_file)[0] + '-min.html'
                    copyfile(self.__temp_file, min_html_file)
                    hpr.update_postq(vers, min_html_file, hashes)

            self.__remove_temp_files()

        self.stop_browsers()


class R2Z2:
    def __init__(self, input_version_pair: dict[str, tuple[int, int, int]], output_dir: str, num_of_threads: int) -> None:
        self.ioq = IOQueue(input_version_pair)
        self.out_dir = output_dir
        self.num_of_threads = num_of_threads

        self.experiment_result = {}

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

        for th in threads:
            th.join(timeout=3600 * 24)

        end = time.time()
        elapsed = end - start
        elapsed_time = str(timedelta(seconds=elapsed))
        print (f'{class_name} stage ends...')
        print (elapsed_time)
        if not report:
            self.experiment_result[class_name] = [self.ioq.num_of_outputs, elapsed_time]
        self.ioq.move_to_preqs()
        if not report:
            dirname = class_name
            dir_path = os.path.join(self.out_dir, dirname)
            self.ioq.dump_queue_with_sort(dir_path)
            self.ioq.dump_queue_as_csv(os.path.join(dir_path, 'result.csv'))


    def process(self) -> None:
        tester = [
                CrossVersion,
                Minimizer,
                Oracle,
                Bisecter,
                BisecterBuild
        ]

        for test in tester: 
            self.test_wrapper(test)

#        dir_path = os.path.join(self.out_dir, 'Result')
#        self.ioq.dump_queue_with_sort(dir_path)
#        self.ioq.dump_queue_as_csv(os.path.join(dir_path, 'result.csv'))

        report = [
                CrossVersion,
        ]

        for test in report: 
            self.test_wrapper(test, True)



class Finder(R2Z2):
    def __init__(self, input_version_pair: dict[str, tuple[int, int, int]], output_dir: str, num_of_threads: int, answer_version: int) -> None:
        super().__init__(input_version_pair, output_dir, num_of_threads)
        self.__answer_version = answer_version


    def answer(self) -> None:
        print ('answer step')
        ref_br = Browser('chrome', self.__answer_version)
        ref_br.setup_browser()

        hpr = self.ioq
        while True:
            vers = hpr.get_vers()
            if not vers: break

            result = hpr.pop_from_queue()
            if not result: break
            html_file, hashes = result
            if len(hashes) != 2:
                raise ValueError('Something wrong in hashes...')

            ref_hash = ref_br.get_hash_from_html(html_file, True, True)
            if ref_hash is None:
                continue
            if not ImageDiff.diff_images(hashes[0], ref_hash):
                hpr.update_postq(vers, html_file, hashes)

        ref_br.kill_browser()
        self.ioq.move_to_preqs()
        dir_path = os.path.join(self.out_dir, 'answer')
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        self.ioq.dump_queue_as_csv(os.path.join(dir_path, 'result.csv'))


    def process(self) -> None:
        start = time.time()
        tester = [
                CrossVersion,
        #        Minimizer,
                Oracle,
                Bisecter,
        ]

        for test in tester: 
            self.test_wrapper(test)

        end = time.time()
        elapsed = end - start
        elapsed_time = str(timedelta(seconds=elapsed))
        self.experiment_result['TOTAL'] = [self.ioq.num_of_outputs, elapsed_time]

        report = [
                CrossVersion,
                Oracle,
        ]

        for test in report: 
            self.test_wrapper(test, True)

        self.answer()
        print (self.experiment_result)

class ChromeRegression(R2Z2):
    def __init__(self, input_version_pair: dict[str, tuple[int, int, int]], output_dir: str, num_of_threads: int) -> None:
        super().__init__(input_version_pair, output_dir, num_of_threads)


    def process(self) -> None:
        start = time.time()
        tester = [
                CrossVersion,
        #        Minimizer,
                ChromeOracle,
                Bisecter,
        ]

        for test in tester: 
            self.test_wrapper(test)

        self.ioq.dump_queue_with_sort(os.path.join(self.out_dir, 'Report'))
        end = time.time()
        elapsed = end - start
        elapsed_time = str(timedelta(seconds=elapsed))
        self.experiment_result['TOTAL'] = [self.ioq.num_of_outputs, elapsed_time]
        report = [
                CrossVersion,
                ChromeOracle
        ]

        for test in report: 
            self.test_wrapper(test, True)
        print (self.experiment_result)


class Preprocesser:
    def __init__(self, input_version_pair: dict[str, tuple[int, int, int]], output_dir: str, num_of_threads: int) -> None:
        self.ioq = IOQueue(input_version_pair)
        self.out_dir = output_dir
        self.num_of_threads = num_of_threads

        self.experiment_result = {}

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
        for th in threads:
            th.join()

        self.ioq.reset_lock()

        end = time.time()
        elapsed = end - start
        elapsed_time = str(timedelta(seconds=elapsed))
        print (f'{class_name} stage ends...')

        if not report:
            self.experiment_result[class_name] = [self.ioq.num_of_outputs, elapsed_time]
        self.ioq.move_to_preqs()
        print (elapsed_time)
        if not report:
            dirname = class_name
            dir_path = os.path.join(self.out_dir, dirname)
            self.ioq.dump_queue(dir_path)
            #self.ioq.dump_queue_as_csv(os.path.join(dir_path, 'result.csv'))


    def process(self) -> None:
        tester = [
                CrossVersion,
                Minimizer,
        ]

        for test in tester: 
            self.test_wrapper(test)

import os
import re

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


class CrossVersion(Thread):
    def __init__(self, helper: IOQueue) -> None:
        super().__init__()
        self.helper = helper
        self.__br_list = []
        print ('CrossVersion created...')

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
        for br in self.__br_list: br.kill_browser()
        self.__br_list.clear()

    def cross_version_test_html(self, html_file: str, save_shot: bool = False) -> Optional[list]:

        img_hashes = []
        for br in self.__br_list:
            hash_v = br.get_hash_from_html(html_file, save_shot)
            if not hash_v: return

            img_hashes.append(hash_v)

        return img_hashes

    def is_bug(self, hashes):
        return  hashes and ImageDiff.diff_images(hashes[0], hashes[1])

    def run(self) -> None:

        cur_vers = None
        hpr = self.helper
        while True:
            vers = hpr.get_vers()
            if not vers: break

            if cur_vers != vers:
                cur_vers = vers

                hpr.get_chrome(cur_vers[0])
                hpr.get_chrome(cur_vers[1])
                if not self.start_browsers(cur_vers):
                    continue
            html_file, _ = hpr.pop_from_queue()

            hashes = self.cross_version_test_html(html_file)
            if self.is_bug(hashes):
                hpr.update_postq(vers, html_file, hashes)

        self.stop_browsers()


class Oracle(Thread):
    def __init__(self, helper: IOQueue) -> None:
        super().__init__()
        self.helper = helper
        self.__ref_br = None
        print ('Oracle created...')

    def __start_ref_browser(self, ver: int) -> bool:
        self.__stop_ref_browser()
        self.__ref_br = Browser('firefox', ver)
        return self.__ref_br.setup_browser()

    def __stop_ref_browser(self):
        if self.__ref_br:
            self.__ref_br.kill_browser()
            self.__ref_br = None

    def __is_regression(self, hashes: tuple, ref_hash) -> bool:
        #return hashes[0] != hashes[1] and hashes[0] == ref_hash
        return hashes[0] == ref_hash


    def run(self) -> None:

        cur_refv = None
        hpr = self.helper
        while True:
            vers = hpr.get_vers()
            if not vers: break

            refv = vers[-1]
            if cur_refv != refv:
                cur_refv = refv
                if not self.__start_ref_browser(cur_refv):
                    continue

            html_file, hashes = hpr.pop_from_queue()
            if len(hashes) != 2:
                raise ValueError('Something wrong in hashes...')

            ref_hash = self.__ref_br.get_hash_from_html(html_file)
            if ref_hash and self.__is_regression(hashes, ref_hash):
                hpr.update_postq(vers, html_file, hashes)

        self.__stop_ref_browser()


class Bisecter(Thread):
    def __init__(self, helper: IOQueue) -> None:
        super().__init__()
        self.helper = helper
        self.__ref_br = None
        self.__version_list = [] 

    def __start_ref_browser(self, ver: int) -> bool:
        self.__stop_ref_browser()
        self.__ref_br = Browser('chrome', ver)
        return self.__ref_br.setup_browser()

    def __stop_ref_browser(self) -> None:
        if self.__ref_br:
            self.__ref_br.kill_browser()
            self.__ref_br = None

    def __set_version_list(self):
        self.__version_list = FileManager.get_bisect_csv()

    def __convert_to_ver(self, index: int) -> int:
        return self.__version_list[index]

    def __convert_to_index(self, ver: int) -> int:
        return bisect(self.__version_list, ver) 

    def run(self) -> None:

        cur_mid = None
        hpr = self.helper
        self.__set_version_list()

        while True:
            vers = hpr.get_vers()
            if not vers: break

            start, end, ref = vers
            if start >= end: continue

            start_idx = self.__convert_to_index(start)
            end_idx = self.__convert_to_index(end)

            html_file, hashes = hpr.pop_from_queue()
            if len(hashes) != 2:
                raise ValueError('Something wrong in hashes...')

            if end_idx - start_idx == 1:
                hpr.update_postq(vers, html_file, hashes)
                continue

            mid_idx = (start_idx + end_idx) // 2
            mid = self.__convert_to_ver(mid_idx)
            if cur_mid != mid:
                cur_mid = mid
                hpr.get_chrome(cur_mid)
                if not self.__start_ref_browser(cur_mid):
                    continue

            ref_hash = self.__ref_br.get_hash_from_html(html_file)
            if not ref_hash: continue

            if hashes[0] == ref_hash:
                low = self.__convert_to_ver(mid_idx + 1)
                high = end

            elif hashes[1] == ref_hash:
                low = start
                high = self.__convert_to_ver(mid_idx - 1)
            else:
                continue

            hpr.insert_to_queue((low, high, ref), html_file, hashes)

        self.__stop_ref_browser()


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
        hashes = self.cross_version_test_html(html_file) 
        #print ('before', hashes[0] - hashes[1])
        return self.is_bug(hashes)


    def __minimize_sline(self, idx, style_lines):
        style_line = style_lines[idx]

        style_line = re.sub('{ ', '{ \n', style_line)
        style_line = re.sub(' }', ' \n}', style_line)
        style_line = re.sub('; ', '; \n', style_line)
        style_blocks = style_line.split('\n')

        print('> Minimizing style idx: {} ...'.format(idx))
        print('> Initial style entries: {}'.format(len(style_blocks)))

        min_blocks = style_blocks
        min_indices = range(len(style_blocks))

        trim_sizes = [ pow(2,i) for i in range(3,-1,-1) ] # 8, 4, 2, 1
        trim_sizes = [x for x in trim_sizes if x < len(style_blocks)]
        for trim_size in trim_sizes:
            print('> Setting trim size: {}'.format(trim_size))
            for offset in range(1, len(style_blocks) - 2, trim_size):
                if offset not in min_indices:
                    continue
                print('> Current style entries: {}'.format(len(min_blocks)))

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

                hashes = self.cross_version_test_html(self.__trim_file)
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
                print ('style is ', soup.style)
                return
        else:
            return True

    def __minimize_dom(self):
        br = self.get_newer_browser()
        br.run_html(self.__temp_file)
        attrs = br.exec_script('return get_all_attrnames();')
        for i in range(len(attrs) - 1, 0, -1):
            br.run_html(self.__temp_file)
            br.exec_script(f'document.body.querySelectorAll(\'*\')[{i}].remove();')

            text = br.get_source()
            FileManager.write_file(self.__trim_file, text)
            hashes = self.cross_version_test_html(self.__trim_file) 
            if self.is_bug(hashes):
                print (f'{i}th element is removed')
                self.__min_html = text
                FileManager.write_file(self.__temp_file, self.__min_html)
            else:
                for attr in attrs[i]:
                    br.run_html(self.__temp_file)
                    br.exec_script(
                            f'document.body.querySelectorAll(\'*\')[{i}].removeAttribute(\'{attr}\');')
    
                    text = br.get_source()
                    FileManager.write_file(self.__trim_file, text)
                    hashes = self.cross_version_test_html(self.__trim_file) 
                    if self.is_bug(hashes):
                        print (f'{attr} attr is removed')
                        self.__min_html = text
                        FileManager.write_file(self.__temp_file, self.__min_html)


    def __minimizing(self):
        self.__minimize_dom()
        self.__minimize_style()


    def run(self) -> None:
        cur_vers = None
        hpr = self.helper
        while True:
            vers = hpr.get_vers()
            if not vers: break

            if cur_vers != vers:
                cur_vers = vers
                if not self.start_browsers(cur_vers):
                    continue
            html_file, _ = hpr.pop_from_queue()

            if self.__initial_test(html_file):
                self.__minimizing()

                hashes = self.cross_version_test_html(self.__temp_file)
                #print ('after', hashes[0] - hashes[1])
                min_html_file = os.path.splitext(html_file)[0] + '-min.html'
                copyfile(self.__temp_file, min_html_file)
                if self.is_bug(hashes):
                    hpr.update_postq(vers, min_html_file, hashes)

            self.__remove_temp_files()

        self.stop_browsers()


class R2Z2:
    def __init__(self, input_version_pair: dict[str, tuple[int, int, int]], output_dir: str, num_of_threads: int):
        self.__ioq = IOQueue(input_version_pair)
        self.__out_dir = output_dir
        self.__num_of_threads = num_of_threads

    def test_wrapper(self, test_class: object):
        num_of_threads = min(self.__num_of_threads, self.__ioq.num_of_inputs // 2 + 1)
        
        threads = []
        for i in range(num_of_threads):
            threads.append(test_class(self.__ioq))

        class_name = type(threads[-1]).__name__

        for th in threads:
            th.start()

        for th in threads:
            th.join()

        dir_path = os.path.join(self.__out_dir, class_name)
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        self.__ioq.dump_queue(dir_path)
        self.__ioq.dump_queue_as_csv(os.path.join(dir_path, 'result.csv'))
        self.__ioq.move_to_preqs()

    def process(self):
        self.test_wrapper(CrossVersion)
        self.test_wrapper(Minimizer)
        self.test_wrapper(Oracle)
        self.test_wrapper(Bisecter)


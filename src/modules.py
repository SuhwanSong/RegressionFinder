from driver import Browser
from typing import Optional

from helper import IOQueue
from helper import ImageDiff
from helper import FileManager
from threading import Thread

from bisect import bisect

class CrossVersion(Thread):
    def __init__(self, helper: IOQueue) -> None:
        super().__init__()
        self.__helper = helper
        self.__br_list = []
        print ('CrossVersion created...')

    def __start_browsers(self, vers: tuple[int, int, int]) -> bool:
        self.__stop_browsers()
        self.__br_list.append(Browser('chrome', vers[0]))
        self.__br_list.append(Browser('chrome', vers[1]))
        for br in self.__br_list:
            if not br.setup_browser():
                return False
        return True

    def __stop_browsers(self) -> None:
        for br in self.__br_list: br.kill_browser()
        self.__br_list.clear()

    def __cross_version_test_html(self, html_file: str, save_shot: bool = False) -> Optional[list]:

        img_hashes = []
        for br in self.__br_list:
            hash_v = br.get_hash_from_html(html_file, save_shot)
            if not hash_v: return

            img_hashes.append(hash_v)

        return img_hashes

    def run(self) -> None:

        cur_vers = None
        hpr = self.__helper
        while True:
            vers = hpr.get_vers()
            if not vers: break

            if cur_vers != vers:
                cur_vers = vers
                if not self.__start_browsers(cur_vers):
                    continue
            html_file, _ = hpr.pop_from_queue()

            hashes = self.__cross_version_test_html(html_file)
            if hashes and ImageDiff.diff_images(hashes[0], hashes[1]):
                hpr.update_postq(vers, html_file, hashes)

        self.__stop_browsers()


class Oracle(Thread):
    def __init__(self, helper: IOQueue) -> None:
        super().__init__()
        self.__helper = helper
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
        hpr = self.__helper
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
        self.__helper = helper
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
        hpr = self.__helper
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


class R2Z2:
    def __init__(self, input_version_pair: dict[str, tuple[int, int, int]], output_dir: str, num_of_threads: int):
        self.__ioq = IOQueue(input_version_pair)
        self.__out_dir = output_dir
        self.__num_of_threads = num_of_threads


    def test_wrapper(self, test_class: object):
        threads = []
        for i in range(self.__num_of_threads):
            threads.append(test_class(self.__ioq))

        for th in threads:
            th.start()

        for th in threads:
            th.join()

        self.__ioq.move_to_preqs()

    def process(self):
        self.test_wrapper(CrossVersion)
        self.test_wrapper(Oracle)
        #self.test_wrapper(Bisecter)


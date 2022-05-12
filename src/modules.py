from driver import Browser
from typing import Optional

from helper import IOQueue
from helper import ImageDiff
from threading import Thread

class CrossVersion(Thread):
    def __init__(self, helper: IOQueue) -> None:
        super().__init__()
        self.__helper = helper
        self.__br_list = []

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

    def __start_ref_browser(self, ver: int) -> bool:
        self.__stop_ref_browser()
        self.__ref_br = Browser('chrome', ver)
        return self.__ref_br.setup_browser()

    def __stop_ref_browser(self):
        if self.__ref_br:
            self.__ref_br.kill_browser()
            self.__ref_br = None

    def run(self) -> None:

        cur_mid = None
        hpr = self.__helper
        while True:
            vers = hpr.get_vers()
            if not vers: break

            start, end, ref = vers
            if start >= end: continue

            html_file, hashes = hpr.pop_from_queue()
            if len(hashes) != 2:
                raise ValueError('Something wrong in hashes...')

            # if adjacent (i.e., bisect done)
            if end - start == 1:
                hpr.update_postq(vers, html_file, hashes)
                continue

            mid = (start + end) // 2
            if cur_mid != mid:
                cur_mid = mid
                if not self.__start_ref_browser(cur_mid):
                    continue

            ref_hash = self.__ref_br.get_hash_from_html(html_file)
            if not ref_hash: continue

            if hashes[0] == ref_hash:
                new_vers = (mid, end, ref)
            elif hashes[1] == ref_hash:
                new_vers = (start, mid, ref)
            else:
                continue

            hpr.insert_to_queue(new_vers, html_file, hashes)

        self.__stop_ref_browser()


class R2Z2:
    def __init__(self, vers: tuple[int, int, int], inputs: list, output_dir: str, num_of_threads: int):
        print(inputs)
        self.__ioq = IOQueue(vers, inputs)
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
#        self.test_wrapper(Bisecter)


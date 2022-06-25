from os import environ, getenv
from os.path import dirname, join, abspath, splitext
import time
from pathlib import Path
from helper import ImageDiff
from helper import FileManager

from jshelper import AHEM_FONT, NOSCROLLBAR
from jshelper import ALLSET, RESET, UNSET, NORM, FFAHEM, FAHEM, TEXTAREA 

from selenium import webdriver

from collections import defaultdict

class Browser:
    def __init__(self, browser_type: str, commit_version: int) -> None:
        environ["DBUS_SESSION_BUS_ADDRESS"] = '/dev/null'

        if browser_type == 'chrome':
            options = [
                    '--headless',
                    '--disable-seccomp-sandbox --no-sandbox',
                    '--disable-logging',
                    '--disable-gpu'
                    ]
            self.options = webdriver.chrome.options.Options()

        elif browser_type == 'firefox':
            options = [
                    '--headless',
                    '--disable-gpu'
                    ]
            self.options = webdriver.firefox.options.Options()

        else:
            raise ValueError('[DEBUG] only chrome or firefox are allowed')

        parent_dir = FileManager.get_parent_dir(__file__)
        browser_dir = join(parent_dir, browser_type)
        browser_path = join(browser_dir, str(commit_version), browser_type)
        self.options.binary_location = browser_path

        for op in options: self.options.add_argument(op)

        self.__num_of_run = 0
        self.__browser_type = browser_type

        self.version = commit_version

        self.time = defaultdict(float)
        self.count = defaultdict(int)
        self.flak = defaultdict(int)

    def setup_browser(self):
        self.__num_of_run = 0
        start = time.time()
        for _ in range(10):
            try:
                if self.__browser_type == 'chrome':
                    self.browser = webdriver.Chrome(options=self.options,
                            executable_path=self.options.binary_location + 'driver')
                elif self.__browser_type == 'firefox':
                    self.browser = webdriver.Firefox(options=self.options,
                            executable_path=self.options.binary_location + 'driver')
                else:
                    raise ValueError('Check browser type')
                break

            except Exception as e:
                pass

        WIDTH = getenv('WIDTH')
        WIDTH = 800 if not WIDTH else int(WIDTH)
        HEIGHT = getenv('HEIGHT')
        HEIGHT = 600 if not HEIGHT else int(HEIGHT)
        TIMEOUT = 10

        self.__set_viewport_size(WIDTH, HEIGHT)
        self.browser.set_script_timeout(TIMEOUT)
        self.browser.set_page_load_timeout(TIMEOUT)
        self.browser.implicitly_wait(TIMEOUT)
        self.time['setup'] += time.time() - start
        return True


    def __set_viewport_size(self, width, height):
        window_size = self.browser.execute_script("""
        return [window.outerWidth - window.innerWidth + arguments[0],
          window.outerHeight - window.innerHeight + arguments[1]];
        """, width, height)
        self.browser.set_window_size(*window_size)

    def __screenshot_and_hash(self, name=None):
        try:
            start = time.time()
            if name:
                png = self.browser.get_screenshot_as_png()
                ImageDiff.save_image(name, png)

            else:
                png = self.browser.get_screenshot_as_png()
            self.time['getscreenshot'] += time.time() - start
            self.count['getscreenshot'] += 1

            start = time.time()
            pixels = ImageDiff.get_phash(png)
            self.time['convertscreenshot'] += time.time() - start
            self.count['convertscreenshot'] += 1
            return pixels
        except Exception as e:
            return

    def kill_browser(self):
        if self.browser and self.browser.session_id:
            self.browser.quit()

    def get_source(self):
        try: return '<!DOCTYPE html>\n' + self.browser.page_source
        except: return

    def exec_script(self, scr, arg=None):
        try:
            return self.browser.execute_script(scr, arg)
        except Exception as e:
            return None

    def run_html(self, html_file: str, fn_reduction: bool = False):
        start = time.time()
        if self.__num_of_run % 1000 == 0:
            self.kill_browser()
            self.setup_browser()
        try:
            self.browser.get('file://' + abspath(html_file))
        except Exception as e:
            print ('Error in run_html')
            self.kill_browser()
            self.setup_browser()
            return False
        if fn_reduction:
            s1 = time.time()
            self.exec_script(AHEM_FONT) # baseline
            self.exec_script(ALLSET) # baseline
            self.time['SCRIPT'] += time.time() - s1
        self.time['runhtml'] += time.time() - start
        self.count['runhtml'] += 1
        self.__num_of_run += 1
        return True

    def _get_hash_from_html(self, html_file, save_shot: bool = False, fn_reduction: bool = False):
        ret = self.run_html(html_file, fn_reduction)
        if not ret: return 

        name_noext = splitext(html_file)[0]
        screenshot_name = f'{name_noext}_{self.version}.png' if save_shot else None
        hash_v = self.__screenshot_and_hash(screenshot_name)
        for _ in range(0):
            if ImageDiff.diff_images(hash_v, self.__screenshot_and_hash(screenshot_name)):
                self.flak['BAD'] += 1
                return
        self.flak['TOTAL'] += 1
        return hash_v

    def get_hash_from_html(self, html_file, save_shot: bool = False, fn_reduction: bool = False):
        hash_v = self._get_hash_from_html(html_file, save_shot, fn_reduction)
        for _ in range(0):
            if hash_v is None: 
                self.flak['BAD HTML'] += 1
                print ('bad', html_file)
                return None
            elif ImageDiff.diff_images(hash_v, self._get_hash_from_html(html_file, save_shot, fn_reduction)): 
                self.flak['BAD HTML DIFF'] += 1
                print ('bad diff', html_file)
                return None
        return hash_v


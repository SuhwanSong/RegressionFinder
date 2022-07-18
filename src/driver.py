import time, psutil
from pathlib import Path
from helper import ImageDiff
from helper import FileManager

from selenium import webdriver
from collections import defaultdict

from os import environ, getenv
from os.path import dirname, join, abspath, splitext, exists

from chrome_binary import ensure_chrome_binaries

class Browser:
    def __init__(self, browser_type: str, commit_version: int) -> None:
        environ["DBUS_SESSION_BUS_ADDRESS"] = '/dev/null'

        parent_dir = FileManager.get_parent_dir(__file__)
        browser_dir = join(parent_dir, browser_type)
        if not exists(browser_dir):
            Path(browser_dir).mkdir(parents=True, exist_ok=True)
        browser_path = join(browser_dir, str(commit_version), browser_type)

        if browser_type == 'chrome':
            options = [
                    '--headless',
                    '--disable-seccomp-sandbox',
                    '--disable-logging',
                    '--disable-gpu',
                    ]
            self.options = webdriver.chrome.options.Options()
            ensure_chrome_binaries(browser_dir, commit_version)

        elif browser_type == 'firefox':
            options = [
                    '--headless',
                    '--disable-gpu'
                    ]
            self.options = webdriver.firefox.options.Options()

        else:
            raise ValueError('[DEBUG] only chrome or firefox are allowed')

        self.options.binary_location = browser_path
        for op in options: self.options.add_argument(op)

        self.__num_of_run = 0
        self.__browser_type = browser_type

        self.browser = None
        self.version = commit_version

        self.time = defaultdict(float)
        self.count = defaultdict(int)
        self.flak = defaultdict(int)

    def setup_browser(self):
        self.__num_of_run = 0
        start = time.time()
        self.browser = None
        for _ in range(5):
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
                continue

        # System crashes if fails to start browser.
        if self.browser is None:
            sys.exit(f"Browser {version} fails to start..")
        WIDTH = getenv('WIDTH')
        WIDTH = 800 if not WIDTH else int(WIDTH)
        HEIGHT = getenv('HEIGHT')
        HEIGHT = 300 if not HEIGHT else int(HEIGHT)
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


    def get_screenshot(self):
        for attempt in range(5):
            if attempt == 4:
                self.kill_browser()
                self.setup_browser()
            try:
                png = self.browser.get_screenshot_as_png()
                return png
            except Exception as e:
                continue

        return None 

    def __screenshot_and_hash(self, name=None):
        start = time.time()
        png = self.get_screenshot()
        if name:
            ImageDiff.save_image(name, png)
        pixels = ImageDiff.get_phash(png)
        return pixels

    def kill_browser(self):
        if self.browser and self.browser.session_id:
            try:
                self.browser.close()
                self.browser.quit()
            except:
                return False

        return True

    def kill_browser_by_pid(self):
        if not self.browser: 
            return False
        br = self.browser
        if not br.session_id or not br.service or not br.service.process:
            return False
        try:
            p = psutil.Process(br.service.process.pid)
            for proc in p.children(recursive=True):
                proc.kill()
        except Exception as e:
            pass
        return True

    def get_source(self):
        try: return '<!DOCTYPE html>\n' + self.browser.page_source
        except: return

    def exec_script(self, scr, arg=None):
        try:
            return self.browser.execute_script(scr, arg)
        except Exception as e:
            return None

    def repeatly_run(self, html_file):
        for attempt in range(5):
            if attempt == 4:
                self.kill_browser()
                self.setup_browser()
            try:
                self.browser.get('file://' + abspath(html_file))
                return 
            except Exception as e:
                continue

        return None 

    def run_html(self, html_file: str):
        if self.__num_of_run == 1000:
            self.kill_browser()
            self.setup_browser()
        self.repeatly_run(html_file)
        self.__num_of_run += 1
        return True

    def clean_html(self):
        self.browser.get('about:blank')

    def get_hash_from_html(self, html_file, save_shot: bool = False):
        ret = self.run_html(html_file)
        if not ret: return 

        name_noext = splitext(html_file)[0]
        screenshot_name = f'{name_noext}_{self.version}.png' if save_shot else None
        hash_v = self.__screenshot_and_hash(screenshot_name)
        return hash_v

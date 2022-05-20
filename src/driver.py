from os.path import dirname, join, abspath, splitext

from pathlib import Path
from helper import ImageDiff
from helper import FileManager

from jshelper import JSCODE
from selenium import webdriver


class Browser:
    def __init__(self, browser_type: str, commit_version: int) -> None:
        if browser_type == 'chrome':
            options = [
                    '--headless',
                    '--disable-seccomp-sandbox --no-sandbox',
                    '--disable-logging',
#                    '--disable-gpu'
                    ]
            self.options = webdriver.chrome.options.Options()

        elif browser_type == 'firefox':
            options = [
                    '--headless'
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

    def setup_browser(self):
        self.__num_of_run = 0
        try:
            if self.__browser_type == 'chrome':
                self.browser = webdriver.Chrome(options=self.options,
                        executable_path=self.options.binary_location + 'driver')

            elif self.__browser_type == 'firefox':
                self.browser = webdriver.Firefox(options=self.options,
                        executable_path=self.options.binary_location + 'driver')

            else:
                raise ValueError('Check browser type')
        except Exception as e:
            print ('setup_browser', e)
            return False

        WIDTH  = 1024
        HEIGHT = 500
        TIMEOUT = 10

        self.__set_viewport_size(WIDTH, HEIGHT)
        self.browser.set_script_timeout(TIMEOUT)
        self.browser.set_page_load_timeout(TIMEOUT)
        self.browser.implicitly_wait(TIMEOUT)

        #print (f'{self.__browser_type} {self.version} starts ...')
        return True


    def __set_viewport_size(self, width, height):
        window_size = self.browser.execute_script("""
        return [window.outerWidth - window.innerWidth + arguments[0],
          window.outerHeight - window.innerHeight + arguments[1]];
        """, width, height)
        self.browser.set_window_size(*window_size)

    def __screenshot_and_hash(self, name=None):
        try:
            if name:
                self.browser.save_screenshot(name)
                png = name
            else:
                png = self.browser.get_screenshot_as_png()
            return ImageDiff.get_phash(png)
        except Exception as e:
            #print('screenshot_and_hash', e)
            return

    def kill_browser(self):
        if self.browser and self.browser.session_id:
            self.browser.quit()

    def get_source(self):
        try: return self.browser.page_source
        except: return

    def exec_script(self, scr, arg=None):
        try:
            return self.browser.execute_script(scr, arg)
        except:
            return None

    def run_html(self, html_file):
        try:
            self.browser.get('file://' + abspath(html_file))
        except Exception as e:
            print ('run_html', e)
            self.kill_browser()
            self.setup_browser()
            return False
        self.exec_script(JSCODE)
        self.exec_script('trigger();')
        self.__num_of_run += 1
        return True

    def get_hash_from_html(self, html_file, save_shot: bool = False):
        if not self.run_html(html_file): return
        
        #save_shot = True
        name_noext = splitext(html_file)[0]
        screenshot_name = f'{name_noext}_{self.version}.png' if save_shot else None
        
        hash_v = self.__screenshot_and_hash(screenshot_name)
        if not hash_v: return

        for _ in range(2):
            if hash_v != self.__screenshot_and_hash(screenshot_name):
                return
        return hash_v

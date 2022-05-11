from r2z2 import ThreadHelper
from r2z2 import CrossVersion
from jshelper import REDUCER

class Minimizer(CrossVersion):
    def __init__(self, helper: ThreadHelper, old_chrome_path: str, new_chrome_path: str) -> None:
        CrossVersion.__init__(self, helper, old_chrome_path, new_chrome_path)

    def __minimize_dom(self, html_file: str) -> None:
        br = self.br_list[-1]
        br.run_html(html_file)
        pass

    def run(self) -> None:
        self.__start()

        th = self.__thread_helper
        while True:
            th.lock.acquire()
            if th.queue.empty():
                th.lock.release()
                break

            html_file = th.queue.get()
            th.lock.release()

            if not self.__test_html(html_file): continue

            # TODO

        self.__terminate()

import os
import sys

import shutil
import tempfile
import requests

from pathlib import Path
from bs4 import BeautifulSoup

def get_commit_from_position(position):
    URL = 'https://crrev.com/' + str(position)
    response = requests.get(URL)
    if response.status_code == 404:
        print(response.status_code)
        return 0
    else:
        soup = BeautifulSoup(response.text, "lxml")
        title = soup.title.string.split(' - ')[0]
        return title

def build_chrome_binary(revision):
    revision = str(revision)
    if not os.path.exists(revision): 
        try:
            commit = get_commit_from_position(revision)
            cur_path = os.path.dirname(os.path.abspath(__file__))
            br_build = os.path.join(cur_path, 'build_chrome.sh')

            if commit != 0:
                command = f'{br_build} {commit} {revision}'
                print (command)
                ret = os.system(command)
        except Exception as e:
            print("exception", e)
    else:
        print("pass " + revision)


class ChromeBinary:
    def __init__(self):
        platform = sys.platform

        # linux, mac (x64 or arm) We currently use the x64 binaries on arm
        # instead of using the arm-specific binaries.
        platform_names = {'linux': 'Linux_x64', 'darwin': 'Mac'}
        chrome_binaries = {'linux': 'chrome-linux', 'darwin': 'chrome-mac'}
        chrome_driver_binaries = {'linux': 'chromedriver_linux64', 'darwin': 'chromedriver_mac64'}

        self.platform_name = platform_names[platform]
        self.chrome_binary = chrome_binaries[platform]
        self.chrome_driver_binary = chrome_driver_binaries[platform]

        self.url_prefix = "https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/"

    def get_chromium_binary_download_url(self, revision):
        return self.url_prefix + f"{self.platform_name}%2F{revision}%2F{self.chrome_binary}.zip?alt=media"

    def get_chromium_driver_download_url(self, revision):
        return self.url_prefix + f"{self.platform_name}%2F{revision}%2F{self.chrome_driver_binary}.zip?alt=media"


    # Ensures chrome binaries (chrome + chromedriver) exist in path/revision/. If
    # they do not exist, they will be downloaded. This function returns True if the
    # binaries exist.
    def ensure_chrome_binaries(self, path, revision):
        def download(url, name, base="."):
            try:
                r = requests.request("GET", url)
                r.raise_for_status()
                with open(os.path.join(base, name), "wb") as f:
                    for chunk in r:
                        f.write(chunk)
                return True
            except Exception as e:
                return False

        revision = str(revision)
        binary_dir_path = os.path.join(path, revision)
        if os.path.exists(binary_dir_path):
            return True

        # Multiple threads may call this function simultaneously. To prevent races,
        # a temporary directory is used for downloading, and an atomic rename is
        # used to update the binaries once they are available.
        with tempfile.TemporaryDirectory() as outdir:
            print(f"downloading chrome {revision} at {outdir}")
            url = self.get_chromium_binary_download_url(revision)
            filename = f'{revision}.zip'
            filename_path = os.path.join(outdir, filename)
            ret = download(url, filename, outdir)
            if not ret:
                raise ValueError("Failed to download chrome binary at " + url)
            os.system(f'unzip -q {filename_path} -d {outdir}')
            url = self.get_chromium_driver_download_url(revision)
            filename = f'{revision}-driver.zip'
            filename_path = os.path.join(outdir, filename)
            ret = download(url, filename, outdir)
            if not ret:
                raise ValueError("Failed to download chromedriver binary at " + url)

            os.system(f'unzip -q {filename_path} -d {outdir}')
            tmp_outdir = os.path.join(outdir, self.chrome_binary)
            tmp_driver_path = os.path.join(outdir, self.chrome_driver_binary, 'chromedriver')
            os.rename(tmp_driver_path, os.path.join(tmp_outdir, 'chromedriver'))
            os.rename(tmp_outdir, os.path.join(path, revision))
        return True

import os
import sys

import shutil
import tempfile
import requests

from pathlib import Path
from bs4 import BeautifulSoup

def get_chromium_binary_download_url(position):
    url = f"https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F{position}%2Fchrome-linux.zip?alt=media"
    return url

def get_chromium_driver_download_url(position):
    url = f"https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F{position}%2Fchromedriver_linux64.zip?alt=media"
    return url

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


# This function will download chrome revision and
# use os.rename to avoid concurrency issues
def download_chromium_position(outdir, position):
    if not position:
        print("[-] Version is not correct :(")
        return 1

    url = get_chromium_binary_download_url(position)
    name = os.path.join(outdir, f'{position}.zip')
    ret = download(url, name)
    if not ret:
        print("[-] No pre-built binary :(")
        return 1

    os.system(f'unzip -q {name} -d {outdir}')

    url = get_chromium_driver_download_url(position)
    name = os.path.join(outdir, f'{position}-driver.zip')
    ret = download(url, name)
    if not ret:
        print("[-] No pre-built binary :(")
        return 1

    os.system(f'unzip -q {name} -d {outdir}')

    tmp_outdir = os.path.join(outdir, 'chrome-linux')
    tmp_driver_path = os.path.join(outdir, 'chromedriver_linux64', 'chromedriver')
    os.rename(tmp_driver_path, os.path.join(tmp_outdir, 'chromedriver'))
    os.rename(tmp_outdir, str(position))
    return 0

def get_commit_from_position(position):
    URL = 'https://crrev.com/' + str(position)
    response = requests.get(URL)
    if response.status_code == 404:
        print(response.status_code)
        return 0
    else:
        soup = BeautifulSoup(response.text, "lxml")
        title = soup.title.string.split(' - ')[0]
        print (title)
        return title

def download_chrome_binary(tar, pos):
    pos = str(pos)
    cur = os.getcwd()
    os.chdir(tar)
    if os.path.exists(pos): 
        return 
    try:
        with tempfile.TemporaryDirectory() as outdir:
            commit = get_commit_from_position(pos)
            if commit:
                print("downloading " + pos)
                ret = download_chromium_position(outdir, pos)
    except Exception as e:
        print("exception", e)
    os.chdir(cur)

def build_chrome_binary(pos):
    pos = str(pos)
    if not os.path.exists(pos): 
        try:
            commit = get_commit_from_position(pos)
            cur_path = os.path.dirname(os.path.abspath(__file__))
            br_build = os.path.join(cur_path, 'build_chrome.sh')

            if commit != 0:
                command = f'{br_build} {commit} {pos}'
                print (command)
                ret = os.system(command)
        except Exception as e:
            print("exception", e)
    else:
        print("pass " + pos)

import os
import sys

import shutil
import subprocess
import tempfile
import requests

from pathlib import Path


class FirefoxBinary:
    def __init__(self):
        self.__drivername = 'geckodriver'
        platform = sys.platform

        platform_names = {'linux': 'linux-x86_64', 'darwin': 'mac'}
        firefox_binaries = {'linux': 'firefox-', 'darwin': 'Firefox '}
        firefox_exts = {'linux': '.tar.bz2', 'darwin': '.pkg'}
        gecko_binaries = {'linux': 'linux64', 'darwin': 'macos'}

        firefox_dirpaths = {'linux': 'firefox', 'darwin': 'Firefox.app'}
        firefox_filepaths = {'linux': 'firefox', 'darwin': 'Contents/MacOS/firefox'}

        self.__platform_name = platform_names[platform]
        self.__firefox_binary = firefox_binaries[platform]
        self.__firefox_ext = firefox_exts[platform]
        self.__gecko_binary = gecko_binaries[platform]

        self.__firefox_dirpath = firefox_dirpaths[platform]
        self.__firefox_filepath = firefox_filepaths[platform]

    def __get_firefox_binary_download_url(self, version):
        platform = sys.platform
        prefix = "https://ftp.mozilla.org/pub/firefox/releases/"
        firefox_filepath = f"{self.__firefox_binary}{version}{self.__firefox_ext}"
        return prefix + f"{version}/{self.__platform_name}/en-US/{firefox_filepath}"

    def __get_geckodriver_download_url(self):
        platform = sys.platform
        prefix = "https://github.com/mozilla/geckodriver/releases/download/v0.31.0/"
        gecko_filename = f'{self.__drivername}-v0.31.0-{self.__gecko_binary}.tar.gz'
        return prefix + gecko_filename

    # Ensures firefox binaries (firefox + geckodriver) exist in path/revision/.
    # If they do not exist, they will be downloaded. This function returns True
    # if the binaries exist.
    def ensure_firefox_binaries(self, path, version):
        def download(url, base="."):
            local_filename = url.split('/')[-1]
            try:
                r = requests.request("GET", url)
                r.raise_for_status()
                with open(os.path.join(base, local_filename), "wb") as f:
                    for chunk in r:
                        f.write(chunk)
                return True
            except Exception as e:
                return False

        def unzip_tar(file, path):
            os.system(f"tar -xf {file} -C {path}")

        def unzip_firefox(file, path):
            platform = sys.platform
            if platform == "linux":
                unzip_tar(file, path)
            elif platform == "darwin":
                prev = os.getcwd()
                script = ['tar', '-xf', file, '-C', path]
                subprocess.call(script)
                os.chdir(path)
                os.system(f"cat Firefox.tmp1.pkg/Payload | gunzip -dc | cpio -i")
                os.chdir(prev)
            else:
                raise ValueError("")

        def unzip_driver(file, path):
            unzip_tar(file, path)

        # Multiple threads may call this function simultaneously. To prevent races,
        # a temporary directory is used for downloading, and an atomic rename is
        # used to update the binaries once they are available.
        with tempfile.TemporaryDirectory() as outdir:
            print(f"downloading firefox {version} at {outdir}")
            url = self.__get_firefox_binary_download_url(version)
            filename = url.split('/')[-1]
            ret = download(url, outdir)
            if not ret:
                raise ValueError("Failed to download firefox binary at " + url)
            unzip_firefox(os.path.join(outdir, filename), outdir)

            url = self.__get_geckodriver_download_url()
            filename = url.split('/')[-1]
            ret = download(url, outdir)
            if not ret:
                raise ValueError("Failed to download geckodriver at " + url)
            unzip_driver(os.path.join(outdir, filename), outdir)
            firefox_tmpdir = os.path.join(outdir, self.__firefox_dirpath)
            os.rename(os.path.join(outdir, self.__drivername),
                      os.path.join(firefox_tmpdir, self.__drivername))

            os.rename(firefox_tmpdir, os.path.join(path, version))

    def get_browser_path(self, path, version):
        return os.path.join(path, version, self.__firefox_filepath)

    def get_driver_path(self, path, version):
        return os.path.join(path, version, self.__drivername)

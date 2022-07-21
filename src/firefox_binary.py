import os
import sys

import shutil
import tempfile
import requests

from pathlib import Path


class FirefoxBinary:
    def __init__(self):
        self.__drivername = 'geckodriver'

    def __get_firefox_binary_download_url(self, version):
        platform = sys.platform
        prefix = "https://ftp.mozilla.org/pub/firefox/releases/"
        platform_names = {'linux': 'linux-x86_64', 'darwin': 'mac'}
        firefox_binaries = {'linux': 'firefox-', 'darwin': 'Firefox '}
        firefox_exts = {'linux': '.tar.bz2', 'darwin': '.pkg'}
        firefox_filename = f"{firefox_binaries[platform]}{version}{firefox_exts[platform]}"
        return prefix + f"{version}/{platform_names[platform]}/en-US/{firefox_filename}"

    def __get_geckodriver_download_url(self):
        platform = sys.platform
        gecko_binaries = {'linux': 'linux64', 'darwin': 'macos'}
        prefix = "https://github.com/mozilla/geckodriver/releases/download/v0.31.0/"
        gecko_filename = f'{self.__drivername}-v0.31.0-{gecko_binaries[platform]}.tar.gz'
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

        def unzip(file, path):
            ext = os.path.splitext(file)[1]
            if '.pkg' == ext:
                os.system(f"xar -xf {file} {path}")
            else:
                os.system(f"tar -xf {file} -C {path}")

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
            unzip(os.path.join(outdir, filename), outdir)

            url = self.__get_geckodriver_download_url()
            filename = url.split('/')[-1]
            ret = download(url, outdir)
            if not ret:
                raise ValueError("Failed to download geckodriver at " + url)
            unzip(os.path.join(outdir, filename), outdir)

            firefox_tmpdir = os.path.join(outdir, 'firefox')
            os.rename(os.path.join(outdir, self.__drivername),
                      os.path.join(firefox_tmpdir, self.__drivername))

            os.rename(firefox_tmpdir, os.path.join(path, version))

    def get_browser_path(self, path, version):
        return os.path.join(path, version, 'firefox')

    def get_driver_path(self, path, version):
        return os.path.join(path, version, self.__drivername)

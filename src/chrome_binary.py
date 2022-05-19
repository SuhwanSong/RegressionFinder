import requests
import os
import sys

from bs4 import BeautifulSoup

def get_chromium_binary_download_url(position):
    url = f"https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F{position}%2Fchrome-linux.zip?alt=media"
    return url

def get_chromium_binary_name_position(position):
    name = f"{position}-chrome-linux.zip"
    return name

def get_chromium_driver_download_url(position):
    url = f"https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F{position}%2Fchromedriver_linux64.zip?alt=media"
    return url

def get_chromium_driver_name_position(position):
    name = f"{position}-chromedriver-linux64.zip"
    return name

def download(url, name, base="."):
    r = requests.request("GET", url)

    try:
        r.raise_for_status()
        with open(os.path.join(base, name), "wb") as f:
            for chunk in r:
                f.write(chunk)
        return True
    except:
        return False

def download_chromium_position(position):
    if not position:
        print("[-] Version is not correct :(")
        return 1

    url = get_chromium_binary_download_url(position)
    name = get_chromium_binary_name_position(position)
    try:
        ret = download(url, name)
    except:
        return 1
    if not ret:
        print("[-] No pre-built binary :(")
        return 1
   
    os.system(f"unzip {name} &> /dev/null")
    os.system(f"mv chrome-linux {position} &> /dev/null")
    os.system(f"rm -rf {name} &> /dev/null")

    url = get_chromium_driver_download_url(position)
    name = get_chromium_driver_name_position(position)
    try:
        ret = download(url, name)
    except:
        return 1
    
    if not ret:
        print("[-] No pre-built binary :(")
        return 1

    os.system(f"unzip {name} &> /dev/null")
    os.system(f"mv chromedriver_linux64/chromedriver {position} &> /dev/null")
    os.system(f"rm -rf chromedriver_linux64 {name} &> /dev/null")
    
    return 0

def get_commit_from_position(position):
    URL = 'https://crrev.com/' + position
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
    if not os.path.exists(pos): 
        try:
            commit = get_commit_from_position(pos)
            if commit != 0:
                print("downloading " + pos)
                ret = download_chromium_position(pos)
        except Exception as e:
            print("exception", e)
    else:
        print("pass " + pos)

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



def main():
    tar = sys.argv[1]
    pos = sys.argv[2]
    download_chrome(tar, pos)
    return 0


if __name__ == "__main__":
    ret = main()
    exit(ret)

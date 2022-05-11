import sys
import os
import requests
import json

def get_chromium_base_position(version):
    url = "https://omahaproxy.appspot.com/deps.json"

    querystring = {"version":version}

    r = requests.request("GET", url, params=querystring)

    try:
        r.raise_for_status()
        return json.loads(r.text)['chromium_base_position']
    except:
        return None

def get_chromium_binary_download_url(position):
    url = f"https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F{position}%2Fchrome-linux.zip?alt=media"
    return url

def get_chromium_binary_name(version, position):
    name = f"{version}-{position}-chrome-linux.zip"
    return name

def get_chromium_binary_name_position(position):
    name = f"{position}-chrome-linux.zip"
    return name

def get_chromium_driver_download_url(position):
    url = f"https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F{position}%2Fchromedriver_linux64.zip?alt=media"
    return url

def get_chromium_driver_name(version, position):
    name = f"{version}-{position}-chromedriver-linux64.zip"
    return name

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

def download_chromium(version):
    position = get_chromium_base_position(version)
    if not position:
        print("[-] Version is not correct :(")
        return 1

    url = get_chromium_binary_download_url(position)
    name = get_chromium_binary_name(version, position)
    ret = download(url, name)
    if not ret:
        print("[-] No pre-built binary :(")
        return 1

    url = get_chromium_driver_download_url(position)
    name = get_chromium_driver_name(version, position)
    ret = download(url, name)
    
    if not ret:
        print("[-] No pre-built binary :(")
        return 1
    
    return 0

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
   
    os.system("unzip " + name)
    os.system("mv chrome-linux " + position)
    os.system("rm -rf " + name)

    url = get_chromium_driver_download_url(position)
    name = get_chromium_driver_name_position(position)
    try:
        ret = download(url, name)
    except:
        return 1
    
    if not ret:
        print("[-] No pre-built binary :(")
        return 1

    os.system("unzip " + name)
    os.system("mv chromedriver_linux64/chromedriver " + position)
    os.system("rm -rf chromedriver_linux64 " + name)
    
    return 0


def main(argv):
    ret = download_chromium(argv[1])
    return ret

if __name__ == "__main__":
    ret = main(sys.argv)
    exit(ret)

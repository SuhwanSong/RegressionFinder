import requests
import json
import time
import os
import sys

import download_chromium

def get_chromium_tags():
    url = "https://api.github.com/repos/chromium/chromium/git/refs/tags"
    r = requests.request("GET", url)

    try:
        r.raise_for_status()
        data = json.loads(r.text)
        return ['/'.join(item['ref'].split('/')[2:]) for item in data]
    except:
        return None

def sort_tags(tags):
    result = {}
    for tag in tags:
        if "." in tag:
            try:
                major = int(tag.split(".")[0])
            except:
                major = '-'
        else:
            major = '-'
        if major not in result:
            result[major] = []
        result[major].insert(0, tag)
    return result

def get_commit_from_position(position):
    URL = 'https://crrev.com/' + position
    response = requests.get(URL)
    if response.status_code == 404:
        print(response.status_code)
        return 0
    else:
        a = 66
        b = 40
        print(response.text[a:a+1+b])
        return str(response.text[a:a+1+b])


#def main():
#    tags = get_chromium_tags()
#    tag_map = sort_tags(tags)
#
#    for i in range(84, 85+1):
#        if i == 82: continue
#        for tag in tag_map[i]:
#            print(f"Try download {tag} version")
#            ret = download_chromium.download_chromium(tag)
##            if ret == 0:
##                break
#            time.sleep(0.1)
#    return 0

def main():
#    tags = get_chromium_tags()
#    tag_map = sort_tags(tags)

    dir_list = os.listdir()
    dir_list.sort()
    check = "check"

    start = int(sys.argv[1])

    for i in range(start, start + 1):
        pos = str(i)
        if not os.path.exists(pos): 
            try:
                commit = get_commit_from_position(pos)
                if commit == 0: continue
                ret = download_chromium.download_chromium_position(pos)
                print("downloading " + pos)
            except:
                print("exception")
        else:
            print("pass " + pos)

    return 0

if __name__ == "__main__":
    ret = main()
    exit(ret)

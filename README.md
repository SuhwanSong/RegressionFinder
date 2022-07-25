# [Intern Project] RegressionFinder

An automatic tool which finds regressions in Chrome browser.

## Table                                                                                     
1. [Setup](#Setup)    
2. [Tutorial](#Tutorial)                                                                                                       

## Setup
- You need to install the dependencies of RegressionFinder.
- The bash file `setup.sh` will install all of dependencies.

```shell
$ git clone https://github.com/SuhwanSong/RegressionFinder.git
$ cd RegressionFinzer
$ ./setup.sh
```

## Tutorial
- First, you need to generate the html files.

```shell
$ cd RegressionFinder/src/domato
$ python3 generator.py --output_dir ./html_testcases --no_of_files 10000
```
* This will generate 10,000 testcases in `./html_testcases` directory. 
* Now you can run RegressionFinder with `r2z2.py`.
* It provides eight options:
  * -b: The base version of Chrome (e.g., 87)
  * --base-flags: The flags for base Chrome (e.g., "")
  * -t: The target version of Chrome (e.g., 88)
  * --target-flags: The flags for target Chrome (e.g., "--enable-blink-features=LayoutNG")
  * -f: The version of Firefox (e.g., 101.0)
  * -i: The html testcase directory
  * -o: The output directory
  * -j: The number of threads

- Move to `RegressionFinder/src` directory and run the following command:
```shell
$ python3 r2z2.py -b 87 -t 88 -f 101.0 -i ./domato/html_testcases -o ./results -j 4
```

- Or if you want to test specific flags, run the following command:
```shell
$ python3 r2z2.py -b 87 --base-flags="" -t 87 --target-flags="--enable-blink-features=LayoutNG" \ 
  -f 101.0 -i ./domato/html_testcases -o ./results -j 4
```

- When the run is done, you can check the result at `./results` directory.
```
$ ls ./results
Bisecter  CrossVersion  Minimizer  Oracle  Report
```

- Final result is stored in `Report` directory.
- The bug html testcases with their screenshots are grouped by their bug commit revision. 
- The revision range url is saved in `changelog.txt` file.
```shell
$ ls ./results/Report
800521  802388  803746  805192  805372  806660

$ ls ./results/Report/806660
13-0007482-min_806657.png  13-0007482-min_806660.png  13-0007482-min_101.0.png  13-0007482-min.html  changelog.txt

$ cat ./results/Report/806660/changelog.txt
https://chromium.googlesource.com/chromium/src/+log/834b0fa2668edc7d06f50da5b1a5ace2337c4367..b5590351a10c17d1522c0fef47fe66a86087ea10
```

* Other directories have the intermediate result of each stage:
  * `CrossVersion` contains the html testcases which are differently rendered on base and target Chrome browsers.
  * `Minimizer` contains the minimized html testcases.
  * `Oracle` contains the html testcases in which Firefox and base Chrome render the same.
  * `Bisecter` contains the html testcases which are correctly bisected (i.e., pinpointed to bug commit).



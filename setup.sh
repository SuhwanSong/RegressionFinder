#! /bin/bash
set -o xtrace

CUR_DIR="$( cd "$(dirname "$0")" ; pwd -P )"
SRC_DIR=$CUR_DIR/src/
TOL_DIR=$CUR_DIR/tools/
DAT_DIR=$CUR_DIR/data

function build_chromium(){
  # Clone depot_tools
  if [ ! -e $TOL_DIR/depot_tools ]; then
    pushd $TOL_DIR
    git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git
    popd
  fi
  export PATH="$PATH:$TOL_DIR/depot_tools"

  if [ ! -e $TOL_DIR/wpt ]; then
    pushd $TOL_DIR
    git clone https://github.com/web-platform-tests/wpt.git
    popd
  fi
  # chromium
  mkdir -p chrome && cd chrome

  # Run the fetch tool from depot_tools to check out the code and its dependencies.
  if [ ! -e $CUR_DIR/chrome/src ]; then
    fetch --nohooks chromium

    # Install additional build dependencies
    cd src
    ./build/install-build-deps.sh
    # Run the hooks
    gclient runhooks
  fi
}

# make directories
mkdir -p $CUR_DIR/firefox
mkdir -p $CUR_DIR/chrome
mkdir -p $TOL_DIR

# install dep
pip3 install imagehash
pip3 install selenium
pip3 install pillow
pip3 install beautifulsoup4
pip3 install requests
pip3 install PyVirtualDisplay
pip3 install deepdiff


# Determine the archive to use. For now, only Mac64 and Linux64 are supported.
archive=$([ "$(uname)" == "Darwin" ] && echo "mac64" || echo "linux64")

# download versions
pushd $DAT_DIR
python3 bisect-builds.py -a $archive --use-local-cache
popd

build_chromium

#!/bin/bash
CUR_DIR="$( cd "$(dirname "$0")" ; pwd -P )"/..
CHM_DIR=$CUR_DIR/chrome/src
TOL_DIR=$CUR_DIR/tools/
export PATH="$PATH:$TOL_DIR/depot_tools"

GIT_VER=$1
BRV=$2

pushd $CHM_DIR
git checkout -f $GIT_VER || exit 1
git reset --hard
COMMIT_DATE=$(git log -n 1 --pretty=format:%ci)

pushd $TOL_DIR/depot_tools
git checkout $(git rev-list -n 1 --before="$COMMIT_DATE" master) || exit 1
export DEPOT_TOOLS_UPDATE=0
git clean -ffd
popd

echo $PWD

#gclient sync -D --force --reset
gclient sync -D 
./build/install-build-deps.sh
sudo apt-get install python -y 
gclient runhooks

gn gen out/Release
#cp $CUR_DIR/build/args.gn out/Release
#gn gen out/Release
autoninja -C out/Release chrome

rm -rf out/$GIT_VER
cp -r out/Release out/$GIT_VER


gn gen out/chromedriver
autoninja -C out/chromedriver chromedriver

rm -rf out/$GIT_VER/chrd
cp -r out/chromedriver out/$GIT_VER/chrd


mkdir $CUR_DIR/chrome/$BRV
ln -s `pwd`/out/$GIT_VER/chrome $CUR_DIR/chrome/$BRV/chrome
ln -s `pwd`/out/$GIT_VER/chrd/chromedriver $CUR_DIR/chrome/$BRV/chromedriver

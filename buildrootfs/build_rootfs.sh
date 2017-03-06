#!/bin/bash
#
# Skia < skia AT libskia DOT so >
#
# Beerware licensed software - 2017
#

BASE="$(pwd)"
OUTPUT="$BASE/output"
BUILDROOT_ROOT_PATH="$BASE/../../buildroot/"
BUILDROOT_LOG="$BASE/buildroot.log"
BUSYBOX_DEFCONFIG="$BASE/busybox_defconfig"
OVERLAY="$BASE/overlay"
TEST_REPO="file://$HOME/workspace/custom_tests"
TEST_FOLDER="$OVERLAY/tests"

TMP_DEFCONFIG="/tmp/buildroot_defconfig"


cd $OVERLAY
echo "Cleaning old tests"
test -d $TEST_FOLDER&&rm -rf $TEST_FOLDER
echo "Fetching latest tests"
git clone $TEST_REPO $TEST_FOLDER
echo "Remove .git folder to save some space"
rm -rf $TEST_FOLDER/.git

cd $BUILDROOT_ROOT_PATH

cp "$BASE/buildroot_defconfig" $TMP_DEFCONFIG

echo "BR2_PACKAGE_BUSYBOX_CONFIG=\"$BUSYBOX_DEFCONFIG\"" >> $TMP_DEFCONFIG
echo "BR2_ROOTFS_OVERLAY=\"$OVERLAY\"" >> $TMP_DEFCONFIG
test -d $OVERLAY||mkdir $OVERLAY

export BR2_DEFCONFIG="$TMP_DEFCONFIG"

echo "Moving to buildroot folder: $BUILDROOT_ROOT_PATH"
echo "Launching Buildroot" > $BUILDROOT_LOG
make defconfig >> $BUILDROOT_LOG 2>&1
make -j 4 >> $BUILDROOT_LOG 2>&1
if [ "$?" != 0 ]; then
    echo "Build failed, see $BUILDROOT_LOG"
    exit 1
fi
echo "Build finished!"

cd $BASE
echo "Copying files to output:"
test -d $OUTPUT||mkdir $OUTPUT
cp $BUILDROOT_ROOT_PATH/output/images/* $OUTPUT/
echo "Your files are here: $OUTPUT/"



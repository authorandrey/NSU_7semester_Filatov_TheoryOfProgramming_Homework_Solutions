#!/bin/bash

set -euxo pipefail

echo "VERSION=$VERSION"

export TARGET_DIR=rasp-machine-emulator-$VERSION
rm -rf $TARGET_DIR
mkdir $TARGET_DIR
cp ./target/scala-2.13/rasp-machine-emulator-assembly-$VERSION.jar $TARGET_DIR/rasp-machine-emulator.jar
cp -r samples $TARGET_DIR/samples

cd $TARGET_DIR
zip -r rasp-machine-emulator-$VERSION.zip *

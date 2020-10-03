#!/usr/bin/env bash

OLD_CWD=$(pwd)
cd .. || exit

echo "BUILDING LINUX PLUGIN"
scons platform=linux -j8 bits=64 target=release
mkdir -p project/bin/x11/
mv godot-cpp/bin/x11/* project/bin/x11/

cd "$OLD_CWD" || exit

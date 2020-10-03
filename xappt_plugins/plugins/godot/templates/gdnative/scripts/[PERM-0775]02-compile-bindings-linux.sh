#!/usr/bin/env bash

OLD_CWD=$(pwd)
cd ../godot-cpp || exit

echo "BUILDING LINUX BINDINGS"
scons platform=linux generate_bindings=yes -j8 bits=64 use_custom_api_file=../api.json target=debug
scons platform=linux generate_bindings=yes -j8 bits=64 use_custom_api_file=../api.json target=release

#echo "BUILDING ANDROID BINDINGS"
#scons platform=android generate_bindings=yes -j8 bits=64 use_custom_api_file=../api.json target=release android_arch=armv7
#scons platform=android generate_bindings=yes -j8 bits=64 use_custom_api_file=../api.json target=release android_arch=arm64v8
#scons platform=android generate_bindings=yes -j8 bits=64 use_custom_api_file=../api.json target=release android_arch=x86
#scons platform=android generate_bindings=yes -j8 bits=64 use_custom_api_file=../api.json target=release android_arch=x86_64

cd "$OLD_CWD" || exit

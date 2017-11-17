#!/usr/bin/env python3

# The MIT License (MIT)
#
# Copyright (c) 2016 Scott Shawcroft for Adafruit Industries
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import os
import os.path
import shlex
import shutil
import sys
import subprocess
import zipfile

import circuitpython_build_tools


def add_file(bundle, src_file, zip_name):
    bundle.write(src_file, zip_name)
    file_size = os.stat(src_file).st_size
    file_sector_size = file_size
    if file_size % 512 != 0:
        file_sector_size = (file_size // 512 + 1) * 512
    print(zip_name, file_size, file_sector_size)
    return file_sector_size


def build_bundle(lib_location, bundle_version, output_filename,
                 mpy_cross=None):
    build_dir = "build-" + output_filename
    build_lib_dir = os.path.join(build_dir, "lib")
    if os.path.isdir(build_dir):
        print("Deleting existing build.")
        shutil.rmtree(build_dir)
        os.mkdir(build_dir)
        os.mkdir(build_lib_dir)

    success = True
    total_size = 512
    for subdirectory in os.listdir("libraries"):
        for library in os.listdir(os.path.join("libraries", subdirectory)):
            library_path = os.path.join("libraries", subdirectory, library)

            circuitpython_build_tools.build_library(library_path,
                                                    build_lib_dir,
                                                    mpy_cross=mpy_cross)

    with open(os.path.join(build_lib_dir, "VERSIONS.txt"), "w") as f:
        f.write(bundle_version + "\r\n")
        versions = subprocess.run('git submodule foreach \"git remote get-url origin && git describe --tags\"', shell=True, stdout=subprocess.PIPE)
        repo = None
        for line in versions.stdout.split(b"\n"):
            if line.startswith(b"Entering") or not line:
                continue
            if line.startswith(b"git@"):
                repo = b"https://github.com/" + line.split(b":")[1][:-len(".git")]
            elif line.startswith(b"https:"):
                repo = line.strip()[:-len(".git")]
            else:
                f.write(repo.decode("utf-8", "strict") + "/releases/tag/" + line.strip().decode("utf-8", "strict") + "\r\n")

    with zipfile.ZipFile(output_filename, 'w') as bundle:
        total_size += add_file(bundle, "README.txt", "lib/README.txt")
        for filename in os.listdir("update_scripts"):
            src_file = os.path.join("update_scripts", filename)
            total_size += add_file(bundle, src_file, os.path.join("lib", filename))
        for root, dirs, files in os.walk(build_lib_dir):
            ziproot = root[len(build_dir + "/"):].replace("-", "_")
            for filename in files:
                total_size += add_file(bundle, os.path.join(root, filename),
                                       os.path.join(ziproot, filename.replace("-", "_")))

    print()
    print(total_size, "B", total_size / 1024, "kiB", total_size / 1024 / 1024, "MiB")
    print("Bundled in", zip_filename)
    if not success:
        print("WARNING: some failures above")
        sys.exit(2)


if __name__ == "__main__":
    from scripts import target_versions

    tagged = input("Did you tag this release already ([y]/n)? ")
    if tagged and tagged.lower() != 'y':
        print("Go ahead and tag. I'll wait.")
        sys.exit(3)

    bundle_lib_location = os.path.abspath(sys.argv[1])
    output_dir = os.path.abspath(sys.argv[2])
    os.chdir(bundle_lib_location)

    bundle_version = None
    tag = subprocess.run('git describe --tags --exact-match', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if tag.returncode == 0:
        bundle_version = tag
    else:
        commitish = subprocess.run("git log --pretty=format:'%h' -n 1", shell=True, stdout=subprocess.PIPE)
        bundle_version = commitish
    bundle_version = bundle_version.stdout.strip().decode("utf-8", "strict")

    zip_filename = os.path.join(output_dir,
        'adafruit-circuitpython-bundle-{VERSION}.zip'.format(
            VERSION=bundle_version))
    build_bundle(bundle_lib_location, bundle_version, zip_filename)
    os.makedirs("build_deps", exist_ok=True)
    for version in target_versions.VERSIONS:
        mpy_cross = "build_deps/mpy-cross-" + version["name"]
        circuitpython_build_tools.build_mpy_cross(mpy_cross, version["tag"])
        zip_filename = os.path.join(output_dir,
            'adafruit-circuitpython-bundle-{TAG}-{VERSION}.zip'.format(
                TAG=version["name"],
                VERSION=bundle_version))
        build_bundle(bundle_lib_location, bundle_version, zip_filename, mpy_cross=mpy_cross)

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
import shutil
import sys
import subprocess

IGNORE_PY = ["setup.py", "conf.py", "__init__.py"]

def mpy_cross(mpy_cross_filename, circuitpython_tag, quiet=False):
    if os.path.isfile(mpy_cross_filename):
        return
    if not quiet:
        title = "Building mpy-cross for circuitpython " + circuitpython_tag
        print()
        print(title)
        print("=" * len(title))

    os.makedirs("build_deps/", exist_ok=True)
    if not os.path.isdir("build_deps/circuitpython"):
        clone = subprocess.run("git clone https://github.com/adafruit/circuitpython.git build_deps/circuitpython", shell=True)
        if clone.returncode != 0:
            sys.exit(clone.returncode)

    current_dir = os.getcwd()
    os.chdir("build_deps/circuitpython/mpy-cross")
    make = subprocess.run("git fetch && git checkout {TAG} && git submodule update && make clean && make".format(TAG=circuitpython_tag), shell=True)
    os.chdir(current_dir)

    shutil.copy("build_deps/circuitpython/mpy-cross/mpy-cross", mpy_cross_filename)

    if make.returncode != 0:
        sys.exit(make.returncode)


def library(library_path, output_directory, mpy_cross=None):
    py_files = []
    package_files = []
    total_size = 512
    for filename in os.listdir(library_path):
        full_path = os.path.join(library_path, filename)
        init_file = os.path.join(full_path, "__init__.py")
        if os.path.isdir(full_path) and os.path.isfile(init_file):
            files = os.listdir(full_path)
            files = filter(lambda x: x.endswith(".py"), files)
            files = map(lambda x: os.path.join(filename, x), files)
            package_files.extend(files)
        if filename.endswith(".py") and filename not in IGNORE_PY:
            py_files.append(filename)

    if len(py_files) > 1:
        output_directory = os.path.join(output_directory, library)
        os.makedirs(output_directory)
        package_init = os.path.join(output_directory, "__init__.py")
        # Touch the __init__ file.
        with open(package_init, 'a'):
            pass

    if len(package_files) > 1:
        for fn in package_files:
            base_dir = os.path.join(output_directory, os.path.dirname(fn))
            if not os.path.isdir(base_dir):
                os.makedirs(base_dir)
                total_size += 512


    new_extension = ".py"
    if mpy_cross:
        new_extension = ".mpy"

    for filename in py_files:
        full_path = os.path.join(library_path, filename)
        output_file = os.path.join(output_directory,
                                   filename.replace(".py", new_extension))
        if mpy_cross:
            mpy_success = subprocess.call([mpy_cross,
                                           "-o", output_file,
                                           full_path])
            if mpy_success != 0:
                raise RuntimeError("mpy-cross failed on", full_path)
        else:
            shutil.copyfile(full_path, output_file)

    for filename in package_files:
        full_path = os.path.join(library_path, filename)
        if (not mpy_cross or
                os.stat(full_path).st_size == 0 or
                filename.endswith("__init__.py")):
            output_file = os.path.join(output_directory, filename)
            shutil.copyfile(full_path, output_file)
        else:
            output_file = os.path.join(output_directory,
                                       filename.replace(".py", new_extension))
            mpy_success = subprocess.call([mpy_cross,
                                           "-o", output_file,
                                           full_path])
            if mpy_success != 0:
                raise RuntimeError("mpy-cross failed on", full_path)

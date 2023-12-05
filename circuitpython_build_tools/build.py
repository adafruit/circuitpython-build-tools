#!/usr/bin/env python3

# The MIT License (MIT)
#
# Copyright (c) 2016 Scott Shawcroft for Adafruit Industries
#               2018, 2019 Michael Schroeder
#               2021 James Carr
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
import platform
import pathlib
import requests
import semver
import shutil
import stat
import sys
import subprocess
import tempfile

# pyproject.toml `py_modules` values that are incorrect. These should all have PRs filed!
# and should be removed when the fixed version is incorporated in its respective bundle.

pyproject_py_modules_blocklist = set((
    # adafruit bundle
    "adafruit_colorsys",

    # community bundle
    "at24mac_eeprom",
    "circuitpython_Candlesticks",
    "CircuitPython_Color_Picker",
    "CircuitPython_Equalizer",
    "CircuitPython_Scales",
    "circuitPython_Slider",
    "circuitpython_uboxplot",
    "P1AM",
    "p1am_200_helpers",
))

if sys.version_info >= (3, 11):
    from tomllib import loads as load_toml
else:
    from tomli import loads as load_toml

def load_pyproject_toml(lib_path: pathlib.Path):
    try:
        return load_toml((lib_path / "pyproject.toml") .read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"No pyproject.toml in {lib_path}")
        return {}

def get_nested(doc, *args, default=None):
    for a in args:
        if doc is None: return default
        try:
            doc = doc[a]
        except (KeyError, IndexError) as e:
            return default
    return doc

IGNORE_PY = ["setup.py", "conf.py", "__init__.py"]
GLOB_PATTERNS = ["*.py", "*.bin"]
S3_MPY_PREFIX = "https://adafruit-circuit-python.s3.amazonaws.com/bin/mpy-cross"

def version_string(path=None, *, valid_semver=False):
    version = None
    tag = subprocess.run('git describe --tags --exact-match', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=path)
    if tag.returncode == 0:
        version = tag.stdout.strip().decode("utf-8", "strict")
    else:
        describe = subprocess.run("git describe --tags --always", shell=True, stdout=subprocess.PIPE, cwd=path)
        describe = describe.stdout.strip().decode("utf-8", "strict").rsplit("-", maxsplit=2)
        if len(describe) == 3:
            tag, additional_commits, commitish = describe
            commitish = commitish[1:]
        else:
            tag = "0.0.0"
            commit_count = subprocess.run("git rev-list --count HEAD", shell=True, stdout=subprocess.PIPE, cwd=path)
            additional_commits = commit_count.stdout.strip().decode("utf-8", "strict")
            commitish = describe[0]
        if valid_semver:
            version_info = semver.parse_version_info(tag)
            if not version_info.prerelease:
                version = semver.bump_patch(tag) + "-alpha.0.plus." + additional_commits + "+" + commitish
            else:
                version = tag + ".plus." + additional_commits + "+" + commitish
        else:
            version = commitish
    return version

def mpy_cross(mpy_cross_filename, circuitpython_tag, quiet=False):
    if os.path.isfile(mpy_cross_filename):
        return

    # Try to pull from S3
    uname = platform.uname()
    s3_url = None
    if uname[0].title() == 'Linux' and uname[4].lower() in ('amd64', 'x86_64'):
        s3_url = f"{S3_MPY_PREFIX}/linux-amd64/mpy-cross-linux-amd64-{circuitpython_tag}.static"
    elif uname[0].title() == 'Linux' and uname[4].lower() == 'armv7l':
        s3_url = f"{S3_MPY_PREFIX}/linux-raspbian/mpy-cross-linux-raspbian-{circuitpython_tag}.static-raspbian"
    elif uname[0].title() == 'Darwin':
        s3_url = f"{S3_MPY_PREFIX}/macos-11/mpy-cross-macos-11-{circuitpython_tag}-universal"
    elif uname[0].title() == "Windows" and uname[4].lower() in ("amd64", "x86_64"):
        s3_url = f"{S3_MPY_PREFIX}/windows/mpy-cross-windows-{circuitpython_tag}.static.exe"
    elif not quiet:
         print(f"Pre-built mpy-cross not available for sysname='{uname[0]}' release='{uname[2]}' machine='{uname[4]}'.")

    if s3_url is not None:
        if not quiet:
            print(f"Checking S3 for {s3_url}")
        try:
            r = requests.get(s3_url)
            if r.status_code == 200:
                with open(mpy_cross_filename, "wb") as f:
                    f.write(r.content)
                    # Set the User Execute bit
                    os.chmod(mpy_cross_filename, os.stat(mpy_cross_filename)[0] | stat.S_IXUSR)
                    if not quiet:
                        print("  FOUND")
                    return
        except Exception as e:
            if not quiet:
                print(f"    exception fetching from S3: {e}")
        if not quiet:
            print("  NOT FOUND")

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
    os.chdir("build_deps/circuitpython")
    make = subprocess.run("git fetch && git checkout {TAG} && git submodule update".format(TAG=circuitpython_tag), shell=True)
    os.chdir("tools")
    make = subprocess.run("git submodule update --init .", shell=True)
    os.chdir("../mpy-cross")
    make = subprocess.run("make clean && make", shell=True)
    os.chdir(current_dir)

    if make.returncode != 0:
        print("Failed to build mpy-cross from source... bailing out")
        sys.exit(make.returncode)

    shutil.copy("build_deps/circuitpython/mpy-cross/mpy-cross", mpy_cross_filename)

def _munge_to_temp(original_path, temp_file, library_version):
    with open(original_path, "r", encoding="utf-8") as original_file:
        for line in original_file:
            line = line.strip("\n")
            if line.startswith("__version__"):
                line = line.replace("0.0.0-auto.0", library_version)
                line = line.replace("0.0.0+auto.0", library_version)
            print(line, file=temp_file)
    temp_file.flush()

def get_package_info(library_path, package_folder_prefix):
    lib_path = pathlib.Path(library_path)
    parent_idx = len(lib_path.parts)
    py_files = []
    package_files = []
    package_info = {}
    glob_search = []
    for pattern in GLOB_PATTERNS:
        glob_search.extend(list(lib_path.rglob(pattern)))

    pyproject_toml = load_pyproject_toml(lib_path)
    py_modules = get_nested(pyproject_toml, "tool", "setuptools", "py-modules", default=[])
    packages = get_nested(pyproject_toml, "tool", "setuptools", "packages", default=[])

    blocklisted = [name for name in py_modules if name in pyproject_py_modules_blocklist]

    if blocklisted:
        print(f"{lib_path}/settings.toml:1: {blocklisted[0]} blocklisted: not using metadata from pyproject.toml")
        py_modules = packages = ()

    example_files = [sub_path for sub_path in (lib_path / "examples").rglob("*")
            if sub_path.is_file()]

    if packages and py_modules:
        raise ValueError("Cannot specify both tool.setuptools.py-modules and .packages")

    elif packages:
        if len(packages) > 1:
            raise ValueError("Only a single package is supported")
        package_name = packages[0]
        #print(f"Using package name from pyproject.toml: {package_name}")
        package_info["is_package"] = True
        package_info["module_name"] = package_name
        package_files = [sub_path for sub_path in (lib_path / package_name).rglob("*")
                if sub_path.is_file()]

    elif py_modules:
        if len(py_modules) > 1:
            raise ValueError("Only a single module is supported")
        py_module = py_modules[0]
        #print(f"Using module name from pyproject.toml: {py_module}")
        package_name = py_module
        package_info["is_package"] = False
        package_info["module_name"] = py_module
        py_files = [lib_path / f"{py_module}.py"]

    else:
        print(f"{lib_path}: Using legacy autodetection")
        package_info["is_package"] = False
        for file in glob_search:
            if file.parts[parent_idx] != "examples":
                if len(file.parts) > parent_idx + 1:
                    for prefix in package_folder_prefix:
                        if file.parts[parent_idx].startswith(prefix):
                            package_info["is_package"] = True
                if package_info["is_package"]:
                    package_files.append(file)
                else:
                    if file.name in IGNORE_PY:
                        #print("Ignoring:", file.resolve())
                        continue
                    if file.parent == lib_path:
                        py_files.append(file)

        if package_files:
            package_info["module_name"] = package_files[0].relative_to(library_path).parent.name
        elif py_files:
            package_info["module_name"] = py_files[0].relative_to(library_path).name[:-3]
        else:
            package_info["module_name"] = None

    if len(py_files) > 1:
        raise ValueError("Multiple top level py files not allowed. Please put "
                         "them in a package or combine them into a single file.")

    package_info["package_files"] = package_files
    package_info["py_files"] = py_files
    package_info["example_files"] = example_files

    try:
        package_info["version"] = version_string(library_path, valid_semver=True)
    except ValueError as e:
        print(library_path + " has version that doesn't follow SemVer (semver.org)")
        print(e)
        package_info["version"] = version_string(library_path)

    return package_info

def library(library_path, output_directory, package_folder_prefix,
            mpy_cross=None, example_bundle=False):
    lib_path = pathlib.Path(library_path)
    package_info = get_package_info(library_path, package_folder_prefix)
    py_package_files = package_info["package_files"] + package_info["py_files"]
    example_files = package_info["example_files"]
    module_name = package_info["module_name"]

    for fn in example_files:
        base_dir = os.path.join(output_directory.replace("/lib", "/"),
                                fn.relative_to(library_path).parent)
        if not os.path.isdir(base_dir):
            os.makedirs(base_dir)

    for fn in py_package_files:
        base_dir = os.path.join(output_directory,
                                fn.relative_to(library_path).parent)
        if not os.path.isdir(base_dir):
            os.makedirs(base_dir)

    library_version = package_info['version']

    if not example_bundle:
        for filename in py_package_files:
            full_path = os.path.join(library_path, filename)
            output_file = output_directory / filename.relative_to(library_path)
            if filename.suffix == ".py":
                with tempfile.NamedTemporaryFile(delete=False, mode="w+") as temp_file:
                    temp_file_name = temp_file.name
                    try:
                        _munge_to_temp(full_path, temp_file, library_version)
                        temp_file.close()
                        if mpy_cross and os.stat(temp_file.name).st_size != 0:
                            output_file = output_file.with_suffix(".mpy")
                            mpy_success = subprocess.call([
                                mpy_cross,
                                "-o", output_file,
                                "-s", str(filename.relative_to(library_path)),
                                temp_file.name
                            ])
                            if mpy_success != 0:
                                raise RuntimeError("mpy-cross failed on", full_path)
                        else:
                            shutil.copyfile(full_path, output_file)
                    finally:
                        os.remove(temp_file_name)
            else:
                shutil.copyfile(full_path, output_file)

    requirements_files = lib_path.glob("requirements.txt*")
    requirements_files = [f for f in requirements_files if f.stat().st_size > 0]

    toml_files = lib_path.glob("pyproject.toml*")
    toml_files = [f for f in toml_files if f.stat().st_size > 0]
    requirements_files.extend(toml_files)

    if module_name and requirements_files and not example_bundle:
        requirements_dir = pathlib.Path(output_directory).parent / "requirements"
        if not os.path.isdir(requirements_dir):
            os.makedirs(requirements_dir, exist_ok=True)
        requirements_subdir = f"{requirements_dir}/{module_name}"
        if not os.path.isdir(requirements_subdir):
            os.makedirs(requirements_subdir, exist_ok=True)
        for filename in requirements_files:
            full_path = os.path.join(library_path, filename)
            output_file = os.path.join(requirements_subdir, filename.name)
            shutil.copyfile(full_path, output_file)

    for filename in example_files:
        full_path = os.path.join(library_path, filename)
        output_file = os.path.join(output_directory.replace("/lib", "/"),
                                   filename.relative_to(library_path))
        shutil.copyfile(full_path, output_file)

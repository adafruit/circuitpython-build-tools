#!/usr/bin/env python3

# The MIT License (MIT)
#
# Copyright (c) 2016-2017 Scott Shawcroft for Adafruit Industries
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

import json
import os
import os.path
import re
import shlex
import shutil
import subprocess
import sys
import zipfile

import click

from circuitpython_build_tools import build
from circuitpython_build_tools import target_versions

import pkg_resources

BLINKA_LIBRARIES = [
    "adafruit-blinka",
    "adafruit-blinka-bleio",
    "adafruit-blinka-displayio",
    "adafruit-blinka-pyportal",
    "adafruit-python-extended-bus",
    "numpy",
    "pillow",
    "pyasn1",
    "pyserial",
    "scipy",
    "spidev",
]

def normalize_dist_name(name: str) -> str:
    """Return a normalized pip name"""
    return name.lower().replace("_", "-")

def add_file(bundle, src_file, zip_name):
    bundle.write(src_file, zip_name)
    file_size = os.stat(src_file).st_size
    file_sector_size = file_size
    if file_size % 512 != 0:
        file_sector_size = (file_size // 512 + 1) * 512
    print(zip_name, file_size, file_sector_size)
    return file_sector_size

def get_module_name(library_path, remote_name):
    """Figure out the module or package name and return it"""
    repo = subprocess.run(f'git remote get-url {remote_name}', shell=True, stdout=subprocess.PIPE, cwd=library_path)
    repo = repo.stdout.decode("utf-8", errors="ignore").strip().lower()
    if repo[-4:] == ".git":
        repo = repo[:-4]
    module_name = normalize_dist_name(repo.split("/")[-1])

    # circuitpython org repos are deployed to pypi without "org" in the pypi name
    module_name = re.sub(r"^circuitpython-org-", "circuitpython-", module_name)
    return module_name, repo

def get_bundle_requirements(directory, package_list):
    """
    Open the requirements.txt if it exists
    Remove anything that shouldn't be a requirement like Adafruit_Blinka
    Return the list
    """
    
    pypi_reqs = set()   # For multiple bundle dependency
    dependencies = set()   # For intra-bundle dependency
    
    path = directory + "/requirements.txt"
    if os.path.exists(path):
        with open(path, "r") as file:
            requirements = file.read()
            file.close()
            for line in requirements.split("\n"):
                line = line.lower().strip()
                if line.startswith("#") or line == "":
                    # skip comments
                    pass
                else:
                    # Remove any pip version and platform specifiers
                    original_name = re.split("[<>=~[;]", line)[0].strip()
                    # Normalize to match the indexes in package_list
                    line = normalize_dist_name(original_name)
                    if line in package_list:
                        dependencies.add(package_list[line]["module_name"])
                    elif line not in BLINKA_LIBRARIES:
                        # add with the exact spelling from requirements.txt
                        pypi_reqs.add(original_name)
    return sorted(dependencies), sorted(pypi_reqs)

def build_bundle_json(libs, bundle_version, output_filename, package_folder_prefix, remote_name="origin"):
    """
    Generate a JSON file of all the libraries in libs
    """
    packages = {}
    for library_path in libs:
        package = {}
        package_info = build.get_package_info(library_path, package_folder_prefix)
        module_name, repo = get_module_name(library_path, remote_name)
        if package_info["module_name"] is not None:
            package["module_name"] = package_info["module_name"]
            package["pypi_name"] = module_name
            package["repo"] = repo
            package["is_folder"] = package_info["is_package"]
            package["version"] = package_info["version"]
            package["path"] = "lib/" + package_info["module_name"]
            package["library_path"] = library_path
            packages[module_name] = package

    library_submodules = {}
    for id in packages:
        library = {}
        library["package"] = packages[id]["is_folder"]
        library["pypi_name"] = packages[id]["pypi_name"]
        library["version"] = packages[id]["version"]
        library["repo"] = packages[id]["repo"]
        library["path"] = packages[id]["path"]
        library["dependencies"], library["external_dependencies"] = get_bundle_requirements(packages[id]["library_path"], packages)
        library_submodules[packages[id]["module_name"]] = library
    out_file = open(output_filename, "w")
    json.dump(library_submodules, out_file, sort_keys=True)
    out_file.close()

def build_bundle(libs, bundle_version, output_filename, package_folder_prefix,
        build_tools_version="devel", mpy_cross=None, example_bundle=False, remote_name="origin"):
    build_dir = "build-" + os.path.basename(output_filename)
    top_folder = os.path.basename(output_filename).replace(".zip", "")
    build_lib_dir = os.path.join(build_dir, top_folder, "lib")
    build_example_dir = os.path.join(build_dir, top_folder, "examples")
    if os.path.isdir(build_dir):
        print("Deleting existing build.")
        shutil.rmtree(build_dir)
    total_size = 0
    if not example_bundle:
        os.makedirs(build_lib_dir)
        total_size += 512
    os.makedirs(build_example_dir)
    total_size += 512

    multiple_libs = len(libs) > 1

    success = True
    for library_path in libs:
        try:
            build.library(library_path, build_lib_dir,  package_folder_prefix,
                          mpy_cross=mpy_cross, example_bundle=example_bundle)
        except ValueError as e:
            print("build.library failure:", library_path)
            print(e)
            success = False

    print()
    print("Generating VERSIONS")
    if multiple_libs:
        with open(os.path.join(build_dir, top_folder, "VERSIONS.txt"), "w") as f:
            f.write(bundle_version + "\r\n")
            versions = subprocess.run(f'git submodule --quiet foreach \"git remote get-url {remote_name} && git describe --tags\"', shell=True, stdout=subprocess.PIPE, cwd=os.path.commonpath(libs))
            if versions.returncode != 0:
                print("Failed to generate versions file. Its likely a library hasn't been "
                      "released yet.")
                success = False

            repo = None
            for line in versions.stdout.split(b"\n"):
                if not line:
                    continue
                if line.startswith(b"ssh://git@"):
                    repo = b"https://" + line.split(b"@")[1][:-len(".git")]
                elif line.startswith(b"git@"):
                    repo = b"https://github.com/" + line.split(b":")[1][:-len(".git")]
                elif line.startswith(b"https:"):
                    repo = line.strip()[:-len(".git")]
                else:
                    f.write(repo.decode("utf-8", "strict") + "/releases/tag/" + line.strip().decode("utf-8", "strict") + "\r\n")

    if not success:
        print("WARNING: some failures above")
        sys.exit(2)

    print()
    print("Zipping")

    with zipfile.ZipFile(output_filename, 'w') as bundle:
        build_metadata = {"build-tools-version": build_tools_version}
        bundle.comment = json.dumps(build_metadata).encode("utf-8")
        if multiple_libs:
            total_size += add_file(bundle, "README.txt", os.path.join(top_folder, "README.txt"))
        for root, dirs, files in os.walk(build_dir):
            ziproot = root[len(build_dir + "/"):]
            for filename in files:
                total_size += add_file(bundle, os.path.join(root, filename),
                                       os.path.join(ziproot, filename.replace("-", "_")))

    print()
    print(total_size, "B", total_size / 1024, "kiB", total_size / 1024 / 1024, "MiB")
    print("Bundled in", output_filename)

def _find_libraries(current_path, depth):
    if depth <= 0:
        return [current_path]
    subdirectories = []
    for subdirectory in os.listdir(current_path):
        path = os.path.join(current_path, subdirectory)
        if os.path.isdir(path):
            subdirectories.extend(_find_libraries(path, depth - 1))
    return subdirectories

@click.command()
@click.option('--filename_prefix', required=True, help="Filename prefix for the output zip files.")
@click.option('--output_directory', default="bundles", help="Output location for the zip files.")
@click.option('--library_location', required=True, help="Location of libraries to bundle.")
@click.option('--library_depth', default=0, help="Depth of library folders. This is useful when multiple libraries are bundled together but are initially in separate subfolders.")
@click.option('--package_folder_prefix', default="adafruit_", help="Prefix string used to determine package folders to bundle.")
@click.option('--remote_name', default="origin", help="Git remote name to use during building")
@click.option('--ignore', "-i", multiple=True, type=click.Choice(["py", "mpy", "example", "json"]), help="Bundles to ignore building")
def build_bundles(filename_prefix, output_directory, library_location, library_depth, package_folder_prefix, remote_name, ignore):
    os.makedirs(output_directory, exist_ok=True)

    package_folder_prefix = package_folder_prefix.split(", ")

    bundle_version = build.version_string()

    libs = _find_libraries(os.path.abspath(library_location), library_depth)

    pkg = pkg_resources.get_distribution("circuitpython-build-tools")
    build_tools_version = "devel"
    if pkg:
        build_tools_version = pkg.version

    build_tools_fn = "z-build_tools_version-{}.ignore".format(
        build_tools_version)
    build_tools_fn = os.path.join(output_directory, build_tools_fn)
    with open(build_tools_fn, "w") as f:
        f.write(build_tools_version)

    # Build raw source .py bundle
    if "py" not in ignore:
        zip_filename = os.path.join(output_directory,
            filename_prefix + '-py-{VERSION}.zip'.format(
                VERSION=bundle_version))
        build_bundle(libs, bundle_version, zip_filename, package_folder_prefix,
                    build_tools_version=build_tools_version, remote_name=remote_name)

    # Build .mpy bundle(s)
    if "mpy" not in ignore:
        os.makedirs("build_deps", exist_ok=True)
        for version in target_versions.VERSIONS:
            # Use prebuilt mpy-cross on Travis, otherwise build our own.
            if "TRAVIS" in os.environ:
                mpy_cross = pkg_resources.resource_filename(
                    target_versions.__name__, "data/mpy-cross-" + version["name"])
            else:
                mpy_cross = "build_deps/mpy-cross-" + version["name"] + (".exe" * (os.name == "nt"))
                build.mpy_cross(mpy_cross, version["tag"])
            zip_filename = os.path.join(output_directory,
                filename_prefix + '-{TAG}-mpy-{VERSION}.zip'.format(
                    TAG=version["name"],
                    VERSION=bundle_version))
            build_bundle(libs, bundle_version, zip_filename, package_folder_prefix,
                        mpy_cross=mpy_cross, build_tools_version=build_tools_version, remote_name=remote_name)

    # Build example bundle
    if "example" not in ignore:
        zip_filename = os.path.join(output_directory,
            filename_prefix + '-examples-{VERSION}.zip'.format(
                VERSION=bundle_version))
        build_bundle(libs, bundle_version, zip_filename, package_folder_prefix,
                    build_tools_version=build_tools_version, example_bundle=True, remote_name=remote_name)

    # Build Bundle JSON
    if "json" not in ignore:
        json_filename = os.path.join(output_directory,
            filename_prefix + '-{VERSION}.json'.format(
                VERSION=bundle_version))
        build_bundle_json(libs, bundle_version, json_filename, package_folder_prefix, remote_name=remote_name)

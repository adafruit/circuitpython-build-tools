#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
#
# SPDX-License-Identifier: MIT

from circuitpython_build_tools import build
from circuitpython_build_tools import target_versions

import click


@click.command
@click.argument("versions")
def main(versions):
    print(versions)
    for version in [v for v in target_versions.VERSIONS if v["name"] in versions]:
        print(f"{version['name']}: {build.mpy_cross(version)}")


if __name__ == "__main__":
    main()

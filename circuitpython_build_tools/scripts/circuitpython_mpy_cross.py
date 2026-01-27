# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
#
# SPDX-License-Identifier: MIT
import subprocess

import click

from ..target_versions import VERSIONS
from ..build import mpy_cross


@click.command(context_settings={"ignore_unknown_options": True})
@click.option(
    "--circuitpython-version", type=click.Choice([version["name"] for version in VERSIONS])
)
@click.option("--quiet/--no-quiet", "quiet", type=bool, default=True)
@click.argument("mpy-cross-args", nargs=-1, required=True)
def main(circuitpython_version, quiet, mpy_cross_args):
    (version_info,) = [v for v in VERSIONS if v["name"] == circuitpython_version]
    mpy_cross_exe = str(mpy_cross(version_info, quiet))
    try:
        subprocess.check_call([mpy_cross_exe, *mpy_cross_args])
    except subprocess.CalledProcessError as e:
        raise SystemExit(e.returncode)


if __name__ == "__main__":
    main()

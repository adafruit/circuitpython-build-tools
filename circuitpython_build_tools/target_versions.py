#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2016 Scott Shawcroft, written for Adafruit Industries
#
# SPDX-License-Identifier: MIT

# The tag specifies which version of CircuitPython to use for mpy-cross.
# The name is used when constructing the zip file names.
# native_arches get a foo.<arch>.mpy for files using @micropython.native or viper. Versions
# without it leave those libraries out.
VERSIONS = [
    {"tag": "9.2.9", "name": "9.x"},
    {"tag": "10.3.1", "name": "10.x"},
    {
        "tag": "11.0.0-alpha.1",
        "name": "11.x",
        "native_arches": ("armv6m", "armv7emsp", "armv7emdp", "xtensawin", "rv32imc"),
    },
]

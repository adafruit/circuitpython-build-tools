# Adafruit CircuitPython Build Tools

[![Discord](https://img.shields.io/discord/327254708534116352.svg)](https://adafru.it/discord)

This repo contains build scripts used to build the
[Adafruit CircuitPython bundle](https://github.com/adafruit/Adafruit_CircuitPython_Bundle), [CircuitPython Community bundle](https://github.com/adafruit/CircuitPython_Community_Bundle)
and individual library release zips. Its focused on Github Actions support but will also work locally
when a gcc compiler is present.

The scripts will either fetch a pre-built mpy-cross from s3 or
automatically clone the [CircuitPython repo](https://github.com/adafruit/circuitpython) and attempt
to build mpy-cross. You'll need some version of gcc for this to work.

## Setting up libraries

These build tools automatically build .mpy files and zip them up for
CircuitPython when a new tagged release is created. To add support to a repo
you need to use the [CircuitPython
cookiecutter](https://github.com/adafruit/cookiecutter-adafruit-circuitpython)
to generate `.github/workflows/*.yml`.

The bundle build will produce one zip file for every major CircuitPython
release supported containing compatible mpy files and a zip with human readable py files.
It'll also "release" a `z-build_tools_version-x.x.x.ignore` file that will be
used to determine when a library needs new release files because the build tools
themselves changed, such as when a new major CircuitPython release happens.

## Building libraries locally

To build libraries built with the build tools you'll need to install the
circuitpython-build-tools package.

```shell
python3 -m venv .env
source .env/bin/activate
pip install circuitpython-build-tools
circuitpython-build-bundles --filename_prefix <output file prefix> --library_location .
```

When making changes to `circuitpython-build-tools` itself, you can test your changes
locally like so:

```shell
cd circuitpython-build-tools # this will be specific to your storage location
python3 -m venv .env
source .env/bin/activate
pip install -e .  # '-e' is pip's "development" install feature
circuitpython-build-bundles --filename_prefix <output file prefix> --library_location <library location>
```

## Contributing

Contributions are welcome! Please read our [Code of Conduct]
(https://github.com/adafruit/Adafruit\_CircuitPython\_adabot/blob/master/CODE\_OF\_CONDUCT.md)
before contributing to help this project stay welcoming.

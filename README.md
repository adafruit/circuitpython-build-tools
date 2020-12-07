# Adafruit CircuitPython Build Tools

[![Discord](https://img.shields.io/discord/327254708534116352.svg)](https://adafru.it/discord)

This repo contains build scripts used to build the
[Adafruit CircuitPython bundle](https://github.com/adafruit/Adafruit_CircuitPython_Bundle), [CircuitPython Community bundle](https://github.com/adafruit/CircuitPython_Community_Bundle)
and individual library release zips. Its focused on Travis CI support but will also work locally
when a gcc compiler is present.

The pip package includes mpy-crosses that run on Travis. When building locally, the scripts will
automatically clone the [CircuitPython repo](https://github.com/adafruit/circuitpython) and attempt
to build mpy-crosses. You'll need some version of gcc for this to work.

## Setting up libraries

These build tools are intended for use with [Travis CI](https://travis-ci.org)
to automatically build .mpy files and zip them up for CircuitPython when a new
tagged release is created.  To add support to a repo you need to:

  1. Use the [CircuitPython cookiecutter](https://github.com/adafruit/cookiecutter-adafruit-circuitpython) to generate .travis.yml.
  2. For adafruit repositories, simply give the CircuitPythonLibrarians team
     write access to the repo and Adabot will do the rest.

     Otherwise, go to travis-ci.org and find the repository (it needs to be
     setup to access your github account, and your github account needs access
     to write to the repo).  Flip the 'ON' switch on for Travis and the repo,
     see the Travis docs for more details: https://docs.travis-ci.com/user/getting-started/
  3. Get a GitHub 'personal access token' which has at least 'public_repo' or
     'repo' scope: https://help.github.com/articles/creating-an-access-token-for-command-line-use/
     Keep this token safe and secure!  Anyone with the token will be able to
     access and write to your GitHub repositories.  Travis will use the token
     to attach the .mpy files to the release.
  4. In the Travis CI settings for the repository that was enabled find the
     environment variable editing page: https://docs.travis-ci.com/user/environment-variables/#Defining-Variables-in-Repository-Settings
     Add an environment variable named GITHUB_TOKEN and set it to the value
     of the GitHub personal access token above.  Keep 'Display value in build
     log' flipped off.
  5. That's it!  Tag a release and Travis should go to work to add zipped .mpy files
     to the release.  It takes about a 2-3 minutes for a worker to spin up,
     build mpy-cross, and add the binaries to the release.

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
(https://github.com/adafruit/Adafruit_CircuitPython_adabot/blob/master/CODE_OF_CONDUCT.md)
before contributing to help this project stay welcoming.

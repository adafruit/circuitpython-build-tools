#!/usr/bin/env python

from setuptools import setup

setup(name='circuitpython-travis-build-tools',
      version='0.0.2',
      description='CircuitPython library build tools for Travis CI',
      author='Scott Shawcroft',
      author_email='scott@adafruit.com',
      url='https://www.adafruit.com/',
      packages=['circuitpython_build_tools'],
      package_data={'circuitpython_build_tools': ['data/mpy-cross-*']},
      scripts=["scripts/circuitpython-build-bundles",
               "scripts/circuitpython-build-library"],
      zip_safe=False,
      python_requires='>=3.4',
      install_requires=['']
      )

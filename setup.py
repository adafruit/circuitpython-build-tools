#!/usr/bin/env python

from setuptools import setup

setup(name='circuitpython-travis-build-tools',
      use_scm_version=True,
      setup_requires=["setuptools_scm"],
      description='CircuitPython library build tools for Travis CI',
      author='Scott Shawcroft',
      author_email='scott@adafruit.com',
      url='https://www.adafruit.com/',
      packages=['circuitpython_build_tools'],
      include_package_data=True,
      package_data={'circuitpython_build_tools': ['data/mpy-cross-*']},
      zip_safe=False,
      python_requires='>=3.4',
      install_requires=['Click'],
      entry_points='''
        [console_scripts]
        circuitpython-build-bundles=circuitpython_build_tools.scripts.build_bundles:build_bundles
      '''
      )

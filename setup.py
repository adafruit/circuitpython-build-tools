#!/usr/bin/env python

from setuptools import setup

setup(name='circuitpython-build-tools',
      use_scm_version=True,
      setup_requires=["setuptools_scm"],
      description='CircuitPython library build tools',
      author='Scott Shawcroft',
      author_email='scott@adafruit.com',
      url='https://www.adafruit.com/',
      packages=['circuitpython_build_tools',
                'circuitpython_build_tools.scripts'],
      package_data={'circuitpython_build_tools': ['data/mpy-cross-*']},
      zip_safe=False,
      python_requires='>=3.10',
      install_requires=['Click', 'requests', 'semver', 'tomli; python_version < "3.11"'],
      entry_points='''
        [console_scripts]
        circuitpython-build-bundles=circuitpython_build_tools.scripts.build_bundles:build_bundles
      '''
      )

from __future__ import annotation

try:
    from typing import TYPE_CHECKING
except ImportError:
    pass

try:
    from typing import TYPE_CHECKING as T
except ImportError:
    pass


try:
    import typing
except:
    pass

try:
    import typing as T
except:
    pass

__version__ = "0.0.0-auto"

if sys.implementation.name == "circuitpython":
    print("is circuitpython")

if sys.implementation.name != "circuitpython":
    print("not circuitpython (1)")

if not sys.implementation.name == "circuitpython":
    print("not circuitpython (2)")

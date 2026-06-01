"""pecan-apispec: decorator-driven OpenAPI 3 generation for Pecan apps.

The decorator layer (:func:`path`, :func:`operation`, :func:`schema`,
:func:`security_scheme`) is importable without apispec or Pecan installed.
The builder entry points (:func:`build_spec`, :func:`build_dict`,
:func:`build_yaml`) and the :class:`SpecController` are resolved lazily via
``__getattr__`` so importing this package never eagerly pulls in apispec/Pecan.
"""

from .decorators import operation
from .decorators import path
from .decorators import schema
from .decorators import security_scheme
from .registry import controllers
from .registry import reset
from .registry import schemas
from .registry import security_schemes

__version__ = "0.1.0"

__all__ = [
    "path",
    "operation",
    "schema",
    "security_scheme",
    "reset",
    "controllers",
    "schemas",
    "security_schemes",
    "build_spec",
    "build_dict",
    "build_yaml",
    "SpecController",
]

_LAZY = {"build_spec", "build_dict", "build_yaml"}


def __getattr__(name):
    if name in _LAZY:
        from . import builder

        return getattr(builder, name)
    if name == "SpecController":
        from .ext.ui import SpecController

        return SpecController
    raise AttributeError("module %r has no attribute %r" % (__name__, name))


def __dir__():
    return sorted(__all__)

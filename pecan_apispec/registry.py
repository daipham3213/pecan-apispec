"""Global metadata registry for pecan-apispec.

This module is intentionally free of any Pecan or apispec imports so that it
can be imported (and unit tested) in complete isolation.  The decorator layer
writes into the module-level dictionaries defined here, and the builder reads
from them when assembling an OpenAPI document.
"""

from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

__all__ = [
    "OperationInfo",
    "ControllerNode",
    "controllers",
    "schemas",
    "security_schemes",
    "reset",
]


@dataclass
class OperationInfo:
    """Per-method OpenAPI overrides recorded by :func:`~pecan_apispec.decorators.operation`.

    Anything that is ``None`` means "fall back to whatever introspection
    infers".  ``fields`` carries arbitrary OpenAPI Operation Object members
    (``summary``, ``description``, ``parameters``, ``requestBody``,
    ``responses``, ``security``, ...).
    """

    func_name: str
    methods: Optional[List[str]] = None
    path_suffix: Optional[str] = None
    fields: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ControllerNode:
    """A single node in the controller tree, registered by ``@path``."""

    segment: str
    name: str
    parent: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    cls: Optional[type] = None
    operations: Dict[str, OperationInfo] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Module-level registries.  Keyed by the logical *name* of each component so
# decorators can reference relationships (e.g. a child's ``parent``) by name
# without holding object references.
# ---------------------------------------------------------------------------
controllers: Dict[str, ControllerNode] = {}
schemas: Dict[str, Any] = {}
security_schemes: Dict[str, Dict[str, Any]] = {}


def reset() -> None:
    """Clear every registry.  Primarily useful for tests and REPL sessions."""
    controllers.clear()
    schemas.clear()
    security_schemes.clear()

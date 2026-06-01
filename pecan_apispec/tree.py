"""Pure path-tree mathematics.

Given the flat ``controllers`` registry (name -> :class:`ControllerNode`), these
helpers walk the ``parent`` chain up to the root and compose normalized URL
paths.  No Pecan, apispec, or registry-mutation here -- everything is a pure
function of its arguments so it can be exercised directly in unit tests.
"""

from typing import Dict
from typing import List

__all__ = ["join_paths", "parent_chain", "full_base_path"]


def join_paths(*parts: str) -> str:
    """Join URL path fragments into a single normalized absolute path.

    Empty fragments and stray slashes are collapsed; the result always begins
    with ``/`` and never has a trailing slash (except the root ``/`` itself).

        >>> join_paths('/', 'profile', '/{id}')
        '/profile/{id}'
        >>> join_paths('/')
        '/'
    """
    cleaned: List[str] = []
    for part in parts:
        if not part:
            continue
        for chunk in part.split("/"):
            if chunk:
                cleaned.append(chunk)
    return "/" + "/".join(cleaned) if cleaned else "/"


def parent_chain(
    name: str, controllers: Dict[str, "object"]
) -> List["object"]:
    """Return the chain of nodes from the root down to ``name`` (inclusive).

    Raises :class:`ValueError` on an unknown parent reference or a cycle.
    """
    chain: List[object] = []
    seen = set()
    current = name
    while current is not None:
        if current in seen:
            raise ValueError(
                "cycle detected in controller tree at %r" % current
            )
        seen.add(current)
        node = controllers.get(current)
        if node is None:
            raise ValueError(
                "unknown controller/parent reference %r" % current
            )
        chain.append(node)
        current = node.parent
    chain.reverse()
    return chain


def full_base_path(name: str, controllers: Dict[str, "object"]) -> str:
    """Compose the full base URL path for the controller named ``name``."""
    segments = [node.segment for node in parent_chain(name, controllers)]
    return join_paths(*segments)

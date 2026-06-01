"""Assemble an OpenAPI 3 document from the registry using apispec.

This is the only module that imports apispec, and it is imported lazily by the
package's ``__getattr__`` so the decorator layer keeps working without apispec
installed.  When marshmallow is available a :class:`MarshmallowPlugin` is added
automatically so registered ``Schema`` classes resolve to ``$ref`` components.
"""

from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from .introspect import operations_for_controller
from .registry import controllers
from .registry import schemas
from .registry import security_schemes
from .tree import full_base_path
from .tree import join_paths

__all__ = ["build_spec", "build_dict", "build_yaml"]

DEFAULT_OPENAPI_VERSION = "3.0.3"


def _is_marshmallow_schema(obj: Any) -> bool:
    try:
        from marshmallow import Schema
    except (
        ImportError
    ):  # pragma: no cover - exercised only without marshmallow
        return False
    if isinstance(obj, Schema):
        return True
    return isinstance(obj, type) and issubclass(obj, Schema)


def _default_plugins(plugins: Optional[List[Any]]) -> List[Any]:
    plugins = list(plugins or [])
    try:
        from apispec.ext.marshmallow import MarshmallowPlugin
    except ImportError:  # pragma: no cover - marshmallow extra not installed
        return plugins
    if not any(isinstance(p, MarshmallowPlugin) for p in plugins):
        plugins.append(MarshmallowPlugin())
    return plugins


def _register_components(spec) -> None:
    for name, definition in security_schemes.items():
        spec.components.security_scheme(name, definition)
    for name, schema_obj in schemas.items():
        if _is_marshmallow_schema(schema_obj):
            spec.components.schema(name, schema=schema_obj)
        else:
            spec.components.schema(name, component=schema_obj)


def _grouped_paths() -> Dict[str, Dict[str, Any]]:
    """Map full URL path -> {http verb: operation fields}."""
    paths: Dict[str, Dict[str, Any]] = {}
    for node in controllers.values():
        base = full_base_path(node.name, controllers)
        for op in operations_for_controller(node):
            full = join_paths(base, op["sub_path"])
            fields = dict(op["fields"])
            if node.tags and "tags" not in fields:
                fields["tags"] = list(node.tags)
            paths.setdefault(full, {})[op["method"]] = fields
    return paths


def build_spec(
    title: str,
    version: str,
    openapi_version: str = DEFAULT_OPENAPI_VERSION,
    plugins: Optional[List[Any]] = None,
    **options: Any,
):
    """Build and return an :class:`apispec.APISpec` from the registry."""
    from apispec import APISpec

    spec = APISpec(
        title=title,
        version=version,
        openapi_version=openapi_version,
        plugins=_default_plugins(plugins),
        **options,
    )
    _register_components(spec)
    for full_path, operations in _grouped_paths().items():
        spec.path(path=full_path, operations=operations)
    return spec


def build_dict(
    title: str,
    version: str,
    openapi_version: str = DEFAULT_OPENAPI_VERSION,
    plugins: Optional[List[Any]] = None,
    **options: Any,
) -> Dict[str, Any]:
    """Build the OpenAPI document as a plain ``dict``."""
    return build_spec(
        title, version, openapi_version, plugins, **options
    ).to_dict()


def build_yaml(
    title: str,
    version: str,
    openapi_version: str = DEFAULT_OPENAPI_VERSION,
    plugins: Optional[List[Any]] = None,
    **options: Any,
) -> str:
    """Build the OpenAPI document as a YAML string (requires PyYAML)."""
    return build_spec(
        title, version, openapi_version, plugins, **options
    ).to_yaml()

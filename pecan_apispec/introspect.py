"""Infer HTTP verbs and sub-paths from Pecan controller conventions.

This module never ``import pecan``.  Instead it reads the conventions Pecan
records by *attribute access*:

* exposed methods carry ``func.exposed == True`` and a ``func._pecan`` dict;
* generic controllers (``@expose(generic=True)``) store their HTTP verbs in
  ``func._pecan['generic_handlers']`` keyed by uppercase method name plus a
  ``'DEFAULT'`` entry (which answers ``GET``);
* ``RestController`` subclasses follow name-based verb conventions
  (``get_all`` -> ``GET /``, ``get_one`` -> ``GET /{id}``, ``post`` ->
  ``POST /``, ...), detected by class name in the MRO.

Anything declared with :func:`~pecan_apispec.decorators.operation` overrides the
inferred result.
"""

import inspect
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

__all__ = ["operations_for_controller"]

#: RestController method name -> (http verb, sub-path) convention.
REST_VERB_MAP: Dict[str, tuple] = {
    "get_all": ("get", ""),
    "get_one": ("get", "/{id}"),
    "get": ("get", "/{id}"),
    "post": ("post", ""),
    "put": ("put", "/{id}"),
    "delete": ("delete", "/{id}"),
    "new": ("get", "/new"),
    "edit": ("get", "/{id}/edit"),
    "get_delete": ("get", "/{id}/delete"),
}


def _pecan_cfg(func) -> Optional[dict]:
    return getattr(func, "_pecan", None)


def is_exposed(func) -> bool:
    return getattr(func, "exposed", False) or _pecan_cfg(func) is not None


def is_rest_controller(cls) -> bool:
    return any(base.__name__ == "RestController" for base in cls.__mro__)


def _generic_methods(cfg: dict) -> List[str]:
    """HTTP verbs for a generic controller, from its ``generic_handlers``."""
    handlers = cfg.get("generic_handlers") or {}
    methods: List[str] = []
    for key in handlers:
        verb = "get" if key == "DEFAULT" else key.lower()
        if verb not in methods:
            methods.append(verb)
    return methods or ["get"]


def _inferred_methods(func_name: str, func, rest: bool) -> List[str]:
    if rest and func_name in REST_VERB_MAP:
        return [REST_VERB_MAP[func_name][0]]
    cfg = _pecan_cfg(func) or {}
    if cfg.get("generic"):
        return _generic_methods(cfg)
    return ["get"]


def _inferred_sub_path(func_name: str, rest: bool) -> str:
    if rest and func_name in REST_VERB_MAP:
        return REST_VERB_MAP[func_name][1]
    if func_name == "index":
        return ""
    return "/" + func_name


def _handler_funcs_to_skip(cls) -> set:
    """Generic ``when`` handlers are reported via their parent's
    ``generic_handlers``; collect them so we don't emit them twice."""
    skip = set()
    for _, func in inspect.getmembers(cls, predicate=inspect.isfunction):
        cfg = _pecan_cfg(func)
        if cfg and cfg.get("generic_handlers"):
            for key, handler in cfg["generic_handlers"].items():
                if key != "DEFAULT":
                    skip.add(handler)
    return skip


def _emit_generic(
    node,
    func_name,
    func,
    override,
    base_sub,
    name_by_func,
    results: List[Dict[str, Any]],
) -> None:
    """Emit one operation per verb of a generic controller.

    Each verb is served by its own handler function (the ``DEFAULT`` handler
    answers GET), so each verb picks up *that handler's* ``@operation`` fields
    rather than sharing the index's.
    """
    cfg = _pecan_cfg(func) or {}
    handlers = cfg.get("generic_handlers") or {"DEFAULT": func}
    for key, handler in handlers.items():
        verb = "get" if key == "DEFAULT" else key.lower()
        handler_name = name_by_func.get(handler, func_name)
        handler_override = node.operations.get(handler_name)
        if key == "DEFAULT":
            handler_override = override or handler_override
        sub_path = base_sub
        fields: Dict[str, Any] = {}
        if handler_override is not None:
            if handler_override.path_suffix is not None:
                sub_path = handler_override.path_suffix
            fields = dict(handler_override.fields)
        results.append(
            {
                "method": verb,
                "sub_path": sub_path,
                "func_name": handler_name,
                "fields": fields,
            }
        )


def operations_for_controller(node) -> List[Dict[str, Any]]:
    """Yield one entry per (controller method, HTTP verb).

    Each entry is a dict with keys ``method`` (lowercase verb), ``sub_path``,
    ``func_name`` and ``fields`` (the OpenAPI override fields, possibly empty).
    """
    cls = node.cls
    if cls is None:
        return []

    rest = is_rest_controller(cls)
    skip = _handler_funcs_to_skip(cls)
    name_by_func = {
        func: name
        for name, func in inspect.getmembers(cls, predicate=inspect.isfunction)
    }
    results: List[Dict[str, Any]] = []

    for func_name, func in inspect.getmembers(
        cls, predicate=inspect.isfunction
    ):
        if func in skip:
            continue
        override = node.operations.get(func_name)
        rest_verb = rest and func_name in REST_VERB_MAP
        if override is None and not is_exposed(func) and not rest_verb:
            continue

        cfg = _pecan_cfg(func) or {}
        explicit_methods = (
            override is not None and override.methods is not None
        )

        if cfg.get("generic") and not explicit_methods:
            if override is not None and override.path_suffix is not None:
                base_sub = override.path_suffix
            else:
                base_sub = _inferred_sub_path(func_name, rest)
            _emit_generic(
                node,
                func_name,
                func,
                override,
                base_sub,
                name_by_func,
                results,
            )
            continue

        methods = (
            override.methods
            if explicit_methods
            else _inferred_methods(func_name, func, rest)
        )
        if override is not None and override.path_suffix is not None:
            sub_path = override.path_suffix
        else:
            sub_path = _inferred_sub_path(func_name, rest)
        fields = dict(override.fields) if override is not None else {}

        for verb in methods:
            results.append(
                {
                    "method": verb,
                    "sub_path": sub_path,
                    "func_name": func_name,
                    "fields": fields,
                }
            )

    return results

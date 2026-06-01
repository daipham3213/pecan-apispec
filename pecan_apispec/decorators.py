"""The public decorator API.

These decorators only *record* lightweight metadata into :mod:`pecan_apispec.registry`.
They deliberately avoid importing Pecan or apispec, so an application can be
annotated even in an environment where neither is installed (the spec is only
assembled later, by the builder).
"""

from typing import Any
from typing import Dict
from typing import Iterable
from typing import Optional

from .registry import ControllerNode
from .registry import OperationInfo
from .registry import controllers
from .registry import schemas
from .registry import security_schemes

__all__ = ["path", "operation", "schema", "security_scheme"]

#: Attribute stamped onto a controller method by :func:`operation`.
_OPERATION_ATTR = "_apispec_operation"


def path(
    segment: str,
    name: Optional[str] = None,
    parent: Optional[str] = None,
    tags: Optional[Iterable[str]] = None,
):
    """Register a controller class as a node in the API path tree.

    :param segment: the URL path segment this controller is mounted at,
        relative to its parent (use ``'/'`` for the root controller).
    :param name: logical name used to reference this node (defaults to the
        class name).  Children reference it via ``parent=...``.
    :param parent: the ``name`` of the parent controller, or ``None`` for root.
    :param tags: OpenAPI tags applied to every operation under this controller
        (unless an individual :func:`operation` overrides ``tags``).
    """

    def decorator(cls):
        node_name = name or cls.__name__
        operations: Dict[str, OperationInfo] = {}
        # ``@operation`` runs on the methods *before* this class decorator, so
        # the metadata is already stamped on the functions -- collect it now.
        for attr_name, attr in vars(cls).items():
            op = getattr(attr, _OPERATION_ATTR, None)
            if op is not None:
                op.func_name = attr_name
                operations[attr_name] = op
        controllers[node_name] = ControllerNode(
            segment=segment,
            name=node_name,
            parent=parent,
            tags=list(tags or []),
            cls=cls,
            operations=operations,
        )
        return cls

    return decorator


def operation(
    methods: Optional[Iterable[str]] = None,
    path_suffix: Optional[str] = None,
    **openapi_fields: Any,
):
    """Attach OpenAPI Operation metadata to a controller method.

    Anything supplied here *overrides* what introspection would otherwise infer.

    :param methods: explicit list of HTTP verbs (e.g. ``['get', 'post']``).
    :param path_suffix: explicit sub-path appended to the controller's base
        path (e.g. ``'/{id}'``).  An empty string maps to the base path.
    :param openapi_fields: arbitrary Operation Object members such as
        ``summary``, ``description``, ``parameters``, ``requestBody``,
        ``responses``, ``security`` and ``tags``.
    """

    def decorator(func):
        setattr(
            func,
            _OPERATION_ATTR,
            OperationInfo(
                func_name=getattr(func, "__name__", ""),
                methods=[m.lower() for m in methods]
                if methods is not None
                else None,
                path_suffix=path_suffix,
                fields=dict(openapi_fields),
            ),
        )
        return func

    return decorator


def schema(name: Optional[str] = None):
    """Register a reusable component schema.

    Works as a class decorator on a marshmallow ``Schema`` (resolved to a
    ``$ref`` by the builder) or can be called directly with a plain OpenAPI
    schema ``dict``.

        >>> @schema()
        ... class PetSchema(Schema): ...

        >>> schema('Error')({'type': 'object', ...})
    """

    def decorator(schema_obj):
        schema_name = name
        if schema_name is None:
            schema_name = getattr(schema_obj, "__name__", None)
        if schema_name is None:
            raise ValueError("schema() requires a name for non-class schemas")
        schemas[schema_name] = schema_obj
        return schema_obj

    return decorator


def security_scheme(name: str, **definition: Any) -> Dict[str, Any]:
    """Register a reusable OpenAPI security scheme.

    >>> security_scheme('bearerAuth', type='http', scheme='bearer',
    ...                  bearerFormat='JWT')
    """
    security_schemes[name] = dict(definition)
    return security_schemes[name]

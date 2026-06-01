=============
pecan-apispec
=============

Decorator-driven `OpenAPI 3 <https://spec.openapis.org/oas/v3.0.3>`_ spec
generation for `Pecan <https://pecan.readthedocs.io/>`_ applications.

``pecan-apispec`` follows the same shape as `pecan-swagger
<https://github.com/dougwig/pecan-swagger>`_ -- lightweight decorators record
metadata into a global registry, and a build step walks that registry to
assemble the document -- with two differences:

* it emits **OpenAPI 3** (not Swagger 2.0), and
* operations are **filled in** (summaries, parameters, request bodies,
  responses, and optional `marshmallow <https://marshmallow.readthedocs.io/>`_
  schemas) instead of being empty stubs.

Install
=======

.. code-block:: console

    uv pip install pecan-apispec
    # optional extras
    uv pip install "pecan-apispec[marshmallow,yaml]"

Quick start
===========

.. code-block:: python

    import pecan
    from pecan_apispec import path, operation, schema, security_scheme

    security_scheme('bearerAuth', type='http', scheme='bearer', bearerFormat='JWT')

    @path('profile', name='Profile', parent='Root', tags=['profile'])
    class ProfileController:
        @pecan.expose(generic=True, template='json')
        @operation(summary='Get profile',
                   responses={'200': {'description': 'The profile'}})
        def index(self):
            ...

        @index.when(method='POST', template='json')
        @operation(summary='Update profile', security=[{'bearerAuth': []}])
        def index_post(self):
            ...

    @path('/', name='Root')
    class RootController:
        profile = ProfileController()

Then build the document:

.. code-block:: python

    from pecan_apispec import build_dict, build_yaml

    doc = build_dict('myapp', '1.0')        # -> dict (OpenAPI 3.0.3)
    text = build_yaml('myapp', '1.0')       # -> YAML string (needs 'yaml' extra)

How it works
============

``registry``
    Module-level dicts plus ``ControllerNode`` / ``OperationInfo`` dataclasses.
    No Pecan or apispec imports, so it is testable in isolation.

``decorators``
    ``@path(segment, name, parent, tags)`` registers a controller node;
    ``@operation(methods, path_suffix, **openapi_fields)`` attaches per-method
    OpenAPI metadata; ``schema()`` / ``security_scheme()`` register reusable
    components.

``introspect``
    Reads Pecan conventions purely by attribute access (never ``import
    pecan``): the ``_pecan`` dict for exposed methods, ``generic_handlers`` for
    verbs on ``@expose(generic=True)``, and ``RestController`` conventions by
    MRO class name.  ``index`` maps to the controller path, other methods to
    ``/<name>``, and REST member actions to ``/{id}``.  ``@operation``
    overrides anything inferred.

``tree``
    Pure functions that walk the parent chain to the root and normalize
    slashes; guards against cycles and unknown parents.

``builder``
    ``build_spec`` / ``build_dict`` / ``build_yaml``: constructs an
    ``APISpec`` (adding ``MarshmallowPlugin`` automatically when marshmallow is
    installed), registers components, then emits one path per controller.

``ext.ui``
    ``SpecController`` mounts in your controller tree and serves
    ``GET /<mount>/openapi.json`` plus a Swagger UI page at ``GET /<mount>/``.
    Pecan is imported lazily so the package imports without Pecan present.

Design decisions
================

* **Lazy apispec/Pecan imports** via ``__getattr__`` -- the decorator layer is
  usable without apispec or Pecan installed.
* **``@operation`` always wins** over introspection, so bad inference is never
  a dead end.
* **OpenAPI 3.0.3** by default; marshmallow schemas resolve to ``$ref``
  components.

Serving the spec
================

.. code-block:: python

    from pecan_apispec import SpecController

    @path('/', name='Root')
    class RootController:
        docs = SpecController('myapp', '1.0')   # GET /docs/  and /docs/openapi.json

License
=======

Apache-2.0.

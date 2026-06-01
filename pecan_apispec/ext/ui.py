"""A mountable Pecan controller that serves the spec and Swagger UI.

Pecan is imported lazily inside :func:`SpecController` so that
``import pecan_apispec`` (and even ``from pecan_apispec.ext import ui``) works in
environments where Pecan is not installed.  The controller is built by a
factory rather than declared at module scope, because the ``@expose``
decorators must run against the real Pecan at call time.

Mounted at ``spec = SpecController('My API', '1.0')`` inside your controller
tree, it exposes:

* ``GET  /<mount>/openapi`` (and ``/<mount>/openapi.json``) -- the OpenAPI
  document as JSON;
* ``GET  /<mount>/``       -- Swagger UI (loaded from a CDN) pointed at it.

The ``.json`` suffix works because Pecan's default content-type-by-extension
routing strips the extension and dispatches to the ``openapi`` method (a
literal ``route='openapi.json'`` cannot work, as the extension is consumed
before routing).
"""

from typing import Any

__all__ = ["SpecController", "SWAGGER_UI_TEMPLATE"]

#: Minimal Swagger UI page; ``{spec_url}`` is filled with the JSON endpoint.
SWAGGER_UI_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{title}</title>
  <link rel="stylesheet"
        href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js">
  </script>
  <script>
    window.onload = function () {{
      window.ui = SwaggerUIBundle({{
        url: "{spec_url}",
        dom_id: "#swagger-ui",
        deepLinking: true,
      }});
    }};
  </script>
</body>
</html>"""


def SpecController(
    title: str,
    version: str,
    openapi_version: str = "3.0.3",
    ui: bool = True,
    spec_url: str = "openapi.json",
    **build_options: Any,
):
    """Construct and return a Pecan controller instance serving the spec.

    :param title: OpenAPI document title.
    :param version: API version string.
    :param openapi_version: OpenAPI spec version (default ``3.0.3``).
    :param ui: when ``True`` (default) also serve Swagger UI at the index.
    :param spec_url: relative URL the UI fetches the JSON from.
    :param build_options: forwarded to :func:`pecan_apispec.build_dict`.
    """
    from pecan import expose

    from ..builder import build_dict

    class _SpecController(object):
        @expose("json")
        def openapi(self):
            return build_dict(title, version, openapi_version, **build_options)

        if ui:

            @expose(content_type="text/html")
            def index(self):
                return SWAGGER_UI_TEMPLATE.format(
                    title=title,
                    spec_url=spec_url,
                )

    return _SpecController()

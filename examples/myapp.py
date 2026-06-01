"""A tiny Pecan application annotated with pecan-apispec decorators.

Run the spec generation with ``examples/myapp_doc.py``.  This module only
declares controllers; it does not start a server, so it imports cleanly even
without a full Pecan deployment.
"""

import pecan

from pecan_apispec import operation
from pecan_apispec import path
from pecan_apispec import schema
from pecan_apispec import security_scheme

try:
    from marshmallow import Schema
    from marshmallow import fields

    @schema()
    class ProfileSchema(Schema):
        id = fields.Int(dump_only=True)
        name = fields.Str(required=True)
        email = fields.Email()

    HAVE_MARSHMALLOW = True
except ImportError:  # pragma: no cover - marshmallow is an optional extra
    HAVE_MARSHMALLOW = False


security_scheme("bearerAuth", type="http", scheme="bearer", bearerFormat="JWT")


@path("profile", name="Profile", parent="Root", tags=["profile"])
class ProfileController(object):
    @pecan.expose(generic=True, template="json")
    @operation(
        summary="Get the current profile",
        responses={
            "200": {
                "description": "The profile",
                "content": {
                    "application/json": {
                        "schema": {
                            "$ref": "#/components/schemas/ProfileSchema"
                        }
                        if HAVE_MARSHMALLOW
                        else {"type": "object"}
                    }
                },
            }
        },
    )
    def index(self):
        return {"id": 1, "name": "Ada", "email": "ada@example.com"}

    @index.when(method="POST", template="json")
    @operation(
        summary="Update the current profile",
        security=[{"bearerAuth": []}],
        requestBody={
            "required": True,
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ProfileSchema"}
                    if HAVE_MARSHMALLOW
                    else {"type": "object"}
                }
            },
        },
        responses={"200": {"description": "Updated profile"}},
    )
    def index_post(self):
        return pecan.request.json


@path("/", name="Root")
class RootController(object):
    profile = ProfileController()

    @pecan.expose(template="json")
    @operation(
        summary="Service root", responses={"200": {"description": "OK"}}
    )
    def index(self):
        return {"service": "myapp"}

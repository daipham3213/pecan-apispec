"""Tests for the apispec-backed builder (OpenAPI 3 assembly)."""

import pecan
import pytest

from pecan_apispec import build_dict
from pecan_apispec import build_spec
from pecan_apispec import build_yaml
from pecan_apispec import operation
from pecan_apispec import path
from pecan_apispec import schema
from pecan_apispec import security_scheme

marshmallow = pytest.importorskip("marshmallow")
from marshmallow import Schema  # noqa: E402
from marshmallow import fields  # noqa: E402


def _build_sample_app():
    @schema()
    class PetSchema(Schema):
        id = fields.Int(dump_only=True)
        name = fields.Str(required=True)

    security_scheme(
        "bearerAuth", type="http", scheme="bearer", bearerFormat="JWT"
    )

    @path("/", name="Root")
    class Root:
        pass

    @path("pets", name="Pets", parent="Root", tags=["pets"])
    class Pets:
        @pecan.expose(generic=True, template="json")
        @operation(
            summary="List pets",
            responses={"200": {"description": "ok"}},
        )
        def index(self):
            pass

        @index.when(method="POST", template="json")
        @operation(
            summary="Create a pet",
            security=[{"bearerAuth": []}],
            responses={"201": {"description": "created"}},
        )
        def index_post(self):
            pass

    return PetSchema


def test_build_dict_structure_and_metadata():
    _build_sample_app()
    doc = build_dict("Pet Store", "2.0")

    assert doc["openapi"] == "3.0.3"
    assert doc["info"] == {"title": "Pet Store", "version": "2.0"}

    assert "/pets" in doc["paths"]
    pets = doc["paths"]["/pets"]
    assert set(pets) == {"get", "post"}
    assert pets["get"]["summary"] == "List pets"
    # controller tags propagate to every operation that didn't set its own
    assert pets["get"]["tags"] == ["pets"]
    assert pets["post"]["summary"] == "Create a pet"
    assert pets["post"]["security"] == [{"bearerAuth": []}]


def test_components_registered():
    _build_sample_app()
    doc = build_dict("Pet Store", "2.0")

    components = doc["components"]
    assert components["securitySchemes"]["bearerAuth"]["scheme"] == "bearer"

    # marshmallow plugin resolves the Schema into a component
    assert "PetSchema" in components["schemas"]
    pet = components["schemas"]["PetSchema"]
    assert "name" in pet["properties"]


def test_custom_openapi_version_and_spec_object():
    @path("ping", name="Ping")
    class Ping:
        @pecan.expose(template="json")
        @operation(summary="ping", responses={"200": {"description": "pong"}})
        def index(self):
            pass

    spec = build_spec("API", "1.0", openapi_version="3.1.0")
    doc = spec.to_dict()
    assert doc["openapi"] == "3.1.0"
    assert "/ping" in doc["paths"]


def test_build_yaml_returns_string():
    pytest.importorskip("yaml")
    _build_sample_app()
    text = build_yaml("Pet Store", "2.0")
    assert isinstance(text, str)
    assert "openapi: 3.0.3" in text
    assert "/pets" in text


def test_plain_dict_schema_component():
    schema("Error")(
        {"type": "object", "properties": {"message": {"type": "string"}}}
    )
    doc = build_dict("API", "1.0")
    assert doc["components"]["schemas"]["Error"]["properties"]["message"] == {
        "type": "string"
    }

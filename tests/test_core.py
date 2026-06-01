"""Tests for the registry, decorators, tree math and introspection.

These exercise the apispec-free layer of the package.  Real Pecan is used so
the introspection is validated against genuine ``_pecan`` conventions.
"""

import pecan
import pytest
from pecan.rest import RestController

from pecan_apispec import controllers
from pecan_apispec import operation
from pecan_apispec import path
from pecan_apispec import registry
from pecan_apispec import schema
from pecan_apispec import security_scheme
from pecan_apispec.introspect import operations_for_controller
from pecan_apispec.tree import full_base_path
from pecan_apispec.tree import join_paths
from pecan_apispec.tree import parent_chain


# --------------------------------------------------------------------------- #
# tree
# --------------------------------------------------------------------------- #
def test_join_paths_normalizes():
    assert join_paths("/", "profile", "/{id}") == "/profile/{id}"
    assert join_paths("/") == "/"
    assert join_paths("", "//a//", "b/") == "/a/b"
    assert join_paths() == "/"


def test_parent_chain_and_base_path():
    @path("/", name="Root")
    class Root:
        pass

    @path("profile", name="Profile", parent="Root")
    class Profile:
        pass

    chain = [n.name for n in parent_chain("Profile", controllers)]
    assert chain == ["Root", "Profile"]
    assert full_base_path("Profile", controllers) == "/profile"
    assert full_base_path("Root", controllers) == "/"


def test_unknown_parent_raises():
    @path("x", name="Orphan", parent="Nope")
    class Orphan:
        pass

    with pytest.raises(ValueError, match="unknown"):
        full_base_path("Orphan", controllers)


def test_cycle_detected():
    registry.controllers["A"] = registry.ControllerNode("a", "A", parent="B")
    registry.controllers["B"] = registry.ControllerNode("b", "B", parent="A")
    with pytest.raises(ValueError, match="cycle"):
        full_base_path("A", registry.controllers)


# --------------------------------------------------------------------------- #
# decorators / registry
# --------------------------------------------------------------------------- #
def test_path_registers_node_with_tags_and_operations():
    @path("widgets", name="Widgets", tags=["widget"])
    class Widgets:
        @pecan.expose(template="json")
        @operation(summary="list widgets")
        def index(self):
            pass

    node = controllers["Widgets"]
    assert node.segment == "widgets"
    assert node.tags == ["widget"]
    assert "index" in node.operations
    assert node.operations["index"].fields["summary"] == "list widgets"


def test_schema_and_security_scheme_registration():
    @schema("Error")
    class _Error:
        pass

    security_scheme("bearerAuth", type="http", scheme="bearer")

    assert registry.schemas["Error"] is _Error
    assert registry.security_schemes["bearerAuth"]["scheme"] == "bearer"


def test_schema_with_plain_dict():
    schema("Plain")({"type": "object"})
    assert registry.schemas["Plain"] == {"type": "object"}


# --------------------------------------------------------------------------- #
# introspection
# --------------------------------------------------------------------------- #
def test_generic_controller_infers_get_and_post():
    @path("profile", name="Profile")
    class Profile:
        @pecan.expose(generic=True, template="json")
        def index(self):
            pass

        @index.when(method="POST", template="json")
        def index_post(self):
            pass

    ops = operations_for_controller(controllers["Profile"])
    by_method = {o["method"]: o for o in ops}
    assert set(by_method) == {"get", "post"}
    # both map to the controller base path (empty suffix), single func_name
    assert by_method["get"]["sub_path"] == ""
    assert by_method["post"]["sub_path"] == ""
    assert by_method["get"]["func_name"] == "index"


def test_plain_exposed_method_uses_named_subpath():
    @path("acct", name="Acct")
    class Acct:
        @pecan.expose(template="json")
        def settings(self):
            pass

    ops = operations_for_controller(controllers["Acct"])
    settings = [o for o in ops if o["func_name"] == "settings"]
    assert settings and settings[0]["method"] == "get"
    assert settings[0]["sub_path"] == "/settings"


def test_rest_controller_conventions():
    @path("books", name="Books")
    class Books(RestController):
        @pecan.expose(template="json")
        def get_all(self):
            pass

        @pecan.expose(template="json")
        def get_one(self, _id):
            pass

        @pecan.expose(template="json")
        def post(self):
            pass

        @pecan.expose(template="json")
        def delete(self, _id):
            pass

    ops = operations_for_controller(controllers["Books"])
    seen = {(o["method"], o["sub_path"]) for o in ops}
    assert ("get", "") in seen  # get_all -> GET /
    assert ("get", "/{id}") in seen  # get_one -> GET /{id}
    assert ("post", "") in seen  # post -> POST /
    assert ("delete", "/{id}") in seen  # delete -> DELETE /{id}


def test_operation_override_wins_over_inference():
    @path("things", name="Things")
    class Things:
        @pecan.expose(template="json")
        @operation(methods=["put"], path_suffix="/{key}", summary="set")
        def index(self):
            pass

    ops = operations_for_controller(controllers["Things"])
    assert len(ops) == 1
    assert ops[0]["method"] == "put"
    assert ops[0]["sub_path"] == "/{key}"
    assert ops[0]["fields"]["summary"] == "set"

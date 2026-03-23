import copy

import pytest

from ocdskit.normalize import (
    convert_from_oas3,
    fix_validation_errors,
    get_definitions_keyword,
    get_normal_schema,
    get_schema_hash,
    hoist_deep_properties,
    normalize_schema,
    remove_fields,
    remove_private_fields,
    remove_unreachable_definitions,
)

OAS3_SCHEMA = {
    "paths": {
        "/foo": {
            "get": {
                "responses": {
                    "200": {"content": {"application/json": {"schema": {"$ref": "#/components/schemas/Foo"}}}}
                }
            }
        }
    },
    "components": {
        "schemas": {
            "Foo": {"type": "object", "properties": {"bar": {"$ref": "#/components/schemas/Bar"}}},
            "Bar": {"type": "object"},
            "Baz": {"type": "object"},
        }
    },
}


@pytest.mark.parametrize(
    ("schema", "expected"),
    [
        ({}, "$defs"),
        ({"$defs": {}}, "$defs"),
        ({"definitions": {}}, "definitions"),
        ({"$defs": {}, "definitions": {}}, "$defs"),
    ],
)
def test_get_definitions_keyword(schema, expected):
    assert get_definitions_keyword(schema) == expected


@pytest.mark.parametrize(
    ("a", "b"),
    [
        ({"type": "string"}, {"type": "string"}),
        ({"key": 1, "order": 2}, {"order": 2, "key": 1}),
        ({"type": "string", "description": "foo"}, {"type": "string", "description": "bar"}),
    ],
)
def test_get_schema_hash_equal(a, b):
    def normalizer(s):
        return {k: v for k, v in s.items() if k != "description"}

    assert get_schema_hash(a, normalizer) == get_schema_hash(b, normalizer)


def test_get_schema_hash_inequal():
    def normalizer(s):
        return s

    assert get_schema_hash({"type": "string"}, normalizer) != get_schema_hash({"type": "integer"}, normalizer)


@pytest.mark.parametrize(
    "schema",
    [
        {},
        {
            "paths": {
                "/foo": {
                    "get": {
                        "responses": {  # non-components $ref
                            "200": {"content": {"application/json": {"schema": {"$ref": "#/other/Foo"}}}}
                        },
                    }
                }
            },
            "components": {"schemas": {}},
        },
    ],
)
def test_convert_from_oas3_empty_definitions(schema):
    result = convert_from_oas3(schema)

    assert result == {"$schema": "http://json-schema.org/draft-04/schema#", "definitions": {}}


def test_convert_from_oas3_get_only_false():
    result = convert_from_oas3(copy.deepcopy(OAS3_SCHEMA))

    assert result == {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "definitions": {
            "Foo": {"type": "object", "properties": {"bar": {"$ref": "#/definitions/Bar"}}},  # $ref rewritten
            "Bar": {"type": "object"},
            "Baz": {"type": "object"},
        },
    }


def test_convert_from_oas3_get_only_true():
    result = convert_from_oas3(copy.deepcopy(OAS3_SCHEMA), get_only=True)

    assert result == {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "definitions": {
            "Foo": {"type": "object", "properties": {"bar": {"$ref": "#/definitions/Bar"}}},  # $ref rewritten
            "Bar": {"type": "object"},
            # Baz not reachable
        },
    }


def test_remove_private_fields():
    schema = {
        "properties": {
            "public": {"_keep": True},
            "_private": {},
            "outer": {"properties": {"_remove": {}, "inner": {}}},
        }
    }
    remove_private_fields(schema)

    assert schema == {"properties": {"public": {"_keep": True}, "outer": {"properties": {"inner": {}}}}}


def test_remove_fields():
    schema = {
        "properties": {
            "public": {"keep": True},
            "private": {},
            "outer": {"properties": {"remove": {}, "inner": {}}},
        }
    }
    remove_fields(schema, {"private", "remove", "keep"})

    assert schema == {"properties": {"public": {"keep": True}, "outer": {"properties": {"inner": {}}}}}


@pytest.mark.parametrize("keyword", ["$defs", "definitions"])
def test_remove_unreachable_definitions(keyword):
    schema = {
        keyword: {
            "Root": {"properties": {"foo": {"$ref": f"#/{keyword}/Reachable"}}},
            "Reachable": {},
            "Unreachable": {},
        }
    }
    remove_unreachable_definitions(schema, "Root")

    assert schema == {keyword: {"Root": {"properties": {"foo": {"$ref": f"#/{keyword}/Reachable"}}}, "Reachable": {}}}


@pytest.mark.parametrize("keyword", ["$defs", "definitions"])
def test_remove_unreachable_definitions_no_pattern_match(keyword):
    schema = {keyword: {"Alpha": {}, "Beta": {}}}
    remove_unreachable_definitions(schema, "NoMatch")

    assert schema == {keyword: {}}


def test_remove_unreachable_definitions_list_traversal():
    schema = {
        "definitions": {
            "Root": {"anyOf": [{"$ref": "#/definitions/Child"}, {"type": "null"}]},
            "Child": {},
            "Unreachable": {},
        }
    }
    remove_unreachable_definitions(schema, "Root")

    assert schema == {
        "definitions": {
            "Root": {"anyOf": [{"$ref": "#/definitions/Child"}, {"type": "null"}]},
            "Child": {},
        }
    }


@pytest.mark.parametrize(
    "schema",
    [
        {"anyOf": {"a": {"type": "string"}, "b": {"type": "integer"}}},
        {"anyOf": {"a": {"type": "string"}, "b": {"type": "integer"}, "c": {"type": "string"}}},  # duplication
        {"anyOf": [{"type": "string"}, {"type": "integer"}]},
    ],
)
def test_fix_validation_errors(schema):
    fix_validation_errors(schema)

    assert schema == {"anyOf": [{"type": "string"}, {"type": "integer"}]}


def test_fix_validation_errors_normalizer():
    schema = {"anyOf": {"a": {"type": "string", "title": "A"}, "b": {"type": "string", "title": "B"}}}
    fix_validation_errors(schema, normalizer=lambda s: {k: v for k, v in s.items() if k != "title"})

    assert schema == {"anyOf": [{"type": "string", "title": "A"}]}


@pytest.mark.parametrize("schema", [{"type": "string", "title": "Foo", "description": "Bar"}, "hello", 42, None])
def test_get_normal_schema(schema):
    assert get_normal_schema(schema) == schema


def test_get_normal_schema_remove_nontype_keywords():
    schema = {
        "type": "object",
        "title": "Foo",
        "description": "Bar",
        "properties": {"foo": {"type": "string", "minLength": 1, "maxLength": 10, "pattern": "^[0-9]+$"}},
        "x-foo": "bar",
    }
    result = get_normal_schema(schema, remove_nontype_keywords=True)

    assert result == {"type": "object", "properties": {"foo": {"type": "string"}}, "x-foo": "bar"}


def test_get_normal_schema_remove_x_keywords():
    schema = {
        "type": "object",
        "x-foo": "bar",
        "x-baz": 1,
        "properties": {"foo": {"type": "string", "x-baz": True}},
        "title": "Foo",
    }
    result = get_normal_schema(schema, remove_x_keywords=True)

    assert result == {"type": "object", "properties": {"foo": {"type": "string"}}, "title": "Foo"}


def test_get_normal_schema_remove_fields():
    schema = {"type": "object", "properties": {"foo": {"type": "string"}, "bar": {"type": "integer"}}, "title": "Foo"}
    result = get_normal_schema(schema, remove_fields={"bar"})

    assert result == {"type": "object", "properties": {"foo": {"type": "string"}}, "title": "Foo"}


def test_get_normal_schema_list_traversal():
    schema = [{"type": "string", "title": "Foo"}, {"type": "integer", "title": "Bar"}]
    result = get_normal_schema(schema, remove_nontype_keywords=True)

    assert result == [{"type": "string"}, {"type": "integer"}]


@pytest.mark.parametrize("keyword", ["definitions", "$defs"])
def test_hoist_deep_properties_named_by_title(keyword):
    schema = {
        keyword: {
            "Root": {
                "type": "object",
                "properties": {"issue": {"title": "Child", "type": "object", "properties": {"x": {"type": "string"}}}},
            }
        }
    }
    hoist_deep_properties(schema, lambda s: s)

    assert schema == {
        keyword: {
            "Root": {"type": "object", "properties": {"issue": {"$ref": f"#/{keyword}/Child"}}},
            "Child": {"title": "Child", "type": "object", "properties": {"x": {"type": "string"}}},
        }
    }


def test_hoist_deep_properties_named_by_prop():
    schema = {
        "definitions": {
            "Root": {
                "type": "object",
                "properties": {"child": {"type": "object", "properties": {"x": {"type": "string"}}}},
            }
        }
    }
    hoist_deep_properties(schema, lambda s: s)

    assert schema == {
        "definitions": {
            "Root": {"type": "object", "properties": {"child": {"$ref": "#/definitions/Child"}}},
            "Child": {"type": "object", "properties": {"x": {"type": "string"}}},
        }
    }


def test_hoist_deep_properties_name_collision():
    schema = {
        "definitions": {
            "Child": {"type": "string"},  # name already taken
            "Root": {
                "type": "object",
                "properties": {"child": {"type": "object", "properties": {"x": {"type": "string"}}}},
            },
        }
    }
    hoist_deep_properties(schema, lambda s: s)

    assert schema == {
        "definitions": {
            "Child": {"type": "string"},
            "Root": {"type": "object", "properties": {"child": {"$ref": "#/definitions/Child_c018a9ca"}}},
            "Child_c018a9ca": {"type": "object", "properties": {"x": {"type": "string"}}},
        }
    }


def test_hoist_deep_properties_top_level_definition():
    schema = {"definitions": {"Flat": {"type": "object", "properties": {"x": {"type": "string"}}}}}
    hoist_deep_properties(schema, lambda s: s)

    assert schema == {"definitions": {"Flat": {"type": "object", "properties": {"x": {"type": "string"}}}}}


def test_hoist_deep_properties_allof_special_case():
    schema = {
        "definitions": {
            "Root": {
                "allOf": [
                    {
                        "type": "object",
                        "properties": {"child": {"type": "object", "properties": {"x": {"type": "string"}}}},
                    }
                ]
            }
        }
    }
    hoist_deep_properties(schema, lambda s: s)

    assert schema == {
        "definitions": {
            "Root": {"allOf": [{"type": "object", "properties": {"child": {"$ref": "#/definitions/Child"}}}]},
            "Child": {"type": "object", "properties": {"x": {"type": "string"}}},
        }
    }


def test_hoist_deep_properties_top_level_properties():
    schema = {"properties": {"foo": {"type": "object", "properties": {"x": {"type": "string"}}}}}
    hoist_deep_properties(schema, lambda s: s)

    assert schema == {
        "properties": {"foo": {"$ref": "#/$defs/Foo"}},
        "$defs": {"Foo": {"type": "object", "properties": {"x": {"type": "string"}}}},
    }


def test_hoist_deep_properties_list_traversal():
    schema = {
        "definitions": {
            "Root": {
                "anyOf": [
                    {"title": "Child", "type": "object", "properties": {"x": {"type": "string"}}},
                    {"type": "null"},
                ]
            }
        }
    }
    hoist_deep_properties(schema, lambda s: s)

    assert schema == {
        "definitions": {
            "Root": {"anyOf": [{"$ref": "#/definitions/Child"}, {"type": "null"}]},
            "Child": {"title": "Child", "type": "object", "properties": {"x": {"type": "string"}}},
        }
    }


def test_normalize_schema():
    def get_base_classes(classes):
        names = list(classes)
        shared = set.intersection(*(classes[n] for n in names))
        return [{"name": "Base", "members": names, "props": shared}]

    schema = {
        "definitions": {
            "A": {"type": "object", "properties": {"x": {"type": "string"}, "y": {"type": "integer"}}},
            "B": {"type": "object", "properties": {"x": {"type": "string"}, "y": {"type": "integer"}}},
        }
    }
    normalize_schema(schema, lambda s: s, get_base_classes)

    assert schema == {
        "definitions": {
            "A": {"allOf": [{"$ref": "#/definitions/Base"}, {"type": "object"}]},
            "B": {"allOf": [{"$ref": "#/definitions/Base"}, {"type": "object"}]},
            "Base": {"properties": {"x": {"type": "string"}, "y": {"type": "integer"}}},
        }
    }


def test_normalize_schema_inheritance_between_base_classes():
    def get_base_classes(classes):
        names = list(classes)
        shared = set.intersection(*(classes[n] for n in names))
        all_props = set().union(*(classes[n] for n in names))
        large_members = [n for n in names if all_props <= classes[n]]
        return [
            {"name": "BaseSmall", "members": names, "props": shared},
            {"name": "BaseLarge", "members": large_members, "props": all_props},
        ]

    schema = {
        "definitions": {
            "A": {
                "type": "object",
                "properties": {"x": {"type": "string"}, "y": {"type": "integer"}, "z": {"type": "boolean"}},
            },
            "B": {
                "type": "object",
                "properties": {"x": {"type": "string"}, "y": {"type": "integer"}, "z": {"type": "boolean"}},
            },
            "C": {
                "type": "object",
                "properties": {"x": {"type": "string"}, "y": {"type": "integer"}},
            },
        }
    }
    normalize_schema(schema, lambda s: s, get_base_classes)

    assert schema == {
        "definitions": {
            "A": {"allOf": [{"$ref": "#/definitions/BaseLarge"}, {"type": "object"}]},
            "B": {"allOf": [{"$ref": "#/definitions/BaseLarge"}, {"type": "object"}]},
            "C": {"allOf": [{"$ref": "#/definitions/BaseSmall"}, {"type": "object"}]},
            "BaseLarge": {"allOf": [{"$ref": "#/definitions/BaseSmall"}, {"properties": {"z": {"type": "boolean"}}}]},
            "BaseSmall": {"properties": {"y": {"type": "integer"}, "x": {"type": "string"}}},
        }
    }


def test_normalize_schema_duplicate_bases():
    def get_base_classes(classes):
        names = list(classes)
        shared = set.intersection(*(classes[n] for n in names))
        return [
            {"name": "Base1", "members": names, "props": shared},
            {"name": "Base2", "members": names, "props": shared},
        ]

    schema = {
        "definitions": {
            "A": {"type": "object", "properties": {"x": {"type": "string"}, "y": {"type": "integer"}}},
            "B": {"type": "object", "properties": {"x": {"type": "string"}, "y": {"type": "integer"}}},
        }
    }
    normalize_schema(schema, lambda s: s, get_base_classes)

    assert schema == {
        "definitions": {
            "A": {"allOf": [{"$ref": "#/definitions/Base1"}, {"type": "object"}]},
            "B": {"allOf": [{"$ref": "#/definitions/Base1"}, {"type": "object"}]},
            "Base1": {"properties": {"y": {"type": "integer"}, "x": {"type": "string"}}},
        }
    }

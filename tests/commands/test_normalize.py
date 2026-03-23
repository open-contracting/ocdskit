import json

import pytest

from ocdskit.__main__ import main
from tests import run_command

DENORM_SCHEMA = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "definitions": {
        "Alpha": {
            "properties": {
                "name": {"type": "string"},
                "description": {"type": "string"},
                "extra": {"type": "integer"},
            },
        },
        "Beta": {
            "properties": {
                "name": {"type": "string"},
                "description": {"type": "string"},
                "other": {"type": "boolean"},
            },
        },
    },
}
NORM_SCHEMA = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "definitions": {
        "Alpha": {
            "allOf": [
                {"$ref": "#/definitions/Base"},
                {
                    "properties": {"extra": {"type": "integer"}},
                },
            ]
        },
        "Beta": {
            "allOf": [
                {"$ref": "#/definitions/Base"},
                {
                    "properties": {"other": {"type": "boolean"}},
                },
            ]
        },
        "Base": {
            "properties": {"name": {"type": "string"}, "description": {"type": "string"}},
        },
    },
}
OAS3_SCHEMA = {
    "openapi": "3.0.0",
    "paths": {
        "/foo": {
            "get": {
                "responses": {
                    "200": {
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Foo"},
                            }
                        }
                    }
                }
            }
        }
    },
    "components": {
        "schemas": {
            "Foo": {"properties": {"id": {"type": "string"}}},
            "Bar": {"properties": {"id": {"type": "string"}}},
        }
    },
}


@pytest.fixture
def schema_path(tmpdir):
    return tmpdir.join("schema.json")


@pytest.fixture
def denorm_schema_path(schema_path):
    schema_path.write(json.dumps(DENORM_SCHEMA))
    return schema_path


@pytest.fixture
def norm_schema_path(schema_path):
    schema_path.write(json.dumps(NORM_SCHEMA))
    return schema_path


@pytest.fixture
def oas3_schema_path(schema_path):
    schema_path.write(json.dumps(OAS3_SCHEMA))
    return schema_path


def test_command(capsys, monkeypatch, denorm_schema_path):
    run_command(capsys, monkeypatch, main, ["normalize", str(denorm_schema_path)])

    assert json.loads(denorm_schema_path.read()) == NORM_SCHEMA


def test_command_check(capsys, monkeypatch, norm_schema_path):
    original = json.dumps(NORM_SCHEMA)

    captured = run_command(capsys, monkeypatch, main, ["normalize", "--check", str(norm_schema_path)])

    assert norm_schema_path.read() == original  # unchanged
    assert captured.err == ""


def test_command_check_error(capsys, monkeypatch, denorm_schema_path):
    original = json.dumps(DENORM_SCHEMA)

    captured = run_command(capsys, monkeypatch, main, ["normalize", "--check", str(denorm_schema_path)])

    assert denorm_schema_path.read() == original  # unchanged
    assert f"ERROR: {denorm_schema_path} is denormalized" in captured.err


def test_command_fix(capsys, monkeypatch, schema_path):
    schema = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "definitions": {"Alpha": {"properties": {"bar": {"anyOf": {"a": {}, "b": {}}}}}},
    }
    schema_path.write(json.dumps(schema))

    run_command(capsys, monkeypatch, main, ["normalize", "--fix", str(schema_path)])

    result = json.loads(schema_path.read())
    assert isinstance(result["definitions"]["Alpha"]["properties"]["bar"]["anyOf"], list)


def test_command_remove_private_fields(capsys, monkeypatch, schema_path):
    schema = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "definitions": {"Alpha": {"properties": {"name": {"type": "string"}, "_private": {"type": "string"}}}},
    }
    schema_path.write(json.dumps(schema))

    run_command(capsys, monkeypatch, main, ["normalize", "--remove-private-fields", str(schema_path)])

    result = json.loads(schema_path.read())
    assert list(result["definitions"]["Alpha"]["properties"]) == ["name"]


def test_command_remove_fields(capsys, monkeypatch, schema_path):
    schema = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "definitions": {"Alpha": {"properties": {"name": {"type": "string"}, "remove": {"type": "string"}}}},
    }
    schema_path.write(json.dumps(schema))

    run_command(capsys, monkeypatch, main, ["normalize", str(schema_path), "--remove-fields", "remove"])

    result = json.loads(schema_path.read())
    assert list(result["definitions"]["Alpha"]["properties"]) == ["name"]


def test_command_root_pattern(capsys, monkeypatch, schema_path):
    schema = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "definitions": {"Root": {"properties": {"x": {"type": "string"}}}, "Unreachable": {"type": "string"}},
    }
    schema_path.write(json.dumps(schema))

    run_command(capsys, monkeypatch, main, ["normalize", "--root-pattern", "Root", str(schema_path)])

    result = json.loads(schema_path.read())
    assert list(result["definitions"]) == ["Root"]


def test_command_ignore_x_keywords(capsys, monkeypatch, schema_path):
    schema = {  # Add x-tag to DENORM_SCHEMA
        "$schema": "http://json-schema.org/draft-04/schema#",
        "definitions": {
            "Alpha": {
                "properties": {
                    "name": {"type": "string", "x-tag": "A"},
                    "description": {"type": "string"},
                    "extra": {"type": "integer"},
                },
            },
            "Beta": {
                "properties": {
                    "name": {"type": "string", "x-tag": "B"},
                    "description": {"type": "string"},
                    "other": {"type": "boolean"},
                },
            },
        },
    }
    schema_path.write(json.dumps(schema))

    run_command(capsys, monkeypatch, main, ["normalize", "--ignore-x-keywords", str(schema_path)])

    result = json.loads(schema_path.read())
    # A base class is extracted if x-tag is ignored.
    assert "allOf" in result["definitions"]["Alpha"]
    assert "allOf" in result["definitions"]["Beta"]


def test_command_ignore_fields(capsys, monkeypatch, schema_path):
    schema = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "definitions": {
            "Alpha": {
                "properties": {
                    "name": {"type": "string"},
                    "widget": {"properties": {"x": {"type": "string"}, "ignore": {"type": "integer"}}},
                }
            },
            "Beta": {
                "properties": {
                    "name": {"type": "string"},
                    "widget": {"properties": {"x": {"type": "string"}, "ignore": {"type": "boolean"}}},
                }
            },
        },
    }
    schema_path.write(json.dumps(schema))

    run_command(capsys, monkeypatch, main, ["normalize", str(schema_path), "--ignore-fields", "ignore"])

    result = json.loads(schema_path.read())
    assert "allOf" in result["definitions"]["Alpha"]
    assert "allOf" in result["definitions"]["Beta"]


def test_command_max_field_prevalence(capsys, monkeypatch, denorm_schema_path):
    run_command(capsys, monkeypatch, main, ["normalize", "--max-field-prevalence", "0.0", str(denorm_schema_path)])

    result = json.loads(denorm_schema_path.read())
    assert "allOf" not in result["definitions"]["Alpha"]
    assert "allOf" not in result["definitions"]["Beta"]


def test_command_oas3(capsys, monkeypatch, oas3_schema_path):
    run_command(capsys, monkeypatch, main, ["normalize", str(oas3_schema_path)])

    result = json.loads(oas3_schema_path.read())

    assert "$schema" in result
    assert list(result["definitions"]) == ["Foo", "Bar"]


def test_command_oas3_get_only(capsys, monkeypatch, oas3_schema_path):
    run_command(capsys, monkeypatch, main, ["normalize", "--get-only", str(oas3_schema_path)])

    result = json.loads(oas3_schema_path.read())

    assert "$schema" in result
    assert list(result["definitions"]) == ["Foo"]

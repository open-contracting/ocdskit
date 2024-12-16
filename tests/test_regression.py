import json
import os
from unittest.mock import Mock

import pytest
from libcove.lib.common import (
    _get_schema_deprecated_paths,
    _get_schema_non_required_ids,
    get_schema_codelist_paths,
    schema_dict_fields_generator,
)

from ocdskit.schema import get_schema_fields
from tests import load

# Remove parts of paths to reduce repetition in EXCEPTIONS.
REMOVE = {"compiledRelease", "records", "releases", "value", "versionedRelease"}

# Some extensions set `type` to "object" but sets `items`.
EXCEPTIONS = {
    # devgateway/ocds_certificate_extension
    # devgateway/ocds_progress_extension
    ('certificates', 'certificateAmount', 'currency'),
    ('certificates', 'certificateAmount', 'exchangeRates', 'currency'),
    ('certificates', 'certificateAmount', 'exchangeRates', 'source'),
    ('certificates', 'totalAmount', 'currency'),
    ('certificates', 'totalAmount', 'exchangeRates', 'currency'),
    ('certificates', 'totalAmount', 'exchangeRates', 'source'),
    ('progress', 'actualValue', 'currency'),
    ('progress', 'actualValue', 'exchangeRates', 'currency'),
    ('progress', 'actualValue', 'exchangeRates', 'source'),
    ('progress', 'investmentValue', 'currency'),
    ('progress', 'investmentValue', 'exchangeRates', 'currency'),
    ('progress', 'investmentValue', 'exchangeRates', 'source'),
    # guatecompras/ocds_partyDetails_publicEntitiesLevelDetails_extension
    ("complaints", "intervenients", "details", "entityType", "id"),
    ("complaints", "intervenients", "details", "legalEntityTypeDetail", "id"),
    ("complaints", "intervenients", "details", "level", "id"),
    ("complaints", "intervenients", "details", "type", "id"),
    ("parties", "details", "entityType", "id"),
    ("parties", "details", "legalEntityTypeDetail", "id"),
    ("parties", "details", "level", "id"),
    ("parties", "details", "type", "id"),
}


@pytest.fixture(params=["a", "b"])
def scenario(request):
    return request.param


@pytest.fixture(params=["release", "record"])
def package_type(request):
    return request.param


# For comparing values to JSON fixtures (tuples versus lists).
def dumpload(data):
    return json.loads(json.dumps(data))


def old(schema, mock):
    set(schema_dict_fields_generator(schema))
    _get_schema_non_required_ids(mock)
    _get_schema_deprecated_paths(mock)
    get_schema_codelist_paths(mock)


def new(schema):
    fields = list(get_schema_fields(schema))

    # Schema fields.
    {f"/{'/'.join(field.path_components)}" for field in fields}
    # Optional IDs.
    {field.path_components for field in fields if field.merge_by_id and not field.required}
    # Deprecated fields.
    {
        field.path_components: (field.deprecated["deprecatedVersion"], field.deprecated["description"])
        for field in fields
        if field.deprecated
    }
    # Codelist fields.
    {
        field.path_components: (field.codelist, field.open_codelist)
        for field in fields
        if field.codelist
    }



def test_benchmark(scenario, package_type, benchmark):
    schema = load(scenario, f"{package_type}-package-schema-dereferenced.json")
    mock = Mock()
    mock.get_pkg_schema_obj = Mock(return_value=schema)

    if os.getenv("BENCHMARK_SAVE"):
        benchmark(old, schema, mock)
    else:
        benchmark(new, schema)


# libcove: get_additional_fields_info uses get_pkg_schema_fields which calls schema_dict_fields_generator, and calls
# get_fields_present_with_examples, which calls fields_present_generator.
def test_schema_dict_fields_generator(scenario, package_type):
    schema = load(scenario, f"{package_type}-package-schema-dereferenced.json")

    expected = dumpload(sorted(set(schema_dict_fields_generator(schema))))

    actual = {
        f"/{'/'.join(field.path_components)}"
        for field in get_schema_fields(schema)
        # libcove doesn't support `patternProperties`.
        if not field.pattern
    }

    assert expected == load(scenario, f"{package_type}-additional.json")
    assert actual == set(expected)


# libcove: get_json_data_missing_ids calls _get_schema_non_required_ids and get_json_data_generic_paths.
def test_get_schema_non_required_ids(scenario, package_type):
    schema = load(scenario, f"{package_type}-package-schema-dereferenced.json")
    mock = Mock()
    mock.get_pkg_schema_obj = Mock(return_value=schema)

    expected = dumpload(_get_schema_non_required_ids(mock))

    actual = {
        field.path_components
        for field in get_schema_fields(schema)
        if field.merge_by_id
        and not field.required
        # libcove doesn't support `oneOf`.
        and field.path_components[:2] != ("records", "releases")
        # libcove trusts `type`, instead of using `properties` and `items`.
        and tuple(c for c in field.path_components if c not in REMOVE) not in EXCEPTIONS
    }

    assert expected == load(scenario, f"{package_type}-missing-ids.json")
    assert actual == {tuple(components) for components in expected}


# libcove: get_json_data_deprecated_fields calls _get_schema_deprecated_paths and get_json_data_generic_paths.
def test_get_schema_deprecated_paths(scenario, package_type):
    schema = load(scenario, f"{package_type}-package-schema-dereferenced.json")
    mock = Mock()
    mock.get_pkg_schema_obj = Mock(return_value=schema)

    expected = dumpload(_get_schema_deprecated_paths(mock))

    actual = {
        field.path_components: (field.deprecated_self["deprecatedVersion"], field.deprecated_self["description"])
        for field in get_schema_fields(schema)
        if field.deprecated
        # libcove doesn't support `oneOf`.
        and field.path_components[:2] != ("records", "releases")
        # libcove doesn't inherit deprecation.
        and field.deprecated_self
    }

    assert expected == load(scenario, f"{package_type}-deprecated.json")
    assert actual == {tuple(components): tuple(value) for components, value in expected}


# libcove: get_additional_codelist_values uses get_schema_codelist_paths and calls _generate_data_path.
def test_get_schema_codelist_paths(scenario, package_type):
    schema = load(scenario, f"{package_type}-package-schema-dereferenced.json")
    mock = Mock()
    mock.get_pkg_schema_obj = Mock(return_value=schema)

    expected = dumpload([[key, value] for key, value in get_schema_codelist_paths(mock).items()])

    # {("tender", "status"): ("tenderStatus.csv", False), ...}
    actual = {
        field.path_components: (field.codelist, field.open_codelist)
        for field in get_schema_fields(schema)
        if field.codelist
        # libcove trusts `type`, instead of using `properties` and `items`.
        and tuple(c for c in field.path_components if c not in REMOVE) not in EXCEPTIONS
    }

    assert expected == load(scenario, f"{package_type}-codelist.json")
    assert actual == {tuple(components): tuple(value) for components, value in expected}

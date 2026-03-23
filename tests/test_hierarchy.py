import pytest

from ocdskit.hierarchy import get_base_class_name, get_base_classes_via_fca


@pytest.mark.parametrize(
    ("class_names", "expected"),
    [
        ([], None),  # < 2 names
        (["OnlyOne"], None),  # < 2 names
        (["Abc", "Mno"], None),  # no LCS
        (["award detail", "award summary"], "Award"),  # space
        (["award.detail", "award.summary"], "Award"),  # dot
        (["award_detail", "award_summary"], "Award"),  # underscore
        (["award-detail", "award-summary"], "Award"),  # dash
        (["AwardDetail", "AwardSummary"], "Award"),  # camelCase
        (["AwardAwardDetail", "AwardAwardSummary"], "Award"),  # unique
    ],
)
def test_get_base_class_name(class_names, expected):
    assert get_base_class_name(class_names) == expected


@pytest.mark.parametrize(("prefix", "expected"), [("", "Award"), ("mylib.", "mylib.Award")])
def test_get_base_class_name_prefix(prefix, expected):
    assert get_base_class_name(["AwardDetail", "AwardSummary"], prefix=prefix) == expected


@pytest.mark.parametrize(
    "classes",
    [
        {"AwardDetail": {"x:1", "y:2"}},  # Only one class, below min_extent=2
        {"AwardDetail": {"x:1"}, "AwardSummary": {"x:1"}},  # Only one property, below min_intent=2
    ],
)
def test_get_base_classes_via_fca_min_extent_max_extent(classes):
    result = get_base_classes_via_fca(classes)

    assert result == []


def test_get_base_classes_via_fca_max_field_prevalence():
    classes = {
        "AwardDetail": {"x:1", "y:2"},
        "AwardSummary": {"x:1", "y:2"},
    }
    result = get_base_classes_via_fca(classes, max_field_prevalence=0.9)

    assert result == []


def test_get_base_classes_via_fca():
    classes = {
        "AwardDetail": {"x:1", "y:2"},
        "AwardSummary": {"x:1", "y:2"},
    }
    result = get_base_classes_via_fca(classes)

    assert result == [
        {
            "name": "Award",
            "members": ["AwardDetail", "AwardSummary"],
            "props": {"x:1", "y:2"},
        },
    ]


def test_get_base_classes_via_fca_name_fallback():
    classes = {
        "Abc": {"x:1", "y:2"},
        "Mno": {"x:1", "y:2"},
    }
    result = get_base_classes_via_fca(classes)

    assert result == [
        {
            "name": "XY",  # get_base_class_name() returns None
            "members": ["Abc", "Mno"],
            "props": {"x:1", "y:2"},
        }
    ]


def test_get_base_classes_via_fca_name_collision():
    classes = {
        "Award": {"x:1", "y:2"},
        "AwardDetail": {"x:1", "y:2"},
    }
    result = get_base_classes_via_fca(classes)

    assert result == [
        {
            "name": "AwardXY",  # get_base_class_name() returns "Award"
            "members": ["Award", "AwardDetail"],
            "props": {"x:1", "y:2"},
        }
    ]


def test_get_base_classes_via_fca_name_counter():
    classes = {
        "Award": {"x:1", "y:2"},
        "AwardDetail": {"x:1", "y:2"},
        "AwardXY": {"x:1", "y:2"},
    }
    result = get_base_classes_via_fca(classes)

    assert result == [
        {
            "name": "AwardXY2",  # number suffixed
            "members": ["Award", "AwardDetail", "AwardXY"],
            "props": {"x:1", "y:2"},
        },
    ]


def test_get_base_classes_via_fca_intent_less_than_inherited_properties():
    classes = {
        "AwardDetail": {"a:1", "b:2", "c:3", "d:4", "e:5", "f:6"},
        "AwardSummary": {"a:1", "b:2", "c:3", "d:4", "e:5", "f:6"},
        "AwardLeft": {"a:1", "b:2", "c:3"},
        "AwardRight": {"d:4", "e:5", "f:6"},
    }
    result = get_base_classes_via_fca(classes)

    # No "AwardABCDEF" for the concept with all properties and [AwardDetail,AwardSummary] members.
    assert result == [
        {
            "name": "Award",
            "members": ["AwardDetail", "AwardSummary", "AwardRight"],
            "props": {"d:4", "e:5", "f:6"},
        },
        {
            "name": "AwardA",
            "members": ["AwardDetail", "AwardSummary", "AwardLeft"],
            "props": {"a:1", "b:2", "c:3"},
        },
    ]

import pytest

from ocdskit.hierarchy import get_base_class_name, get_base_classes_via_fca


@pytest.mark.parametrize(
    ("class_names", "expected"),
    [
        ([], None),  # < 2
        (["OnlyOne"], None),  # < 2
        (["Abc", "Xyz"], None),  # no LCS
        (["AwardAwardDetail", "AwardAwardSummary"], "ocdskit.Award"),  # unique
        (["AwardDetail", "AwardSummary"], "ocdskit.Award"),
        (["PlanningBudget", "PlanningMilestone"], "ocdskit.Planning"),
        (["award.detail", "award.summary"], "ocdskit.Award"),
        (["award_detail", "award_summary"], "ocdskit.Award"),
        (["award-detail", "award-summary"], "ocdskit.Award"),
    ],
)
def test_get_base_class_name(class_names, expected):
    assert get_base_class_name(class_names) == expected


@pytest.mark.parametrize(("prefix", "expected"), [("", "Award"), ("mylib.", "mylib.Award")])
def test_get_base_class_name_prefix(prefix, expected):
    assert get_base_class_name(["AwardDetail", "AwardSummary"], prefix=prefix) == expected


def test_get_base_classes_via_fca_happy_path():
    classes = {
        "AwardDetail": {"x:1", "y:2"},
        "AwardSummary": {"x:1", "y:2"},
    }
    result = get_base_classes_via_fca(classes)

    assert len(result) == 1
    assert result[0]["name"] == "ocdskit.Award"
    assert set(result[0]["members"]) == {"AwardDetail", "AwardSummary"}
    assert result[0]["props"] == {"x:1", "y:2"}


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
    classes = {"AwardDetail": {"x:1", "y:2"}, "AwardSummary": {"x:1", "y:2"}}
    result = get_base_classes_via_fca(classes, max_field_prevalence=0.9)

    assert result == []


def test_get_base_classes_via_fca_name_fallback():
    classes = {"Abc": {"x:1", "y:2"}, "Xyz": {"x:1", "y:2"}}
    result = get_base_classes_via_fca(classes)

    assert result == [
        {
            "members": ["Abc", "Xyz"],
            "name": "BaseXY",  # "Base" name
            "props": {"x:1", "y:2"},
        }
    ]


def test_get_base_classes_via_fca_name_collision_with_existing_class():
    classes = {"ocdskit.Award": {"x:1", "y:2"}, "AwardDetail": {"x:1", "y:2"}}
    result = get_base_classes_via_fca(classes)

    assert result == [
        {
            "members": ["ocdskit.Award", "AwardDetail"],
            "name": "ocdskit.AwardXY",  # not "ocdskit.Award"
            "props": {"x:1", "y:2"},
        }
    ]


def test_get_base_classes_via_fca_covered_by_parents():
    # AwardDetail and AwardSummary have all 6 props. AwardLeft has {a,b,c}. AwardRight has {d,e,f}.
    # The [AwardDetail,AwardSummary] concept passes min_extent/min_intent but its full intent
    # equals the union of its two parents' intents, so it is filtered.
    classes = {
        "AwardDetail": {"a:1", "b:2", "c:3", "d:4", "e:5", "f:6"},
        "AwardSummary": {"a:1", "b:2", "c:3", "d:4", "e:5", "f:6"},
        "AwardLeft": {"a:1", "b:2", "c:3"},
        "AwardRight": {"d:4", "e:5", "f:6"},
    }
    result = get_base_classes_via_fca(classes)

    assert result == [
        {
            "members": ["AwardDetail", "AwardSummary", "AwardRight"],
            "name": "ocdskit.Award",
            "props": {"d:4", "e:5", "f:6"},
        },
        {
            "members": ["AwardDetail", "AwardSummary", "AwardLeft"],
            "name": "ocdskit.AwardA",
            "props": {"a:1", "b:2", "c:3"},
        },
    ]

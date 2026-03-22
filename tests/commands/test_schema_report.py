from ocdskit.__main__ import main
from tests import path, run_command


def test_command(capsys, monkeypatch):
    actual = run_command(
        capsys,
        monkeypatch,
        main,
        ["schema-report", "--codelists", "--definitions", "--min-occurrences", "2", path("test-schema.json")],
    )

    assert actual.out == (
        "codelist,openCodelist\n"
        "a.csv,False/True\n"
        "b.csv,False\n"
        "c.csv,False\n"
        "d.csv,False\n"
        "\n"
        " 2: {'codelist': 'a.csv', 'openCodelist': True, 'type': ['string', 'null']}\n"
    )


def test_command_definitions(capsys, monkeypatch):
    actual = run_command(
        capsys,
        monkeypatch,
        main,
        ["schema-report", "--definitions", "--min-occurrences", "2", path("test-schema.json")],
    )

    assert "codelist,openCodelist" not in actual.out
    assert ":" in actual.out


def test_command_min_occurrences(capsys, monkeypatch):
    actual = run_command(
        capsys,
        monkeypatch,
        main,
        ["schema-report", "--definitions", "--min-occurrences", "1", path("test-schema.json")],
    )

    assert "codelist,openCodelist" not in actual.out
    assert "1:" in actual.out


def test_command_codelists(capsys, monkeypatch):
    actual = run_command(
        capsys,
        monkeypatch,
        main,
        ["schema-report", "--codelists", path("test-schema.json")],
    )

    assert "codelist,openCodelist" in actual.out
    assert ":" not in actual.out


def test_command_field_count(capsys, monkeypatch):
    actual = run_command(
        capsys,
        monkeypatch,
        main,
        ["schema-report", "--field-count", path("test-schema.json")],
    )

    assert actual.out == "6 fields\n"

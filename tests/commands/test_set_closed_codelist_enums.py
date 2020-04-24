import os.path
from tempfile import TemporaryDirectory

from ocdskit.cli.__main__ import main
from tests import assert_command, assert_command_error, read

schema = read('test-schema.json')

schema_with_enum = '''{
  "properties": {
    "closedStringNull": {
      "type": [
        "string",
        "null"
      ],
      "codelist": "a.csv",
      "openCodelist": false,
      "enum": [
        "foo",
        "bar",
        null
      ]
    },
    "closedArrayNull": {
      "type": [
        "array",
        "null"
      ],
      "codelist": "b.csv",
      "openCodelist": false,
      "items": {
        "type": "string",
        "enum": [
          "foo",
          "bar"
        ]
      }
    },
    "closedString": {
      "type": "string",
      "codelist": "c.csv",
      "openCodelist": false,
      "enum": [
        "foo",
        "bar"
      ]
    },
    "closedDisorder": {
      "type": "string",
      "codelist": "d.csv",
      "openCodelist": false,
      "enum": [
        "bar",
        "foo"
      ]
    },
    "open": {
      "type": [
        "string",
        "null"
      ],
      "codelist": "a.csv",
      "openCodelist": true
    },
    "same": {
      "type": [
        "string",
        "null"
      ],
      "codelist": "a.csv",
      "openCodelist": true
    }
  }
}
'''

schema_with_modification = '''{
  "properties": {
    "closedStringNull": {
      "type": [
        "string",
        "null"
      ],
      "codelist": "a.csv",
      "openCodelist": false,
      "enum": [
        "foo",
        "bar",
        "baz",
        null
      ]
    },
    "closedArrayNull": {
      "type": [
        "array",
        "null"
      ],
      "codelist": "b.csv",
      "openCodelist": false,
      "items": {
        "type": "string",
        "enum": [
          "foo"
        ]
      }
    },
    "closedString": {
      "type": "string",
      "codelist": "c.csv",
      "openCodelist": false,
      "enum": [
        "foo",
        "bar"
      ]
    },
    "closedDisorder": {
      "type": "string",
      "codelist": "d.csv",
      "openCodelist": false,
      "enum": [
        "bar",
        "foo"
      ]
    },
    "open": {
      "type": [
        "string",
        "null"
      ],
      "codelist": "a.csv",
      "openCodelist": true
    },
    "same": {
      "type": [
        "string",
        "null"
      ],
      "codelist": "a.csv",
      "openCodelist": true
    }
  }
}
'''

codelist = 'Code\nfoo\nbar\n'


def test_command(monkeypatch, tmpdir):
    tmpdir.join('release-schema.json').write(schema)

    tmpdir.mkdir('codelists')
    for basename in ('a', 'b', 'c', 'd'):
        tmpdir.join('codelists', '{}.csv'.format(basename)).write(codelist)

    assert_command(monkeypatch, main, ['set-closed-codelist-enums', str(tmpdir)], '')
    assert tmpdir.join('release-schema.json').read() == schema_with_enum


def test_unused_codelists(monkeypatch, caplog, tmpdir):
    tmpdir.join('release-schema.json').write(schema)

    tmpdir.mkdir('codelists')
    for basename in ('a', 'b', 'c', 'd', 'e'):
        tmpdir.join('codelists', '{}.csv'.format(basename)).write(codelist)

    assert_command(monkeypatch, main, ['set-closed-codelist-enums', str(tmpdir)], '')
    assert tmpdir.join('release-schema.json').read() == schema_with_enum

    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == 'ERROR'
    assert caplog.records[0].message == 'unused codelists: e.csv'


def test_missing_codelists(monkeypatch, caplog, tmpdir):
    tmpdir.join('release-schema.json').write(schema)

    tmpdir.mkdir('codelists')

    excinfo = assert_command_error(monkeypatch, main, ['set-closed-codelist-enums', str(tmpdir)], error=KeyError)

    assert tmpdir.join('release-schema.json').read() == schema

    assert len(caplog.records) == 0
    assert excinfo.value.args == ('a.csv',)


def test_missing_targets(monkeypatch, caplog, tmpdir):
    tmpdir.join('release-schema.json').write(schema)

    tmpdir.mkdir('codelists')
    for basename in ('a', 'b', 'c', 'd', '+e'):
        tmpdir.join('codelists', '{}.csv'.format(basename)).write(codelist)

    excinfo = assert_command_error(monkeypatch, main, ['set-closed-codelist-enums', str(tmpdir)], error=KeyError)

    assert tmpdir.join('release-schema.json').read() == schema

    assert len(caplog.records) == 0
    assert excinfo.value.args == ('e.csv',)


def test_conflicting_codelists(monkeypatch, caplog, tmpdir):
    with TemporaryDirectory() as d:
        for directory in (tmpdir, d):
            os.mkdir(os.path.join(directory, 'codelists'))

            with open(os.path.join(directory, 'release-schema.json'), 'w') as f:
                f.write(schema)

        for basename in ('a', 'b', 'c', 'd'):
            tmpdir.join('codelists', '{}.csv'.format(basename)).write(codelist)

        with open(os.path.join(d, 'codelists', 'a.csv'), 'w') as f:
            f.write('Code\nbaz\n')

        assert_command(monkeypatch, main, ['set-closed-codelist-enums', str(tmpdir), d], '')
        with open(os.path.join(d, 'release-schema.json')) as f:
            assert f.read() == schema_with_enum

        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == 'ERROR'
        assert caplog.records[0].message == 'conflicting codelists: a.csv'


def test_modified_codelists(monkeypatch, tmpdir):
    with TemporaryDirectory() as d:
        for directory in (tmpdir, d):
            os.mkdir(os.path.join(directory, 'codelists'))

            with open(os.path.join(directory, 'release-schema.json'), 'w') as f:
                f.write(schema)

        for basename in ('a', 'b', 'c', 'd'):
            tmpdir.join('codelists', '{}.csv'.format(basename)).write(codelist)

        with open(os.path.join(d, 'codelists', '+a.csv'), 'w') as f:
            f.write('Code\nbaz\n')

        with open(os.path.join(d, 'codelists', '-b.csv'), 'w') as f:
            f.write('Code,Description\nbar,bzz\n')

        assert_command(monkeypatch, main, ['set-closed-codelist-enums', str(tmpdir), d], '')
        with open(os.path.join(d, 'release-schema.json')) as f:
            assert f.read() == schema_with_modification

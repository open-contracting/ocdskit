from ocdskit.__main__ import main
from tests import assert_command, assert_command_error, path


def test_command(capsys, monkeypatch):
    assert_command(capsys, monkeypatch, main,
                   ['mapping-sheet', '--infer-required', path('release-schema.json')],
                   'mapping-sheet.csv')


def test_command_codelist(capsys, monkeypatch):
    assert_command(capsys, monkeypatch, main,
                   ['mapping-sheet', '--infer-required', '--codelist', path('release-schema.json')],
                   'mapping-sheet_codelist.csv')


def test_command_no_deprecated(capsys, monkeypatch):
    assert_command(capsys, monkeypatch, main,
                   ['mapping-sheet', '--infer-required', '--no-deprecated', path('release-schema.json')],
                   'mapping-sheet_no-deprecated.csv')


def test_command_order_by(capsys, monkeypatch):
    assert_command(capsys, monkeypatch, main,
                   ['mapping-sheet', '--infer-required', '--order-by', 'path', path('release-schema.json')],
                   'mapping-sheet_order-by.csv')


def test_command_extension(capsys, monkeypatch):
    url = 'https://github.com/open-contracting-extensions/ocds_lots_extension/archive/v1.1.4.zip'

    assert_command(capsys, monkeypatch, main,
                   ['mapping-sheet', '--infer-required', path('release-schema.json'), '--extension', url],
                   'mapping-sheet_extension.csv')


def test_command_extension_field(capsys, monkeypatch):
    assert_command(capsys, monkeypatch, main,
                   ['mapping-sheet', '--infer-required', '--extension-field', 'extension',
                    path('release-schema.json')],
                   'mapping-sheet_extension-field.csv')


def test_command_extension_and_extension_field(capsys, monkeypatch):
    url = 'https://github.com/open-contracting-extensions/ocds_lots_extension/archive/v1.1.4.zip'

    assert_command(capsys, monkeypatch, main,
                   ['mapping-sheet', '--infer-required', '--extension-field', 'extension',
                    path('release-schema.json'), '--extension', url],
                   'mapping-sheet_extension_extension-field.csv')


def test_command_extension_and_extension_field_alternative(capsys, monkeypatch):
    url = 'https://github.com/open-contracting-extensions/ocds_lots_extension/archive/v1.1.4.zip'

    assert_command(capsys, monkeypatch, main,
                   ['mapping-sheet', '--infer-required', '--extension-field', 'alternative',
                    path('release-schema.json'), '--extension', url],
                   'mapping-sheet_extension_extension-field.csv')


def test_command_extension_and_extension_field_and_no_inherit_extension(capsys, monkeypatch):
    url = 'https://github.com/open-contracting-extensions/ocds_lots_extension/archive/v1.1.4.zip'

    assert_command(capsys, monkeypatch, main,
                   ['mapping-sheet', '--infer-required', '--extension-field', 'extension',
                    path('release-schema.json'), '--extension', url, '--no-inherit-extension'],
                   'mapping-sheet_extension_extension-field_no-inherit-extension.csv')


def test_command_extension_and_extension_field_and_language(capsys, monkeypatch):
    url = 'https://extensions.open-contracting.org/es/extensions/lots/v1.1.5/'

    assert_command(capsys, monkeypatch, main,
                   ['mapping-sheet', '--infer-required', '--extension-field', 'extension',
                    path('release-schema.json'), '--extension', url, '--language', 'es'],
                   'mapping-sheet_extension_extension-field_language.csv')


def test_command_extension_and_extension_field_location(capsys, monkeypatch):
    url = 'https://github.com/open-contracting-extensions/ocds_location_extension/archive/v1.1.4.zip'

    assert_command(capsys, monkeypatch, main,
                   ['mapping-sheet', '--infer-required', '--extension-field', 'extension',
                    path('release-schema.json'), '--extension', url],
                   'mapping-sheet_extension_extension-field_location.csv')


def test_command_extension_and_extension_field_array(capsys, monkeypatch):
    url = 'https://github.com/open-contracting-extensions/ocds_additionalContactPoints_extension/archive/40d6858.zip'

    assert_command(capsys, monkeypatch, main,
                   ['mapping-sheet', '--infer-required', '--extension-field', 'extension',
                    path('release-schema.json'), '--extension', url],
                   'mapping-sheet_extension_extension-field_array.csv')


def test_command_oc4ids(capsys, monkeypatch):
    assert_command(capsys, monkeypatch, main,
                   ['mapping-sheet', path('project-schema.json')],
                   'mapping-sheet_oc4ids.csv')


def test_command_bods(capsys, monkeypatch):
    assert_command(capsys, monkeypatch, main,
                   ['mapping-sheet', '--order-by', 'path', path('bods/person-statement.json')],
                   'mapping-sheet_bods.csv')


def test_command_sedl(capsys, monkeypatch):
    assert_command(capsys, monkeypatch, main,
                   ['mapping-sheet', path('sedl-schema.json')],
                   'mapping-sheet_sedl.csv')


def test_command_order_by_nonexistent(capsys, monkeypatch, caplog):
    assert_command_error(capsys, monkeypatch, main, ['mapping-sheet', '--order-by',
                                                     'nonexistent', path('release-schema.json')])

    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == 'CRITICAL'
    assert caplog.records[0].message == "the column 'nonexistent' doesn't exist – did you make a typo?"

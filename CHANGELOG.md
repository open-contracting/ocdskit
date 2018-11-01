# Changelog

# 0.0.3 (2018-11-01)

New options:

* compile: `--versioned`

New commands:

* release-package

Other changes:

* Add helpful error messages if:
  * the input is not [line-delimited JSON](https://en.wikipedia.org/wiki/JSON_streaming) data;
  * the input to the `indent` command is not valid JSON.
* Print UTF-8 characters instead of escape sequences.
* Rename base exception class from `ReportError` to `OCDSKitError`.

# 0.0.2 (2018-03-14)

New options:

* validate: `--check-urls` and `--timeout`

New commands:

* indent
* schema-report
* schema-strict
* set-closed-codelist-enums

# 0.0.1 (2017-12-25)

New commands:

* combine-record-packages
* combine-release-packages
* compile
* mapping-sheet
* measure
* tabulate
* validate

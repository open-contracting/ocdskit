Schema Commands
===============

The following commands may be used when working with:

* Open Contracting Data Standard (OCDS), plus its extensions and profiles
* Open Contracting for Infrastructure Data Standard (OC4IDS)
* Beneficial Ownership Data Standard (BODS)
* Social Investment Data Lab Specification (SEDL)

Optional arguments for all commands (if relevant) are:

* ``--encoding ENCODING`` the file encoding
* ``--ascii`` print escape sequences instead of UTF-8 characters
* ``--pretty`` pretty print output

mapping-sheet
-------------

Generates a spreadsheet with all field paths in a JSON Schema.

Required arguments:

* ``file`` the schema file

Optional arguments:

* ``--order-by COLUMN`` sort the spreadsheet's rows by this column
* ``--infer-required`` infer whether fields are required (use with OCDS schema)
* ``--extension`` patch the release schema with this extension
* ``--extension-field`` add an "extension" column for the name of the extension in which each field was defined

The ``--extension`` option must be declared after the ``file`` argument. The ``--extension`` option accepts multiple values, which can be extension metadata URLs, base URLs and/or download URLs. For example::

    ocdskit mapping-sheet release-schema.json --extension \
      https://raw.githubusercontent.com/open-contracting-extensions/ocds_coveredBy_extension/master/extension.json \
      https://raw.githubusercontent.com/open-contracting-extensions/ocds_options_extension/master/ \
      https://github.com/open-contracting-extensions/ocds_techniques_extension/archive/master.zip \
      > mapping-sheet.csv

The ``--extension-field`` option can be used with or without the ``--extension`` option.

-  If the ``--extension`` option is set, then the ``--extension-field`` option may be set to any value. In all cases, the result is a mapping sheet with an "extension" column, containing the name of the extension in which each field was defined.

-  If the ``--extension`` option is not set, then the ``--extension-field`` option must be set to the property in the JSON schema containing the name of the extension in which each field was defined. If there is no such property, then the result is a mapping sheet with no values in its "extension" column.

For a description of the columns of the spreadsheet, see the :doc:`../api/mapping_sheet` module.

::

    ocdskit mapping-sheet path/to/project-schema.json > mapping-sheet.csv
    ocdskit mapping-sheet --infer-required path/to/release-schema.json > mapping-sheet.csv
    ocdskit mapping-sheet --order-by path path/to/person-statement.json > mapping-sheet.csv
    ocdskit mapping-sheet --infer-required path/to/release-schema.json --extension https://github.com/open-contracting-extensions/ocds_lots_extension/archive/master.zip > mapping-sheet.csv

For the Python API, see :meth:`ocdskit.mapping_sheet.mapping_sheet`.

schema-report
-------------

Reports details of a JSON Schema (open and closed codelists, definitions that can use a common $ref in the versioned release schema).

Optional arguments:

* ``--no-codelists`` skip reporting open and closed codelists
* ``--no-definitions`` skip reporting definitions that can use a common $ref in the versioned release schema
* ``--min-occurrences`` report definitions that occur at least this many times (default 5)

::

    cat path/to/release-schema.json | ocdskit schema-report

schema-strict
-------------

For any required field, adds "minItems" if an array, "minProperties" if an object and "minLength" if a string and "enum", "format" and "pattern" are not set. For any array field, adds "uniqueItems".

Optional arguments:

* ``--no-unique-items`` don't add "uniqueItems" properties to array fields

::

    cat path/to/release-schema.json | ocdskit schema-strict --pretty > out.json

set-closed-codelist-enums
-------------------------

Sets the enum in a JSON Schema to match the codes in the CSV files of closed codelists.

::

    ocdskit set-closed-codelist-enums path/to/standard path/to/extension1 path/to/extension2

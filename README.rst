OCDS Kit
========

|PyPI version| |Build Status| |Dependency Status| |Coverage Status|

A suite of command-line tools for working with OCDS data.

::

    pip install ocdskit
    ocdskit --help

To install from source:

::

    pip install --upgrade .

To see all commands available, run:

::

    ocdskit --help

Most ``ocdskit`` tools accept JSON data from standard input. To report on a remote file:

::

    curl <url> | ocdskit <command>

To report on a local file:

::

    cat <path> | ocdskit <command>

For exploring JSON data, consider using `jq <https://stedolan.github.io/jq/>`__.

Commands
--------

Optional arguments for all commands are:

* ``-h``, ``--help`` show the help message and exit
* ``--encoding ENCODING`` the file encoding
* ``--pretty`` pretty print output

combine-record-packages
~~~~~~~~~~~~~~~~~~~~~~~

Reads record packages from standard input, collects packages and records, and prints one record package.

::

    cat tests/fixtures/record-package_*.json | ocdskit combine-record-packages > out.json

combine-release-packages
~~~~~~~~~~~~~~~~~~~~~~~~

Reads release packages from standard input, collects releases, and prints one release package.

::

    cat tests/fixtures/release-package_*.json | ocdskit combine-release-packages > out.json

compile
~~~~~~~

Reads release packages from standard input, merges the releases by OCID, and prints the compiled releases.

::

    cat tests/fixtures/realdata/release-package-1.json | ocdskit compile > out.json

indent
~~~~~~

Indents JSON files by modifying the given files in-place.

Optional arguments:

* ``-r``, ``--recursive`` recursively indent JSON files
* ``--indent INDENT`` indent level

::

    ocdskit indent --recursive file1 path/to/directory file2

mapping-sheet
~~~~~~~~~~~~~

Generates a spreadsheet with all field paths from an OCDS schema.

::

    cat path/to/release-schema.json | ocdskit mapping-sheet > mapping-sheet.csv

schema-report
~~~~~~~~~~~~~

Reports details of a JSON Schema (open and closed codelists).

::

    cat path/to/release-schema.json | ocdskit schema-report

schema-strict
~~~~~~~~~~~~~

For any required field, adds "minItems" if an array, "minProperties" if an object and "minLength" if a string and "enum", "format" and "pattern" are not set.

::

    cat path/to/release-schema.json | ocdskit schema-strict > out.json

set-closed-codelist-enums
~~~~~~~~~~~~~~~~~~~~~~~~~

Sets the enum in a JSON Schema to match the codes in the CSV files of closed codelists.

::

    ocdskit set-closed-codelist-enums path/to/standard path/to/extension1 path/to/extension2

tabulate
~~~~~~~~

Load packages into a database.

Optional arguments:

* ``--drop`` drop all tables before loading
* ``--schema SCHEMA`` the release-schema.json to use

::

    cat release_package.json | ocdskit tabulate sqlite:///data.db

For the format of ``database_url``, see the `SQLAlchemy documentation <https://docs.sqlalchemy.org/en/rel_1_1/core/engines.html#database-urls>`__.

validate
~~~~~~~~

Reads JSON data from standard input, validates it against the schema, and prints errors.

Optional arguments:

* ``--schema SCHEMA`` the schema to validate against
* ``--check-urls`` check the HTTP status code if "format": "uri"
* ``--timeout TIMEOUT`` timeout (seconds) to GET a URL

::

    cat tests/fixtures/* | ocdskit validate

Examples
--------

Example 1
~~~~~~~~~

Download a list of release packages:

::

    curl http://www.contratosabiertos.cdmx.gob.mx/api/contratos/array > release_packages.json

Transform it to a stream of release packages, and validate each:

::

    jq -crM '.[]' release_packages.json | ocdskit validate --schema http://standard.open-contracting.org/schema/1__0__3/release-package-schema.json

Or, validate each with a local schema file:

::

    jq -crM '.[]' release_packages.json | ocdskit validate --schema file:///path/to/release-package-schema.json

Transform it to a stream of compiled releases:

::

    jq -crM '.[]' release_packages.json | ocdskit compile > compiled_releases.json

Find a compiled release with a given ``ocid`` (replace the ``…``):

::

    jq 'select(.ocid == "OCDS-87SD3T-AD-SF-DRM-063-2015")' compiled_releases.json

Measure indicators across release packages:

::

    cat release_packages.json | ocdskit --encoding iso-8859-1 measure --currency MXN

Example 2
~~~~~~~~~

Download a list of record packages:

::

    curl https://drive.google.com/uc?export=download&id=1HzVMdv9bryEw6pg80RwmJd3Le31SY1TI > record_packages.json

Combine it into a single record package:

::

    jq -crM '.[]' record_packages.json | ocdskit combine-record-packages > record_package.json

If the file is too large for the OCDS Validator, you can break it into
parts. First, transform the list into a stream:

::

    jq -crM '.[]' record_packages.json > stream.json

Combine the first 10,000 items from the stream into a single record
package:

::

    head -n 10000 stream.json | ocdskit combine-record-packages > record_package-1.json

Then, combine the next 10,000 items from the stream into a single record package:

::

    tail -n +10001 stream.json | head -n 10000 | ocdskit combine-record-packages > record_package-2.json

And so on:

::

    tail -n +20001 stream.json | head -n 10000 | ocdskit combine-record-packages > record_package-3.json

Copyright (c) 2017 Open Contracting Partnership, released under the BSD license

.. |PyPI version| image:: https://badge.fury.io/py/ocdskit.svg
   :target: https://badge.fury.io/py/ocdskit
.. |Build Status| image:: https://secure.travis-ci.org/open-contracting/ocdskit.png
   :target: https://travis-ci.org/open-contracting/ocdskit
.. |Dependency Status| image:: https://gemnasium.com/open-contracting/ocdskit.png
   :target: https://gemnasium.com/open-contracting/ocdskit
.. |Coverage Status| image:: https://coveralls.io/repos/open-contracting/ocdskit/badge.png
   :target: https://coveralls.io/r/open-contracting/ocdskit

OCDS Kit
========

|PyPI version| |Build Status| |Dependency Status| |Coverage Status|

A suite of command-line tools for working with OCDS data, including: creating release packages from releases; creating record packages from release packages; creating compiled releases and versioned releases from release packages; combining small packages into large packages; splitting large packages into small packages.

::

    pip install ocdskit
    ocdskit --help

Or, `use OCDS Kit within a Docker container <https://hub.docker.com/r/ricardoe/ocdskit/>`__.

To see all commands available, run:

::

    ocdskit --help

Input format
------------

Most ``ocdskit`` tools accept only `line-delimited JSON <https://en.wikipedia.org/wiki/JSON_streaming>`__ data from standard input. To process a remote file:

::

    curl <url> | ocdskit <command>

To process a local file:

::

    cat <path> | ocdskit <command>

If the JSON data is not line-delimited, you can make it line-delimited using `jq <https://stedolan.github.io/jq/>`__:

::

    curl <url> | jq -crM . | ocdskit <command>

For exploring JSON data, consider using ``jq``. See `our tips on using jq </docs/Using_jq.md>`__ and the `command-line </docs/Using_the_command_line.md>`__.

Commands
--------

Optional arguments for all commands are:

* ``-h``, ``--help`` show the help message and exit
* ``--encoding ENCODING`` the file encoding
* ``--pretty`` pretty print output

compile
~~~~~~~

Reads release packages from standard input, merges the releases by OCID, and prints the compiled releases.

Optional arguments:

* ``--package`` wrap the compiled releases in a record package
* ``--versioned`` if ``--package`` is set, include versioned releases in the record package; otherwise, print versioned releases instead of compiled releases

::

    cat tests/fixtures/realdata/release-package-1.json | ocdskit compile > out.json

package-releases
~~~~~~~~~~~~~~~~

Reads releases from standard input, and prints one release package. You will need to edit the package metadata.

Optional positional arguments:

* ``extension`` add this extension to the package

::

    cat tests/fixtures/release_*.json | ocdskit package-releases > out.json

To convert record packages to a release package, you can use `use jq </docs/Using_jq.md>`__ to get the releases from the record packages, and the ``package-releases`` command to print a release package. You will need to edit the package metadata.

::

    cat tests/fixtures/realdata/record-package* | jq -crM .records[].releases[] | ocdskit package-releases

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

split-record-packages
~~~~~~~~~~~~~~~~~~~~~

Reads record packages from standard input, and prints smaller record packages for each.

::

    cat tests/fixtures/realdata/record-package-1.json | ocdskit split-record-packages 2 | split -l 1 -a 4

The ``split`` command will write files named ``xaaaa``, ``xaaab``, ``xaaac``, etc. Don't combine the OCDS Kit ``--pretty`` option with the ``split`` command.

split-release-packages
~~~~~~~~~~~~~~~~~~~~~~

Reads release packages from standard input, and prints smaller release packages for each.

::

    cat tests/fixtures/realdata/release-package-1.json | ocdskit split-release-packages 2 | split -l 1 -a 4

The ``split`` command will write files named ``xaaaa``, ``xaaab``, ``xaaac``, etc. Don't combine the OCDS Kit ``--pretty`` option with the ``split`` command.

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
* ``--verbose`` print items without validation errors

::

    cat tests/fixtures/* | ocdskit validate

Generic Commands
----------------

The following commands may be used when working with JSON data, in general.

indent
~~~~~~

Indents JSON files by modifying the given files in-place.

Optional arguments:

* ``-r``, ``--recursive`` recursively indent JSON files
* ``--indent INDENT`` indent level

::

    ocdskit indent --recursive file1 path/to/directory file2

Schema Commands
---------------

The following commands may be used when working with OCDS schema from extensions, profiles, or OCDS itself.

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

If the file is too large for the OCDS Validator, you can break it into parts. First, transform the list into a stream:

::

    jq -crM '.[]' record_packages.json > stream.json

Combine the first 10,000 items from the stream into a single record package:

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
.. |Dependency Status| image:: https://requires.io/github/open-contracting/ocdskit/requirements.svg
   :target: https://requires.io/github/open-contracting/ocdskit/requirements/
.. |Coverage Status| image:: https://coveralls.io/repos/github/open-contracting/ocdskit/badge.svg?branch=master
   :target: https://coveralls.io/github/open-contracting/ocdskit?branch=master

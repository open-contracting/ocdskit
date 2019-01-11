OCDS Kit
========

|PyPI Version| |Build Status| |Coverage Status| |Python Version|

A suite of command-line tools for working with OCDS data, including:

* creating release packages from releases
* creating record packages from release packages
* creating compiled releases and versioned releases from release packages
* combining small packages into large packages
* splitting large packages into small packages
* load packages into a database
* validate JSON data against a JSON schema
* generate a spreadsheet version of OCDS schema

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

For exploring JSON data, consider using ``jq``. See `our tips on using jq <https://github.com/open-contracting/ocdskit/blob/master/docs/Using_jq.md>`__ and the `command-line <https://github.com/open-contracting/ocdskit/blob/master/docs/Using_the_command_line.md>`__.

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

* ``--schema SCHEMA`` the URL or path of the release schema to use
* ``--package`` wrap the compiled releases in a record package
* ``--uri URI`` if ``--package`` is set, set the record package's ``uri`` to this value
* ``--published-date PUBLISHED_DATE`` if ``--package`` is set, set the record package's ``publishedDate`` to this value
* ``--linked-releases`` if ``--package`` is set, use linked releases instead of full releases
* ``--versioned`` if ``--package`` is set, include versioned releases in the record package; otherwise, print versioned releases instead of compiled releases

::

    cat tests/fixtures/realdata/release-package-1.json | ocdskit compile > out.json

upgrade
~~~~~~~

Upgrades packages and releases from an old version of OCDS to a new version. Any data not in the old version is passed through. **Note:** Versioned releases within a record package are not upgraded.

OCDS 1.0 `describes <http://standard.open-contracting.org/1.0/en/schema/reference/#identifier>`__ an organization's ``name``, ``identifier``, ``address`` and ``contactPoint`` as relevant to identifying it. OCDS 1.1 `moves <http://standard.open-contracting.org/1.1/en/schema/reference/#parties>`__ organization data into a ``parties`` array. To upgrade from OCDS 1.0 to 1.1, we create an ``id`` for each organization, based on those identifying fields. This can result in duplicates in the ``parties`` array, if the same organization has different or missing values for identifying fields in different contexts. This can also lead to data loss if the same organization has different values for non-identifying fields in different contexts; the command prints warnings in such cases.

::

    cat tests/fixtures/realdata/release-package-1.json | ocdskit upgrade 1.0:1.1 > out.json

package-releases
~~~~~~~~~~~~~~~~

Reads releases from standard input, and prints one release package. You will need to edit the package metadata.

Optional positional arguments:

* ``extension`` add this extension to the package

::

    cat tests/fixtures/release_*.json | ocdskit package-releases > out.json

To convert record packages to a release package, you can use `use jq <https://github.com/open-contracting/ocdskit/blob/master/docs/Using_jq.md>`__ to get the releases from the record packages, along with the ``package-releases`` command. You will need to edit the package metadata.

::

    cat tests/fixtures/realdata/record-package* | jq -crM .records[].releases[] | ocdskit package-releases

combine-record-packages
~~~~~~~~~~~~~~~~~~~~~~~

Reads record packages from standard input, collects packages and records, and prints one record package.

Optional arguments:

* ``--uri URL`` set the record package's ``uri`` to this value
* ``--published-date PUBLISHED_DATE`` set the record package's ``publishedDate`` to this value

::

    cat tests/fixtures/record-package_*.json | ocdskit combine-record-packages > out.json

combine-release-packages
~~~~~~~~~~~~~~~~~~~~~~~~

Reads release packages from standard input, collects releases, and prints one release package.

Optional arguments:

* ``--uri URL`` set the release package's ``uri`` to this value
* ``--published-date PUBLISHED_DATE`` set the release package's ``publishedDate`` to this value

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

* ``--schema SCHEMA`` the URL or path of the schema to validate against
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

Reports details of a JSON Schema (open and closed codelists, definitions that can use a common $ref in the versioned release schema).

Optional arguments:

* ``--no-codelists`` skip reporting open and closed codelists
* ``--no-definitions`` skip reporting definitions that can use a common $ref in the versioned release schema
* ``--min-occurrences`` report definitions that occur at least this many times (default 5)

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

.. |PyPI Version| image:: https://img.shields.io/pypi/v/ocdskit.svg
   :target: https://pypi.org/project/ocdskit/
.. |Build Status| image:: https://secure.travis-ci.org/open-contracting/ocdskit.png
   :target: https://travis-ci.org/open-contracting/ocdskit
.. |Coverage Status| image:: https://coveralls.io/repos/github/open-contracting/ocdskit/badge.svg?branch=master
   :target: https://coveralls.io/github/open-contracting/ocdskit?branch=master
.. |Python Version| image:: https://img.shields.io/pypi/pyversions/ocdskit.svg
   :target: https://pypi.org/project/ocdskit/

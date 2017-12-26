# OCDS Kit

[![PyPI version](https://badge.fury.io/py/ocdskit.svg)](https://badge.fury.io/py/ocdskit)
[![Build Status](https://secure.travis-ci.org/open-contracting/ocdskit.png)](https://travis-ci.org/open-contracting/ocdskit)
[![Dependency Status](https://gemnasium.com/open-contracting/ocdskit.png)](https://gemnasium.com/open-contracting/ocdskit)
[![Coverage Status](https://coveralls.io/repos/open-contracting/ocdskit/badge.png)](https://coveralls.io/r/open-contracting/ocdskit)

A collection of commands for working with OCDS data.

    pip install ocdskit
    ocdskit --help

To install from source:

    pip install --upgrade .

`ocdskit` accepts JSON data from standard input. To report on a remote file:

    curl <url> | ocdskit <command>

To report on a local file:

    cat <path> | ocdskit <command>

To see all commands available, run:

    ocdskit --help

For exploring JSON data, consider using [jq](https://stedolan.github.io/jq/).

## Example 1

Download a list of release packages:

    curl http://www.contratosabiertos.cdmx.gob.mx/api/contratos/array > release_packages.json

Transform it to a stream of release packages, and validate each:

    jq -crM '.[]' release_packages.json | ocdskit validate --schema http://standard.open-contracting.org/schema/1__0__3/release-package-schema.json

Or, validate each with a local schema file:

    jq -crM '.[]' release_packages.json | ocdskit validate --schema file:///path/to/release-package-schema.json

Transform it to a stream of compiled releases:

    jq -crM '.[]' release_packages.json | ocdskit compile > compiled_releases.json

Find a compiled release with a given `ocid` (replace the `…`):

    jq 'select(.ocid == "OCDS-87SD3T-AD-SF-DRM-063-2015")' compiled_releases.json

Measure indicators across release packages:

    cat release_packages.json | ocdskit --encoding iso-8859-1 measure --currency MXN

## Example 2

Download a list of record packages:

    curl https://drive.google.com/uc?export=download&id=1HzVMdv9bryEw6pg80RwmJd3Le31SY1TI > record_packages.json

Combine it into a single record package:

    jq -crM '.[]' record_packages.json | ocdskit combine-record-packages > record_package.json

If the file is too large for the OCDS Validator, you can break it into parts. First, transform the list into a stream:

    jq -crM '.[]' record_packages.json > stream.json

Combine the first 10,000 items from the stream into a single record package:

    head -n 10000 stream.json | ocdskit combine-record-packages > record_package-1.json

Then, combine the next 10,000 items from the stream into a single record package:

    tail -n +10001 stream.json | head -n 10000 | ocdskit combine-record-packages > record_package-2.json

And so on:

    tail -n +20001 stream.json | head -n 10000 | ocdskit combine-record-packages > record_package-3.json

## Tabulate

    cat release_package.json | ocdskit tabulate sqlite:///data.db

For the format of `database_url`, see the [SQLAlchemy documentation](https://docs.sqlalchemy.org/en/rel_1_1/core/engines.html#database-urls).

Copyright (c) 2017 Open Contracting Partnership, released under the BSD license

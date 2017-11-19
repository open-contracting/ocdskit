# OCDS Kit

Scripts for automatically measuring specific indicators.

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

    jq -crM '.[]' record_packages.json | ocdskit combine-record-packages

Copyright (c) 2017 Open Contracting Partnership, released under the BSD license

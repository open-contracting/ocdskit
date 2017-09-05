# MEL Reporting Support

Scripts for automatically measuring specific indicators.

    pip install --upgrade .
    ocdsreport --help

`ocdsreport` accepts JSON data from standard input. To report on a remote file:

    curl <url> | ocdsreport <command>

To report on a local file:

    cat <path> | ocdsreport <command>

For exploring the JSON output of the `compile` command, consider using [jq](https://stedolan.github.io/jq/).

## Examples

Download a list of release packages:

    curl http://www.contratosabiertos.cdmx.gob.mx/api/contratos/array > release_packages.json

Validate it:

    cat release_packages.json | ocdsreport --encoding iso-8859-1 validate --schema http://standard.open-contracting.org/schema/1__0__3/release-package-schema.json

Transform it to a list of compiled releases:

    cat release_packages.json | ocdsreport --encoding iso-8859-1 compile > compiled_releases.json

Find a compiled release with a given `ocid` (replace the `…`):

    cat compiled_releases.json | jq '.[] | select(.ocid == "…")'

Measure indicators across release packages:

    cat release_packages.json | ocdsreport --encoding iso-8859-1 measure --currency MXN

Copyright (c) 2017 Open Contracting Partnership, released under the BSD license

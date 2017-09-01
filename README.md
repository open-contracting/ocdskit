# MEL Reporting Support

Scripts for automatically measuring specific indicators.

    pip install --upgrade .
    ocdsreport --help

`ocdsreport` accepts JSON data from standard input. To report on a remote file:

    curl <url> | ocdsreport <command>

To report on a local file:

    cat <path> | ocdsreport <command>

For exploring the JSON output of the `merge` command, consider using [jq](https://stedolan.github.io/jq/).

Copyright (c) 2017 Open Contracting Partnership, released under the BSD license

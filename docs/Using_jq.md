# Using jq

[jq](https://stedolan.github.io/jq/) has a very good tutorial and manual. We cover common operations here.

Get an array of release packages:

    curl http://www.contratosabiertos.cdmx.gob.mx/api/contratos/array > release_packages.json

Get the first release package:

    jq  '.[0]' release_packages.json

Before passing the data to an OCDS Kit command, make jq's output raw, compact and monochrome:

    jq --raw-output --compact-output --monochrome-output '.[0]' release_packages.json | ocdskit compile

Or, with short options:

    jq -rcM '.[0]' release_packages.json | ocdskit compile

Get the release packages, one line per package:

    jq -rcM '.[]' release_packages.json

Get the second 10 release packages, one line per package:

    jq -rcM '.[10:20][]' release_packages.json

You can stream release packages, one line per package, to the `compile` command:

    jq -rcM '.[]' release_packages.json | ocdskit compile

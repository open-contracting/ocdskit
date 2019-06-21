# Using jq

## Example 1

[jq](https://stedolan.github.io/jq/) has a very good tutorial and manual. We cover common operations here.

Get an array of release packages:

    curl http://www.contratosabiertos.cdmx.gob.mx/api/contratos/array > release_packages.json

Get the first release package:

    jq  '.[0]' release_packages.json

Before passing the data to an OCDS Kit command, make jq's output compact, raw and monochrome:

    jq --compact-output --raw-output --monochrome-output '.[0]' release_packages.json | ocdskit compile

Or, with short options:

    jq -crM '.[0]' release_packages.json | ocdskit compile

Get the release packages, one line per package:

    jq -crM '.[]' release_packages.json

Get the second 10 release packages, one line per package:

    jq -crM '.[10:20][]' release_packages.json

Or, using `head` and `tail`:

    jq -crM '.[]' release_packages.json | tail -n +10 | head -n 10

Get the first or last packages using `head` or `tail`:

    jq -crM '.[]' release_packages.json | head -n 15
    jq -crM '.[]' release_packages.json | tail -n 30

You can stream release packages, one line per package, to most OCDS Kit commands:

    jq -crM '.[]' release_packages.json | ocdskit compile

Or, you can split the stream of release packages into individual files named `xaaaa`, `xaaab`, `xaaac`, etc.:

    jq -crM '.[]' release_packages.json | split -l 1 -a 4

If the file is large, the above commands will consume GBs of memory. Instead, you can run:

    jq -cnM --stream 'fromstream(1|truncate_stream(inputs))' < release_packages.json | ocdskit compile

## Snippets

Get the compiled releases from a record package:

    jq -crM '.records[].compiledRelease' record_package.json

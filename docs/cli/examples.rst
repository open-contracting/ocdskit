Examples
========

OCDS Kit
--------

Example 1
~~~~~~~~~

Download a list of release packages::

    curl http://www.contratosabiertos.cdmx.gob.mx/api/contratos/array > release_packages.json

Transform it to a stream of release packages, and validate each::

    jq -crM '.[]' release_packages.json | ocdskit validate --schema https://standard.open-contracting.org/schema/1__0__3/release-package-schema.json

Or, validate each with a local schema file::

    jq -crM '.[]' release_packages.json | ocdskit validate --schema file:///path/to/release-package-schema.json

Transform it to a stream of compiled releases::

    jq -crM '.[]' release_packages.json | ocdskit compile > compiled_releases.json

Find a compiled release with a given ``ocid`` (replace the ``…``)::

    jq 'select(.ocid == "OCDS-87SD3T-AD-SF-DRM-063-2015")' compiled_releases.json

Example 2
~~~~~~~~~

Download a list of record packages::

    curl https://drive.google.com/uc?export=download&id=1HzVMdv9bryEw6pg80RwmJd3Le31SY1TI > record_packages.json

Combine it into a single record package::

    jq -crM '.[]' record_packages.json | ocdskit combine-record-packages > record_package.json

If the file is too large for the OCDS Validator, you can break it into parts. First, transform the list into a stream::

    jq -crM '.[]' record_packages.json > stream.json

Combine the first 10,000 items from the stream into a single record package::

    head -n 10000 stream.json | ocdskit combine-record-packages > record_package-1.json

Then, combine the next 10,000 items from the stream into a single record package::

    tail -n +10001 stream.json | head -n 10000 | ocdskit combine-record-packages > record_package-2.json

And so on::

    tail -n +20001 stream.json | head -n 10000 | ocdskit combine-record-packages > record_package-3.json

.. _jq:

jq
--

Example 1
~~~~~~~~~

`jq <https://stedolan.github.io/jq/>`__ has a very good tutorial and manual. We cover common operations here.

Get an array of release packages::

    curl http://www.contratosabiertos.cdmx.gob.mx/api/contratos/array > release_packages.json

Get the first release package::

    jq  '.[0]' release_packages.json

Before passing the data to an OCDS Kit command, make jq's output compact, raw and monochrome::

    jq --compact-output --raw-output --monochrome-output '.[0]' release_packages.json | ocdskit compile

Or, with short options::

    jq -crM '.[0]' release_packages.json | ocdskit compile

Get the release packages, one line per package::

    jq -crM '.[]' release_packages.json

Get the second 10 release packages, one line per package::

    jq -crM '.[10:20][]' release_packages.json

Or, using ``head`` and ``tail``::

    jq -crM '.[]' release_packages.json | tail -n +10 | head -n 10

Get the first or last packages using ``head`` or ``tail``::

    jq -crM '.[]' release_packages.json | head -n 15
    jq -crM '.[]' release_packages.json | tail -n 30

You can stream release packages, one line per package, to most OCDS Kit commands::

    jq -crM '.[]' release_packages.json | ocdskit compile

Or, you can split the stream of release packages into individual files named ``xaaaa``, ``xaaab``, ``xaaac``, etc.::

    jq -crM '.[]' release_packages.json | split -l 1 -a 4

If the file is large, the above commands will consume GBs of memory. Instead, you can run::

    jq -cnM --stream 'fromstream(1|truncate_stream(inputs))' < release_packages.json | ocdskit compile

Snippets
~~~~~~~~

Get the compiled releases from a record package::

    jq -crM '.records[].compiledRelease' record_package.json

.. _command-line:

Command line
------------

Pretty print::

    python -m json.tool filename.json

Read the first 1000 bytes of a file::

    head -c 1000 filename.json

Add newlines to ends of files (Fish shell)::

    for i in *.json; echo >> $i; end

On Windows, you may need to install `Cygwin <http://cygwin.com>`__ to use some command-line tools. PowerShell has `some corresponding tools <http://xahlee.info/powershell/PowerShell_for_unixer.html>`__.

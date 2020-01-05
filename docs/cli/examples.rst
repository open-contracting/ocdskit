Examples
========

OCDS Kit
--------

OCDS example 1
~~~~~~~~~~~~~~

Download a list of release packages::

    curl http://www.contratosabiertos.cdmx.gob.mx/api/contratos/array > release_packages.json

Transform it to a stream of release packages, and validate each::

    cat release_packages.json | ocdskit --encoding iso-8859-1 validate --schema https://standard.open-contracting.org/schema/1__0__3/release-package-schema.json

Or, validate each with a local schema file::

    cat release_packages.json | ocdskit --encoding iso-8859-1 validate --schema file:///path/to/release-package-schema.json

Transform it to a stream of compiled releases::

    cat release_packages.json | ocdskit --encoding iso-8859-1 compile > compiled_releases.json

Find a compiled release with a given ``ocid`` (replace the ``ocid`` value)::

    jq 'select(.ocid == "OCDS-87SD3T-AD-SF-DRM-063-2015")' compiled_releases.json

OCDS example 2
~~~~~~~~~~~~~~

Download a list of record packages::

    curl 'https://drive.google.com/uc?export=download&id=1HzVMdv9bryEw6pg80RwmJd3Le31SY1TI' > record_packages.json

Combine it into a single record package::

    cat record_packages.json | ocdskit combine-record-packages > record_package.json

If the file is too large for the OCDS Validator, you can break it into parts. First, transform the list into a stream::

    cat record_packages.json > stream.json

Combine the first 10,000 items from the stream into a single record package::

    head -n 10000 stream.json | ocdskit combine-record-packages > record_package-1.json

Then, combine the next 10,000 items from the stream into a single record package::

    tail -n +10001 stream.json | head -n 10000 | ocdskit combine-record-packages > record_package-2.json

And so on::

    tail -n +20001 stream.json | head -n 10000 | ocdskit combine-record-packages > record_package-3.json

.. _jq:

jq
--

jq example
~~~~~~~~~~

`jq <https://stedolan.github.io/jq/>`__ has a very good tutorial and manual. We cover common operations here.

Get an array of release packages::

    curl http://www.contratosabiertos.cdmx.gob.mx/api/contratos/array > release_packages.json

Get the first release package::

    jq '.[0]' release_packages.json

Get the release packages, one line per package::

    cat release_packages.json

Get the second 10 release packages, one line per package::

    jq --compact-output --raw-output --monochrome-output '.[10:20][]' release_packages.json

Or, with short options::

    jq -crM '.[10:20][]' release_packages.json

Or, using ``head`` and ``tail``::

    cat release_packages.json | tail -n +10 | head -n 10

Get the first or last packages using ``head`` or ``tail``::

    cat release_packages.json | head -n 15
    cat release_packages.json | tail -n 30

You can stream release packages, one line per package, to most OCDS Kit commands::

    cat release_packages.json | ocdskit compile

Or, you can split the stream of release packages into individual files named ``xaaaa``, ``xaaab``, ``xaaac``, etc.::

    cat release_packages.json | split -l 1 -a 4

jq snippets
~~~~~~~~~~~

Get the compiled releases from a record package, one line per release::

    jq -crM '.records[].compiledRelease' record_package.json

If the file is large, ``jq`` commands can consume GBs of memory. `See this StackOverflow answer <https://stackoverflow.com/questions/39232060/process-large-json-stream-with-jq/48786559#48786559>`__.

.. _command-line:

Command line
------------

Pretty print::

    python -m json.tool filename.json

Read the first 1000 bytes of a file::

    head -c 1000 filename.json

Add newlines to ends of files (Fish shell)::

    for i in *.json; echo >> $i; end

Read line 10,000 of a file::

    sed -n '10000 p' < filename.json

On Windows, you may need to install `Cygwin <http://cygwin.com>`__ to use some command-line tools. PowerShell has `some corresponding tools <http://xahlee.info/powershell/PowerShell_for_unixer.html>`__.

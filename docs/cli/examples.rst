Examples
========

OCDS Kit
--------

Download a list of release packages:

.. code-block:: bash

    curl http://www.contratosabiertos.cdmx.gob.mx/api/contratos/array > release_packages.json

Transform it to a stream of compiled releases:

.. code-block:: bash

    cat release_packages.json | ocdskit --encoding iso-8859-1 compile > compiled_releases.json

.. _command-line:

Command line
------------

On Windows, you may need to install `Cygwin <http://cygwin.com>`__ to use some command-line tools. PowerShell has `some corresponding tools <http://xahlee.info/powershell/PowerShell_for_unixer.html>`__.

Pretty print a JSON file:

.. code-block:: bash

    python -m json.tool filename.json

Pretty print a JSON Lines file:

.. code-block:: bash

    python -m json.tool --json-lines filename.json

Read the first 1000 bytes of a file:

.. code-block:: bash

    head -c 1000 filename.json

Read line 10,000 of a file:

.. code-block:: bash

    sed -n '10000 p' < filename.json

Read the first 10 lines of a file:

.. code-block:: bash

    cat filename.json | head -n 10

Read the last 10 lines of a file:

.. code-block:: bash

    cat filename.json | tail -n 10

Get lines 21-30 of a file:

.. code-block:: bash

    cat filename.json | tail -n +20 | head -n 10

Split each line of a file into new files named ``xaaaa``, ``xaaab``, ``xaaac``, etc.:

.. code-block:: bash

    cat filename.json | split -l 1 -a 4

Add newlines to ends of files (fish shell):

.. code-block:: fish

    for i in *.json; echo >> $i; end

.. _jq:

jq
--

`jq <https://stedolan.github.io/jq/>`__ has a very good tutorial and manual.

Find a compiled release with a given ``ocid`` (replace the ``ocid`` value):

.. code-block:: bash

    jq 'select(.ocid == "OCDS-87SD3T-AD-SF-DRM-063-2015")' releases.json

If the file is large, ``jq`` commands can consume GBs of memory. `See this StackOverflow answer <https://stackoverflow.com/questions/39232060/process-large-json-stream-with-jq/48786559#48786559>`__.

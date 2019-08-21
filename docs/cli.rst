Command-line interface
======================

To see all commands available, run::

    ocdskit --help

.. note:

   Users on Windows should run ``set PYTHONIOENCODING=utf-8`` in the terminal before running any ``ocdskit`` commands.

Most ``ocdskit`` tools accept only `line-delimited JSON <https://en.wikipedia.org/wiki/JSON_streaming>`__ data from standard input. To process a remote file::

    curl <url> | ocdskit <command>

To process a local file::

    cat <path> | ocdskit <command>

If the JSON data is not line-delimited, you can make it line-delimited using `jq <https://stedolan.github.io/jq/>`__::

    curl <url> | jq -crM . | ocdskit <command>

For exploring JSON data, consider using ``jq``. See our tips on using :ref:`jq <jq>` and the :ref:`command-line <command-line>`.

.. toctree::
   :caption: Commands
   :maxdepth: 2

   cli/ocds
   cli/schema
   cli/generic
   cli/examples

Command-Line Interface
======================

To see all commands available, run::

    ocdskit --help

Users on Windows should run ``set PYTHONIOENCODING=utf-8`` in the terminal before running any ``ocdskit`` commands.

To process a remote file::

    curl <url> | ocdskit <command>

To process a local file::

    cat <path> | ocdskit <command>

For exploring JSON data, consider using ``jq``. See our tips on using :ref:`jq <jq>` and the :ref:`command-line <command-line>`.

.. toctree::
   :caption: Commands
   :maxdepth: 2

   cli/ocds
   cli/schema
   cli/generic
   cli/examples

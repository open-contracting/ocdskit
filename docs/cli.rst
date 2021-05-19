Command-Line Interface
======================

To see all commands available, run:

.. code-block:: bash

    ocdskit --help

Users on Windows should run ``set PYTHONIOENCODING=utf-8`` and ``set PYTHONUTF8=1`` in each terminal session before running any ``ocdskit`` commands. To set these environment variables for all future sessions, run ``setx PYTHONIOENCODING utf-8`` and ``setx PYTHONUTF8 1``.

To process a remote file:

.. code-block:: bash

    curl <url> | ocdskit <command>

To process a local file:

.. code-block:: bash

    cat <path> | ocdskit <command>

For exploring JSON data, consider using ``jq``. See our tips on using :ref:`jq <jq>` and the :ref:`command-line <command-line>`.

.. toctree::
   :caption: Commands
   :maxdepth: 2

   cli/ocds
   cli/schema
   cli/generic
   cli/examples

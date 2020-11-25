OC4IDS Commands
===============

Optional arguments for all commands are:

* ``--encoding ENCODING`` the file encoding
* ``--ascii`` print escape sequences instead of UTF-8 characters
* ``--pretty`` pretty print output
* ``--root-path ROOT_PATH`` the path to the items to process within each input

The inputs can be `concatenated JSON <https://en.wikipedia.org/wiki/JSON_streaming#Concatenated_JSON>`__ or JSON arrays.

Handling edge cases
-------------------

See the guidance for :ref:`handling-edge-cases` in OCDS. You can use the same approaches with OC4IDS data.

.. _split-project-packages:

split-project-packages
----------------------

Reads project packages from standard input, and prints smaller project packages for each.

Mandatory positional arguments:

* ``size`` the number of projects per package

.. code-block:: bash

    cat tests/fixtures/oc4ids/project_package.json | ocdskit split-project-packages 1 | split -l 1 -a 4

The ``split`` command will write files named ``xaaaa``, ``xaaab``, ``xaaac``, etc. Don't combine the OCDS Kit ``--pretty`` option with the ``split`` command.

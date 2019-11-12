Contributing
============

Adding a command
----------------

#. Create a file matching the command's name in ``ocdskit/cli/commands``, replacing hyphens with underscores.
#. Add the command's module to ``COMMAND_MODULES`` in ``ocdskit/__main__.py``, in alphabetical order.
#. Fill in the command's file (see ``ocdskit/cli/commands/compile.py`` for a brief file).
#. Add documentation for the command and any new library methods.
#. Add tests for the command.
#. Update the changelog.

Streaming versus buffering
--------------------------

Commands handle inputs in two ways: some commands, like ``package-releases``, buffer all inputs into memory before writing any outputs; other commands read inputs and write outputs progressively or one-at-a-time ("streaming"). Streaming writes outputs faster and requires less memory than buffering. For performance reasons, commands should stream, whenever possible.

These OCDS commands buffer, because they output one JSON file:

* ``combine-record-packages``
* ``combine-release-packages``
* ``package-records``
* ``package-releases``

Python's standard ``json`` library requires an entire file's contents to be in memory before writing. If there is demand to stream output from these commands, we can instead use a custom writer to write iteratively.

These OCDS commands buffer (for now):

* ``compile`` (see `#83 <https://github.com/open-contracting/ocdskit/issues/83>`__)

These OCDS commands stream, using a read buffer of 64 kB:

* ``detect-format``
* ``upgrade``
* ``split-record-packages``
* ``split-release-packages``
* ``validate``

The ``tabulate`` command hasn't yet been reviewed.

To test whether commands stream, you can run, for example::

    echo 'cat tests/fixtures/realdata/record-package_versioned.json tests/fixtures/realdata/record-package_versioned.json; sleep 3; cat tests/fixtures/record-package_minimal.json' > input.sh
    sh input.sh | ocdskit upgrade 1.0:1.1
    sh input.sh | ocdskit split-record-packages 1

::

    echo 'cat tests/fixtures/realdata/release-package-1-2.json tests/fixtures/realdata/release-package-1-2.json; sleep 7; cat tests/fixtures/release-package_minimal.json' > input.sh
    sh input.sh | ocdskit split-release-packages 1
    sh input.sh | ocdskit validate

You can run ``sh input.sh | tee`` to compare the timing of ``tee`` to the timings above.

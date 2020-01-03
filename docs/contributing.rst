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

Streaming
---------

A naive program buffers all inputs into memory before writing any outputs. Since OCDS files can be very large, all OCDS commands read inputs and write outputs progressively or one-at-a-time (that is, they "stream"), as much as possible. Streaming writes outputs faster and requires less memory than buffering.

All OCDS commands stream input, using ``ijson`` to iteratively parse the JSON inputs with a read buffer of 64 kB, and stream output, using `json.JSONDecoder.iterencode() <https://docs.python.org/3/library/json.html#json.JSONEncoder.iterencode>`___ with a `default <https://docs.python.org/3/library/json.html#json.JSONEncoder.default>`__ function that postpones the evaluation of iterators. OCDS commands otherwise avoid buffering by using iterators instead of lists (for example, ``package-releases`` sets the package's ``releases`` to an iterator), using the `itertools <https://docs.python.org/2/library/itertools.html>`__ module.

The streaming behavior of each command is:

-  ``detect-format``: streams, by discarding input as it's read
-  ``compile`` reads all inputs before writing any outputs, to be sure it has all releases for each OCID. Instead of buffering all inputs into memory, however, it buffers into SQLite (if available), which writes to a temporary file as needed.
-  ``upgrade``: reads each input into memory, and processes one at a time
-  ``package-records``: streams, by holding the inputs in an iterator
-  ``package-releases``: streams, by holding the inputs in an iterator
-  ``combine-record-packages``:  buffers all inputs into memory (see details in code)
-  ``combine-release-packages``:  buffers all inputs into memory (see details in code)
-  ``split-record-packages``: reads each input into memory, and processes one at a time
-  ``split-release-packages``: reads each input into memory, and processes one at a time
-  ``validate``: reads each input into memory, and processes one at a time
-  ``tabulate``: not yet reviewed

For ``upgrade`` and ``validate``, if a single package is very large, a workaround is to use ``split-record-packages`` or ``split-release-packages`` to make it smaller. For ``upgrade``, specifically, if a release package is very large, a workaround is to upgrade its individual releases using ``--root-path releases.item``.

You can append these lines to ``BaseCommand.print()`` to see if memory usage increases with input size:

.. code:: python

   import resource
   sys.stderr.write(str(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 / 1024))

And run, for example::

    python -c 'print("\n".join(map(str, range(5000000))))' | ocdskit package-records > /dev/null
    python -c 'print("\n".join(map(str, range(5000000))))' | ocdskit package-releases > /dev/null

To test whether commands stream input, you can run, for example::

    echo 'cat tests/fixtures/realdata/record-package_versioned.json tests/fixtures/realdata/record-package_versioned.json; sleep 3; cat tests/fixtures/record-package_minimal.json' > input.sh
    sh input.sh | ocdskit upgrade 1.0:1.1
    sh input.sh | ocdskit split-record-packages 1

.. code:: bash

    echo 'cat tests/fixtures/realdata/release-package-1-2.json tests/fixtures/realdata/release-package-1-2.json; sleep 7; cat tests/fixtures/release-package_minimal.json' > input.sh
    sh input.sh | ocdskit split-release-packages 1
    sh input.sh | ocdskit validate

You can run ``sh input.sh | tee`` to compare the timing of ``tee`` to the timings above.

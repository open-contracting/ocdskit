Contributing
============

Adding a command
----------------

#. Create a file matching the command's name in ``ocdskit/commands``, replacing hyphens with underscores.
#. Add the command's module to ``COMMAND_MODULES`` in ``ocdskit/__main__.py``, in alphabetical order.
#. Fill in the command's file (see ``ocdskit/commands/package_records.py`` for a brief file).
#. Add documentation for the command and any new library methods.
#. Add tests for the command.
#. Update the changelog.

Streaming
---------

All OCDS commands:

-  stream input, using `ijson <https://pypi.org/project/ijson/>`__ to iteratively parse the JSON inputs with a read buffer of 64 kB
-  stream output, using `json.JSONDecoder.iterencode() <https://docs.python.org/3/library/json.html#json.JSONEncoder.iterencode>`__ with a `default <https://docs.python.org/3/library/json.html#json.JSONEncoder.default>`__ method that postpones the evaluation of iterators
-  postpone the evaluation of inputs by using iterators instead of lists (for example, ``package-releases`` sets the package's ``releases`` to an iterator), using the `itertools <https://docs.python.org/2/library/itertools.html>`__ module

The streaming behavior of each command is:

-  ``detect-format``: streams, by discarding input as it's read
-  ``compile`` reads all inputs before writing any outputs, to be sure it has all releases for each OCID. Instead of buffering all inputs into memory, however, it reads each input into SQLite (if available), which writes to a temporary file as needed.
-  ``upgrade``: reads each input into memory, and processes one at a time
-  ``package-records``: streams, by using an iterator to postpone the evaluation of inputs
-  ``package-releases``: streams, by using an iterator to postpone the evaluation of inputs
-  ``combine-record-packages``:  buffers all inputs into memory (`see issue <https://github.com/open-contracting/ocdskit/issues/119>`__)
-  ``combine-release-packages``:  buffers all inputs into memory (`see issue <https://github.com/open-contracting/ocdskit/issues/119>`__)
-  ``split-record-packages``: reads each input into memory, and processes one at a time
-  ``split-release-packages``: reads each input into memory, and processes one at a time
-  ``echo``: streams, by using an iterator to postpone the evaluation of inputs

You can append these lines to the end of a ``handle()`` method to see if memory usage increases with input size:

.. code-block:: python

   import resource, sys
   print(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 / 1024, file=sys.stderr)

And run, for example:

.. code-block:: bash

    python -c 'import json; print("\n".join(json.dumps({"releases": [{"ocid": str(y), "date": ""} for x in range(100)]}) for y in range(10000)))' | ocdskit compile --package > /dev/null
    python -c 'print("\n".join(map(str, range(5000000))))' | ocdskit package-records > /dev/null
    python -c 'print("\n".join(map(str, range(5000000))))' | ocdskit package-releases > /dev/null
    python -c 'import json; print("\n".join(json.dumps({"records": list(range(500))}) for x in range(10000)))' | ocdskit echo --root-path records.item | ocdskit package-records --size 999 > /dev/null
    python -c 'import json; print("\n".join(json.dumps({"releases": list(range(500))}) for x in range(10000)))' | ocdskit echo --root-path releases.item | ocdskit package-releases --size 999 > /dev/null

To test whether commands stream input, you can run, for example:

.. code-block:: bash

    echo 'cat tests/fixtures/realdata/record-package_versioned.json tests/fixtures/realdata/record-package_versioned.json; sleep 3; cat tests/fixtures/record-package_minimal.json' > input.sh
    sh input.sh | ocdskit upgrade 1.0:1.1
    sh input.sh | ocdskit split-record-packages 1

.. code-block:: bash

    echo 'cat tests/fixtures/realdata/release-package-1-2.json tests/fixtures/realdata/release-package-1-2.json; sleep 7; cat tests/fixtures/release-package_minimal.json' > input.sh
    sh input.sh | ocdskit split-release-packages 1

You can run ``sh input.sh | tee`` to compare the timing of ``tee`` to the timings above.

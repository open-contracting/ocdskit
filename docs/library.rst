API Reference
=============

.. toctree::
   :maxdepth: 2

   api/combine
   api/upgrade
   api/mapping_sheet
   api/packager
   api/schema
   api/util
   api/cli
   api/exceptions

Working with streams
--------------------

A naive program buffers all inputs into memory before writing any outputs. OCDS files can be very large, and loading them into memory can exhaust all available memory. The :doc:`command-line interface<cli>` therefore reads inputs and writes outputs progressively or one-at-a-time (that is, it "streams"), as much as possible. Streaming writes outputs faster and requires less memory than buffering.

Output
~~~~~~

Several library methods return dictionaries with generators as values, which can't be serialized using the ``json`` module without extra work. Use the :func:`ocdskit.util.json_dumps`, :func:`ocdskit.util.json_dump` and :func:`ocdskit.util.iterencode` methods instead.

Input
~~~~~

The command-line interface uses `ijson <https://pypi.org/project/ijson/>`__ to iteratively parse the JSON inputs with a read buffer of 64 kB.

To start, this uses the same amount of memory as ``json.load(f)``:

.. code-block:: python

   import ijson

   with open(filename) as f:
       for item in ijson.items(f, ''):
           # do stuff

If you are working with release packages or record packages and only need the releases or records, set the ``prefix`` argument (:code:`''` above) as described in `ijson's documentation <https://github.com/ICRAR/ijson#prefix>`__. Instead of loading the entire package into memory, this instead loads each release or record one-at-a-time. For example:

.. code-block:: python

   for item in ijson.items(f, 'releases.item'):

.. code-block:: python

   for item in ijson.items(f, 'records.item'):

The ``prefix`` argument is also relevant if you are working with files that :ref:`embed OCDS data<embedded-data>`. For example:

.. code-block:: python

   for item in ijson.items(f, 'results.item'):

If you are parsing `concatenated JSON <https://en.wikipedia.org/wiki/JSON_streaming#Concatenated_JSON>`__, add :code:`multiple_values=True`. For example:

.. code-block:: python

   for item in ijson.items(f, '', multiple_values=True):

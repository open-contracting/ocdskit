Python library
==============

Working with streams
--------------------

A naive program buffers all inputs into memory before writing any outputs. Since OCDS files can be very large, the :doc:`command-line interface<cli>` reads inputs and writes outputs progressively or one-at-a-time (that is, it "streams"), as much as possible. Streaming writes outputs faster and requires less memory than buffering.

Output
~~~~~~

Several library methods return dictionaries with generators as values, which can't be serialized using the ``json`` module without extra work. Use the :func:`ocdskit.util.json_dumps`, :func:`ocdskit.util.json_dump` and :func:`ocdskit.util.iterencode` methods instead.

Input
~~~~~

The command-line interface uses `ijson <https://pypi.org/project/ijson/>`__ to iteratively parse the JSON inputs with a read buffer of 64 kB. To do the same in your code:

.. code-block:: python

   import ijson

   with open(filename) as f:
       for item in ijson.items(f, ''):
           # do stuff

If you are parsing `concatenated JSON <https://en.wikipedia.org/wiki/JSON_streaming#Concatenated_JSON>`__, use :code:`multiple_values=True`:

.. code-block:: python

   for item in ijson.items(f, '', multiple_values=True):

If you are working with files that :ref:`embed OCDS data<embedded-data>`, set the ``prefix`` argument (:code:`''` above) as described in `ijson's documentation <https://github.com/ICRAR/ijson#prefix>`__. For example:

.. code-block:: python

   for item in ijson.items(f, 'results.item'):

Modules
-------

.. toctree::
   :maxdepth: 2

   api/combine
   api/upgrade
   api/oc4ids
   api/mapping_sheet
   api/schema
   api/util
   api/cli
   api/exceptions

Python library
==============

Several library methods return dictionaries with generators as values, which can't be serialized using the ``json`` module without extra work. Use the :func:`ocdskit.util.json_dumps`, :func:`ocdskit.util.json_dump` and :func:`ocdskit.util.iterencode` methods instead.

.. toctree::
   :maxdepth: 2

   api/combine
   api/upgrade
   api/mapping_sheet
   api/schema
   api/util
   api/exceptions

OCDS Kit |release|
==================

.. include:: ../README.rst

Check out the `tutorial <https://www.open-contracting.org/resources/ocds-kit-tutorial/>`__ for an interactive guide to installing and using OCDS Kit.

To install:

.. code-block:: bash

    pip install ocdskit

To improve performance, install as ``pip install ocdskit[perf]``, unless you are using `PyPy <https://www.pypy.org>`__.

OCDS Kit requires a `supported version <https://endoflife.date/python>`__ of Python 3. Users with Python 2 as their default Python interpreter must either run ``pip3 install ocdskit``, set up a Python 3 virtual environment, or `use OCDS Kit within a Docker container <https://hub.docker.com/r/ricardoe/ocdskit/>`__.

OCDS Kit can be used either via its :doc:`command-line interface <cli>` or as a :doc:`Python library <library>`.

.. toctree::
   :maxdepth: 2
   :caption: Contents

   cli
   library
   contributing
   changelog

Copyright (c) 2017 Open Contracting Partnership, released under the BSD license

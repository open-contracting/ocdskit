OCDS Kit |release|
==================

.. include:: ../README.rst

To install::

    pip install ocdskit

To significantly improve performance, install the `YAJL <http://lloyd.github.io/yajl/>`__ system library (for example, on macOS, run ``brew install yajl``) and the `orjson <https://github.com/ijl/orjson#readme>`__ Python package (``pip install orjson``).

OCDS Kit requires Python 3.6 or greater. Users with Python 2 as their default Python interpreter must either run ``pip3 install ocdskit``, set up a Python 3 virtual environment, or `use OCDS Kit within a Docker container <https://hub.docker.com/r/ricardoe/ocdskit/>`__.

OCDS Kit can be used either via its :doc:`cli` or as a :doc:`library`.

.. toctree::
   :maxdepth: 2
   :caption: Contents

   cli
   library
   contributing
   changelog

Copyright (c) 2017 Open Contracting Partnership, released under the BSD license

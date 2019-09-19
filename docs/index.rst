OCDS Kit |release|
==================

.. include:: ../README.rst

To install::

    pip install ocdskit

Until `ijson 2.5 <https://pypi.org/project/ijson/>`__ is available, you must also:

::

    pip install -e git+https://github.com/ICRAR/ijson.git#egg=ijson

To significantly improve performance, install `YAJL <http://lloyd.github.io/yajl/>`__. For example, on macOS, run ``brew install yajl``.

Users with Python 2 as their default Python interpreter must either run ``pip3 install ocdskit``, set up a Python 3 virtual environment, or `use OCDS Kit within a Docker container <https://hub.docker.com/r/ricardoe/ocdskit/>`__.

OCDS Kit can be used either via its :doc:`cli` or as a :doc:`library`.

.. toctree::
   :maxdepth: 2
   :caption: Contents

   cli
   library
   contributing
   changelog

Copyright (c) 2017 Open Contracting Partnership, released under the BSD license

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

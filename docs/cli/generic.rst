Generic Commands
================

The following commands may be used when working with JSON data, in general.

indent
------

Indents JSON files by modifying the given files in-place.

Optional arguments:

* ``-r``, ``--recursive`` recursively indent JSON files
* ``--indent INDENT`` indent level

::

    ocdskit indent --recursive file1 path/to/directory file2

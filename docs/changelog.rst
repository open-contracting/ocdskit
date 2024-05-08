Changelog
=========

1.1.13 (2024-05-08)
-------------------

Added
~~~~~

-  :meth:`ocdskit.combine.merge` accepts a ``convert_exceptions_to_warnings`` argument.

1.1.12 (2024-05-07)
-------------------

Added
~~~~~

-  :meth:`ocdskit.combine.merge` accepts a ``force_version`` argument.

1.1.11 (2024-05-01)
-------------------

Added
~~~~~

-  :meth:`ocdskit.combine.merge` accepts a ``ignore_version`` argument.

1.1.10 (2024-04-15)
-------------------

Added
~~~~~

-  :class:`ocdskit.util.Format` enumeration

Changed
~~~~~~~

-  :meth:`ocdskit.util.detect_format`: Detect empty packages that set metadata fields but not a ``releases`` or ``records`` field.

1.1.9 (2024-01-05)
------------------

Added
~~~~~

-  :meth:`ocdskit.util.is_linked_release` accepts a ``maximum_properties`` argument (default 3).

1.1.8 (2023-06-26)
------------------

Changed
~~~~~~~

-  :ref:`schema-strict`: Add ``minItems`` last, to match existing schema.

1.1.7 (2023-06-13)
------------------

Changed
~~~~~~~

-  :ref:`compile`: Prefix the ``ocid`` to a warning.

1.1.6 (2023-06-08)
------------------

Changed
~~~~~~~

-  :ref:`compile`: Skip ``null`` entries in the ``releases`` array of a release package.

1.1.5 (2023-04-20)
------------------

Changed
~~~~~~~

Update documentation on PyPI.

1.1.4 (2023-02-07)
------------------

Added
~~~~~

New CLI options:

-  :ref:`mapping-sheet`: ``--no-inherit-extension``

Changed
~~~~~~~

-  Drop support for Python 3.6 (end-of-life 2021-12-23).

Fixed
~~~~~

-  :meth:`ocdskit.mapping_sheet.mapping_sheet` works if a schema contains ``"deprecated": null``.
-  :meth:`ocdskit.mapping_sheet.mapping_sheet` works if ``--extension-field`` is set to a value other than "extension".

1.1.3 (2022-10-20)
------------------

Fixed
~~~~~

-  :meth:`ocdskit.mapping_sheet.mapping_sheet` works if ``include_definitions=False`` but ``base_uri`` is not provided.

1.1.2 (2022-10-06)
------------------

Changed
~~~~~~~

-  Move ``ocdskit/cli/__main__.py`` to ``ocdskit/__main__.py``, to support the ``python -m ocdskit`` interface.
-  Move ``ocdskit.cli.commands`` to :mod:`ocdskit.commands`.

1.1.1 (2022-08-17)
------------------

Changed
~~~~~~~

-  :meth:`ocdskit.mapping_sheet.mapping_sheet` resolves ``$ref`` properties if ``include_definitions=False``.

1.1.0 (2022-08-16)
------------------

Changed
~~~~~~~

-  :meth:`ocdskit.mapping_sheet.mapping_sheet` returns columns and rows instead of writing to a file-like object.

1.0.4 (2022-02-10)
------------------

Added
~~~~~

New CLI options:

-  :ref:`mapping-sheet`: ``--codelist``

1.0.3 (2021-12-18)
------------------

Added
~~~~~

-  :meth:`ocdskit.util.get_ocds_patch_tag`

Changed
~~~~~~~

-  :ref:`compile` omits ``packages`` from a record package for OCDS 1.2+.

Fixed
~~~~~

-  :ref:`compile` omits ``packages`` from a record package if empty.
-  :ref:`compile` raises an error if the OCDS version is not recognized, instead of failing silently.

1.0.2 (2021-06-29)
------------------

Fixed
~~~~~

-  :ref:`mapping-sheet` correctly populates the ``extension`` column for extension fields on OCDS objects with ``items`` properties that ``$ref``'erence OCDS definitions.

1.0.1 (2021-06-16)
------------------

Changed
~~~~~~~

-  :meth:`ocdskit.util.detect_format` accepts a ``reader`` keyword argument: for example, ``gzip.open`` instead of ``open``.

1.0.0 (2021-05-19)
------------------

Changed
~~~~~~~

-  ``validate``: Remove command. Instead, use `lib-cove-ocds <https://github.com/open-contracting/lib-cove-ocds>`__.
-  ``tabulate``: Remove command. Instead, convert the JSON data to CSV format using `Spoonbill <https://github.com/open-contracting/spoonbill>`__ or `Flatten Tool <https://flatten-tool.readthedocs.io/en/latest/usage-ocds/>`__, and then load the CSV files into your preferred database. See:

   -  SQLite's `.import <https://sqlite.org/cli.html#importing_csv_files>`__ command (see also `sqlite-utils <https://sqlite-utils.datasette.io/en/stable/>`__)
   -  PostgreSQL's `COPY <https://www.postgresql.org/docs/current/sql-copy.html>`__ command
   -  MySQL's `LOAD DATA <https://dev.mysql.com/doc/refman/8.0/en/load-data.html>`__ command
   -  csvkit's `csvsql <https://csvkit.readthedocs.io/en/latest/scripts/csvsql.html>`__ command

-  ``convert-to-oc4ids``: Remove command. Instead, use oc4idskit's `convert-from-ocds <https://oc4idskit.readthedocs.io/en/latest/cli.html>`__.
-  ``ocdskit.oc4ids``: Remove module. Instead, use oc4idskit's `transforms <https://oc4idskit.readthedocs.io/en/latest/library.html>`__.

0.2.23 (2021-05-06)
-------------------

Fixed
~~~~~

-  :ref:`mapping-sheet`: Set ``deprecated`` on the extra rows for arrays.

0.2.22 (2021-04-23)
-------------------

Fixed
~~~~~

-  :ref:`schema-strict`: Don't add ``"uniqueItems": true`` to coordinates fields.

0.2.21 (2021-04-10)
-------------------

Added
~~~~~

-  Add Python wheels distribution.

0.2.20 (2021-02-19)
-------------------

Added
~~~~~

New CLI options:

-  :ref:`mapping-sheet`: ``--language``

0.2.19 (2021-02-16)
-------------------

Fixed
~~~~~

-  :ref:`upgrade`: If a party's ``roles`` field isn't set, no error occurs.
-  :ref:`upgrade`: If an organization reference has fewer fields than an organization, no warning is issued.

0.2.18 (2020-12-15)
-------------------

Added
~~~~~

New library method:

-  :meth:`ocdskit.util.detect_format`

0.2.17 (2020-12-11)
-------------------

Changed
~~~~~~~

-  ``tabulate``: Supports linked releases and compiled releases.

0.2.16 (2020-10-06)
-------------------

Fixed
~~~~~

-  :ref:`upgrade`: If a party's ``roles`` field isn't a list of strings, no error occurs.

Added
~~~~~

New CLI commands:

-  ``split-project-packages``

0.2.15 (2020-09-30)
-------------------

Changed
~~~~~~~

-  :ref:`upgrade`: If a party's ``roles`` field is a string, it is coerced to an array.

Added
~~~~~

New CLI options:

-  :ref:`mapping-sheet`: ``--no-deprecated``, ``--no-replace-refs``

0.2.14 (2020-09-16)
-------------------

Added
~~~~~

New CLI option:

-  :ref:`schema-strict`: ``--check``

New library method:

-  :meth:`ocdskit.schema.add_validation_properties`

0.2.13 (2020-09-16)
-------------------

Fixed
~~~~~

-  ``convert-to-oc4ids`` no longer errors if a party's ``id`` field isn't set.

0.2.12 (2020-08-19)
-------------------

Changed
~~~~~~~

-  :meth:`ocdskit.util.get_ocds_minor_version` now supports records.

Fixed
~~~~~

-  :ref:`mapping-sheet` correctly populates the ``extension`` column for extension fields on OCDS objects that ``$ref``'erence OCDS definitions.

0.2.11 (2020-08-12)
-------------------

Changed
~~~~~~~

-  :ref:`mapping-sheet`: The ``extension`` column is now the name of the extension that introduced the JSON path, not the name of the extension that defined the field.

0.2.10 (2020-07-28)
-------------------

Changed
~~~~~~~

-  :ref:`indent` respects ``--ascii``.
-  ``tabulate`` supports any OCDS data.

Fixed
~~~~~

-  :ref:`compile` no longer errors on Windows when using the SQLite backend.

0.2.9 (2020-07-08)
------------------

Fixed
~~~~~

-  :ref:`detect-format` respects ``--root-path``.
-  ``convert-to-oc4ids`` omits ``sector`` and ``documents`` if empty.

0.2.8 (2020-04-29)
------------------

Changed
~~~~~~~

-  :ref:`schema-strict` accepts a filename as a positional argument, instead of a schema as standard input.
-  :ref:`schema-strict` adds constraints to all fields, not only required fields.

0.2.7 (2020-04-23)
------------------

Added
~~~~~

New CLI options:

-  :ref:`combine-record-packages`: ``--version``
-  :ref:`combine-release-packages`: ``--version``
-  :ref:`compile`: ``--version``
-  ``convert-to-oc4ids``: ``--version``
-  :ref:`package-records`: ``--version``
-  :ref:`package-releases`: ``--version``

New library method:

-  :meth:`ocdskit.util.is_compiled_release`

Changed
~~~~~~~

-  :ref:`compile` sets ``"version": "1.1"`` even on OCDS 1.0 data (see :meth:`ocdskit.combine.merge`).
-  :ref:`package-records` and :ref:`package-releases` omit the ``extensions`` field if empty (see :meth:`ocdskit.combine.package_records`, :meth:`ocdskit.combine.package_releases`).

Fixed
~~~~~

-  ``convert-to-oc4ids`` sets the ``publishedDate`` field, not the ``published_date`` field.

0.2.6 (2020-04-15)
------------------

Added
~~~~~

New library method:

-  :meth:`ocdskit.util.is_linked_release`

Changed
~~~~~~~

-  :ref:`combine-record-packages` and :ref:`combine-release-packages` warn if the ``"records"`` and ``"releases"`` fields aren't set (see :meth:`ocdskit.combine.combine_record_packages`, :meth:`ocdskit.combine.combine_release_packages`).

0.2.5 (2020-04-14)
------------------

Fixed
~~~~~

-  :ref:`combine-record-packages` and :ref:`combine-release-packages` no longer error if the ``"records"`` and ``"releases"`` fields aren't set (see :meth:`ocdskit.combine.combine_record_packages`, :meth:`ocdskit.combine.combine_release_packages`).

0.2.4 (2020-03-19)
------------------

Fixed
~~~~~

-  ``convert-to-oc4ids`` no longer errors.

0.2.3 (2020-03-19)
------------------

Added
~~~~~

New CLI commands:

-  ``convert-to-oc4ids``

New library module:

-  ``ocdskit.oc4ids``

Changed
~~~~~~~

-  :ref:`compile` errors if an ``ocid`` field is missing from a release (see :meth:`ocdskit.packager.AbstractBackend.add_release`).
-  :ref:`upgrade` upgrades records (see :meth:`ocdskit.upgrade.upgrade_10_11`).

0.2.2 (2020-01-07)
------------------

Changed
~~~~~~~

-  Avoid exception when piping output to tools like ``head``.
-  :ref:`package-records`, :ref:`package-releases`: Use fast writer if ``--size`` is set.
-  :ref:`echo`: Use fast writer (assuming ``--root-path`` is set anytime input is too large).

0.2.1 (2020-01-06)
------------------

Added
~~~~~

New CLI options:

-  :ref:`package-records`: ``--size``
-  :ref:`package-releases`: ``--size``

New CLI commands:

-  :ref:`echo`

Changed
~~~~~~~

-  Implement iterative JSON writer.
-  Use ``orjson`` if available to improve performance of dumping/loading JSON, especially to/from SQL in :ref:`compile` command (see :mod:`ocdskit.packager`).

Fixed
~~~~~

-  :ref:`combine-record-packages` no longer duplicates release package URLs in ``packages`` field (see :meth:`ocdskit.combine.combine_record_packages`).

0.2.0 (2019-12-31)
------------------

Added
~~~~~

New library module:

-  :mod:`ocdskit.packager`

Changed
~~~~~~~

CLI:

-  :ref:`compile` accepts either release packages or individual releases (see :meth:`ocdskit.combine.merge`).
-  :ref:`compile` is memory efficient if given a long list of inputs (see :meth:`ocdskit.combine.merge`).

Library:

-  Deprecate ``ocdskit.combine.compile_release_packages`` in favor of :meth:`ocdskit.combine.merge`.

Fixed
~~~~~

-  ``--linked-releases`` no longer uses the same linked releases for all records (see :meth:`ocdskit.packager.Packager.output_records`).

0.1.5 (2019-12-18)
------------------

Added
~~~~~

New library methods:

-  :meth:`ocdskit.util.is_record`
-  :meth:`ocdskit.util.is_release`

The internal methods ``ocdskit.util.json_load`` and ``ocdskit.util.json_loads`` are removed.

0.1.4 (2019-11-28)
------------------

Added
~~~~~

New CLI options:

-  :ref:`combine-record-packages`: ``--fake``
-  :ref:`combine-release-packages`: ``--fake``
-  :ref:`compile`: ``--fake``
-  :ref:`package-records`: ``--fake``
-  :ref:`package-releases`: ``--fake``

New CLI commands:

-  :ref:`package-records`

New library methods:

-  :meth:`ocdskit.combine.package_records`

Changed
~~~~~~~

-  :ref:`mapping-sheet`: Improve documentation of ``--extension`` and ``--extension-field``.

Fixed
~~~~~

-  :ref:`detect-format` correctly detects concatenated JSON, even if subsequent JSON values are non-OCDS values.

0.1.3 (2019-09-26)
------------------

Changed
~~~~~~~

-  Set missing package metadata to ``""`` instead of ``null`` in CLI commands, to mirror library methods.

0.1.2 (2019-09-25)
------------------

Changed
~~~~~~~

-  Align the library methods :meth:`ocdskit.util.json_dump` and :meth:`ocdskit.util.json_dumps`.

0.1.1 (2019-09-19)
------------------

Fixed
~~~~~

-  :ref:`upgrade` no longer errors if specific fields are ``null``.
-  :ref:`upgrade` no longer errors on packages that have ``parties`` values without ``id`` fields and that declare no version or a version of "1.0".

0.1.0 (2019-09-17)
------------------

Command-line inputs can now be `concatenated JSON <https://en.wikipedia.org/wiki/JSON_streaming#Concatenated_JSON>`__ or JSON arrays, not only `line-delimited JSON <https://en.wikipedia.org/wiki/JSON_streaming#Line-delimited_JSON>`__.

Added
~~~~~

New CLI commands:

-  :ref:`detect-format`

New CLI options:

-  :ref:`package-releases`:

   -  ``--uri``
   -  ``--published-date``
   -  ``--publisher-name``
   -  ``--publisher-uri``
   -  ``--publisher-scheme``
   -  ``--publisher-uid``

-  :ref:`compile`:

   -  ``--publisher-name``
   -  ``--publisher-uri``
   -  ``--publisher-scheme``
   -  ``--publisher-uid``

-  :ref:`combine-record-packages`:

   -  ``--publisher-name``
   -  ``--publisher-uri``
   -  ``--publisher-scheme``
   -  ``--publisher-uid``

-  :ref:`combine-release-packages`:

   -  ``--publisher-name``
   -  ``--publisher-uri``
   -  ``--publisher-scheme``
   -  ``--publisher-uid``

-  :ref:`mapping-sheet`:

   -  ``--order-by``
   -  ``--infer-required``
   -  ``--extension``
   -  ``--extension-field``

The ``--root-path`` option is added to all OCDS commands.

New library methods:

-  :meth:`ocdskit.combine.package_releases`
-  :meth:`ocdskit.combine.combine_record_packages`
-  :meth:`ocdskit.combine.combine_release_packages`
-  :meth:`ocdskit.combine.compile_release_packages`
-  :meth:`ocdskit.mapping_sheet.mapping_sheet`
-  :meth:`ocdskit.schema.get_schema_fields`

Changed
~~~~~~~

-  **Backwards-incompatible**: :meth:`ocdskit.upgrade.upgrade_10_10`, :meth:`ocdskit.upgrade.upgrade_11_11` and :meth:`ocdskit.upgrade.upgrade_10_11` now return data, instead of only editing in-place.
-  **Backwards-incompatible**: :ref:`mapping-sheet` and :ref:`schema-report` now read a file argument instead of standard input, to support schema that ``$ref`` other schema.
-  :ref:`mapping-sheet` and :ref:`schema-report` support schema from: Open Contracting for Infrastructure Data Standard (OC4IDS), Beneficial Ownership Data Standard (BODS), and Social Investment Data Lab Specification (SEDL).
-  :ref:`mapping-sheet` outputs:

   -  ``enum`` values of ``items``
   -  ``enum`` as “Enum:” instead of “Codelist:”
   -  ``pattern`` as “Pattern:”

-  :ref:`schema-strict` adds ``"uniqueItems": true`` to all arrays, unless ``--no-unique-items`` is set.
-  Use ``https://`` instead of ``http://`` for ``standard.open-contracting.org``.

Fixed
~~~~~

-  :ref:`compile` merges extensions' schema into the release schema before merging releases.
-  :ref:`mapping-sheet` fills in the deprecated column if an object field uses ``$ref``.
-  :ref:`schema-strict` no longer errors if a required field uses ``$ref``.
-  :ref:`upgrade` no longer errors if ``awards`` or ``contracts`` is ``null``.

0.0.5 (2019-01-11)
------------------

Added
~~~~~

New CLI options:

-  :ref:`compile`:

   -  ``--schema``: You can create compiled releases and versioned releases using a specific release schema.
   -  ``--linked-releases``: You can have the record package use linked releases instead of full releases.
   -  ``--uri``, ``--published-date``: You can set the ``uri`` and ``publishedDate`` of the record package.

      -  If not set, these will be ``null`` instead of the ``uri`` and ``publishedDate`` of the last package.

-  :ref:`combine-record-packages`: ``--uri``, ``--published-date``
-  :ref:`combine-release-packages`: ``--uri``, ``--published-date``

New CLI commands:

-  :ref:`upgrade`

Changed
~~~~~~~

-  :ref:`compile` raises an error if the release packages use different versions.
-  :ref:`compile` determines the version of the release schema to use if ``--schema`` isn’t set.
-  :ref:`compile`, :ref:`combine-record-packages` and :ref:`combine-release-packages` have a predictable field order.
-  ``measure`` is removed.

Fixed
~~~~~

-  :ref:`indent` prints an error if a path doesn’t exist.
-  :ref:`compile`, :ref:`combine-record-packages` and :ref:`combine-release-packages` succeed if the required ``publisher`` field is missing.

0.0.4 (2018-11-23)
------------------

Added
~~~~~

New CLI options:

-  :ref:`schema-report`: ``--no-codelists``, ``--no-definitions``, ``--min-occurrences``

Changed
~~~~~~~

-  :ref:`schema-report` reports definitions that can use a common ``$ref`` in the versioned release schema.
-  :ref:`schema-report` reports open and closed codelists in CSV format.

0.0.3 (2018-11-01)
------------------

Added
~~~~~

New CLI options:

-  :ref:`compile`: ``--package``, ``--versioned``

New CLI commands:

-  :ref:`package-releases`
-  :ref:`split-record-packages`
-  :ref:`split-release-packages`

Changed
~~~~~~~

-  Add helpful error messages if:

   -  the input is not `line-delimited JSON <https://en.wikipedia.org/wiki/JSON_streaming>`__ data.
   -  the input to the :ref:`indent` command is not valid JSON.

-  Change default behavior to print UTF-8 characters instead of escape sequences.
-  Add ``--ascii`` option to print escape sequences instead of UTF-8 characters.
-  Rename base exception class from ``ReportError`` to :class:`OCDSKitError`.

0.0.2 (2018-03-14)
------------------

Added
~~~~~

New CLI options:

-  ``validate``: ``--check-urls`` and ``--timeout``

New CLI commands:

-  :ref:`indent`
-  :ref:`schema-report`
-  :ref:`schema-strict`
-  :ref:`set-closed-codelist-enums`

0.0.1 (2017-12-25)
------------------

Added
~~~~~

New CLI commands:

-  :ref:`combine-record-packages`
-  :ref:`combine-release-packages`
-  :ref:`compile`
-  :ref:`mapping-sheet`
-  ``measure``
-  ``tabulate``
-  ``validate``

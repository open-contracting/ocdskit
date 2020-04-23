Changelog
=========

0.2.7 (2020-04-23)
------------------

Added
~~~~~

New CLI options:

-  ``combine-record-packages``: ``--version``
-  ``combine-release-packages``: ``--version``
-  ``compile``: ``--version``
-  ``convert-to-oc4ids``: ``--version``
-  ``package-records``: ``--version``
-  ``package-releases``: ``--version``

New library method:

-  :meth:`ocdskit.util.is_compiled_release`

Changed
~~~~~~~

-  ``merge`` sets ``"version": "1.1"`` even on OCDS 1.0 data (see :meth:`~ocdskit.combine.merge`).
-  ``package-records`` and ``package-releases`` omit the ``extensions`` field if empty (see :meth:`~ocdskit.combine.package_records`, :meth:`~ocdskit.combine.package_releases`).

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

-  ``combine-record-packages`` and ``combine-release-packages`` warn if the ``"records"`` and ``"releases"`` fields aren't set (see :meth:`~ocdskit.combine.combine_record_packages`, :meth:`~ocdskit.combine.combine_release_packages`).

0.2.5 (2020-04-14)
------------------

Fixed
~~~~~

-  ``combine-record-packages`` and ``combine-release-packages`` no longer error if the ``"records"`` and ``"releases"`` fields aren't set (see :meth:`~ocdskit.combine.combine_record_packages`, :meth:`~ocdskit.combine.combine_release_packages`).

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

-  :mod:`ocdskit.oc4ids`

Changed
~~~~~~~

-  ``compile`` errors if an ``ocid`` field is missing from a release (see :meth:`~ocdskit.packager.AbstractBackend.add_release`).
-  ``upgrade`` upgrades records (see :meth:`~ocdskit.upgrade.upgrade_10_11`).

0.2.2 (2019-01-07)
------------------

Changed
~~~~~~~

-  Avoid exception when piping output to tools like ``head``.
-  ``package-records``, ``package-releases``: Use fast writer if ``--size`` is set.
-  ``echo``: Use fast writer (assuming ``--root-path`` is set anytime input is too large).

0.2.1 (2020-01-06)
------------------

Added
~~~~~

New CLI options:

-  ``package-records``: ``--size``
-  ``package-releases``: ``--size``

New CLI commands:

-  ``echo``

Changed
~~~~~~~

-  Implement iterative JSON writer.
-  Use ``orjson`` if available to improve performance of dumping/loading JSON, especially to/from SQL in ``compile`` command (see :mod:`ocdskit.packager`).

Fixed
~~~~~

-  ``combine-record-packages`` no longer duplicates release package URLs in ``packages`` (see :meth:`ocdskit.combine.combine_record_packages`).

0.2.0 (2019-12-31)
------------------

Added
~~~~~

New library module:

-  :mod:`ocdskit.packager`

Changed
~~~~~~~

CLI:

-  ``compile`` accepts either release packages or individual releases (see :meth:`~ocdskit.combine.merge`).
-  ``compile`` is memory efficient if given a long list of inputs (see :meth:`~ocdskit.combine.merge`).

Library:

-  Deprecate ``ocdskit.combine.compile_release_packages`` in favor of :meth:`ocdskit.combine.merge`.

Fixed
~~~~~

-  ``--linked-releases`` no longer uses the same linked releases for all records (see :meth:`~ocdskit.packager.Packager.output_records`).

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

-  ``combine-record-packages``: ``--fake``
-  ``combine-release-packages``: ``--fake``
-  ``compile``: ``--fake``
-  ``package-records``: ``--fake``
-  ``package-releases``: ``--fake``

New CLI commands:

-  ``package-records``

New library methods:

-  :meth:`ocdskit.combine.package_records`

Changed
~~~~~~~

-  ``mapping-sheet``: Improve documentation of ``--extension`` and ``--extension-field``.

Fixed
~~~~~

-  ``detect-format`` correctly detects concatenated JSON, even if subsequent JSON values are non-OCDS values.

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

-  ``upgrade`` no longer errors if specific fields are ``null``.
-  ``upgrade`` no longer errors on packages that have ``parties`` without ``id`` fields and that declare no version or a version of "1.0".

0.1.0 (2019-09-17)
------------------

Command-line inputs can now be `concatenated JSON <https://en.wikipedia.org/wiki/JSON_streaming#Concatenated_JSON>`__ or JSON arrays, not only `line-delimited JSON <https://en.wikipedia.org/wiki/JSON_streaming#Line-delimited_JSON>`__.

Added
~~~~~

New CLI commands:

-  ``detect-format``

New CLI options:

-  ``package-releases``:

   -  ``--uri``
   -  ``--published-date``
   -  ``--publisher-name``
   -  ``--publisher-uri``
   -  ``--publisher-scheme``
   -  ``--publisher-uid``

-  ``compile``:

   -  ``--publisher-name``
   -  ``--publisher-uri``
   -  ``--publisher-scheme``
   -  ``--publisher-uid``

-  ``combine-record-packages``:

   -  ``--publisher-name``
   -  ``--publisher-uri``
   -  ``--publisher-scheme``
   -  ``--publisher-uid``

-  ``combine-release-packages``:

   -  ``--publisher-name``
   -  ``--publisher-uri``
   -  ``--publisher-scheme``
   -  ``--publisher-uid``

-  ``mapping-sheet``:

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

-  **Backwards-incompatible**: :meth:`~ocdskit.upgrade.upgrade_10_10`, :meth:`~ocdskit.upgrade.upgrade_11_11` and :meth:`~ocdskit.upgrade.upgrade_10_11` now return data, instead of only editing in-place.
-  **Backwards-incompatible**: ``mapping-sheet`` and ``schema-report`` now read a file argument instead of standard input, to support schema that ``$ref`` other schema.
-  ``mapping-sheet`` and ``schema-report`` support schema from: Open Contracting for Infrastructure Data Standard (OC4IDS), Beneficial Ownership Data Standard (BODS), and Social Investment Data Lab Specification (SEDL).
-  ``mapping-sheet`` outputs:

   -  ``enum`` values of ``items``
   -  ``enum`` as “Enum:” instead of “Codelist:”
   -  ``pattern`` as “Pattern:”

-  ``schema-strict`` adds ``"uniqueItems": true`` to all arrays, unless ``--no-unique-items`` is set.
-  Use ``https://`` instead of ``http://`` for ``standard.open-contracting.org``.

Fixed
~~~~~

-  ``compile`` merges extensions' schema into the release schema before merging releases.
-  ``mapping-sheet`` fills in the deprecated column if an object field uses ``$ref``.
-  ``schema-strict`` no longer errors if a required field uses ``$ref``.
-  ``upgrade`` no longer errors if ``awards`` or ``contracts`` is ``null``.

0.0.5 (2019-01-11)
------------------

Added
~~~~~

New CLI options:

-  ``compile``:

   -  ``--schema``: You can create compiled releases and versioned releases using a specific release schema.
   -  ``--linked-releases``: You can have the record package use linked releases instead of full releases.
   -  ``--uri``, ``--published-date``: You can set the ``uri`` and ``publishedDate`` of the record package.

      -  If not set, these will be ``null`` instead of the ``uri`` and ``publishedDate`` of the last package.

-  ``combine-record-packages``: ``--uri``, ``--published-date``
-  ``combine-release-packages``: ``--uri``, ``--published-date``

New CLI commands:

-  ``upgrade``

Changed
~~~~~~~

-  ``compile`` raises an error if the release packages use different versions.
-  ``compile`` determines the version of the release schema to use if ``--schema`` isn’t set.
-  ``compile``, ``combine-record-packages`` and ``combine-release-packages`` have a predictable field order.
-  ``measure`` is removed.

Fixed
~~~~~

-  ``indent`` prints an error if a path doesn’t exist.
-  ``compile``, ``combine-record-packages`` and ``combine-release-packages`` succeed if the required ``publisher`` field is missing.

0.0.4 (2018-11-23)
------------------

Added
~~~~~

New CLI options:

-  ``schema-report``: ``--no-codelists``, ``--no-definitions``, ``--min-occurrences``

Changed
~~~~~~~

-  ``schema-report`` reports definitions that can use a common ``$ref`` in the versioned release schema.
-  ``schema-report`` reports open and closed codelists in CSV format.

0.0.3 (2018-11-01)
------------------

Added
~~~~~

New CLI options:

-  ``compile``: ``--package``, ``--versioned``

New CLI commands:

-  ``package-releases``
-  ``split-record-packages``
-  ``split-release-packages``

Changed
~~~~~~~

-  Add helpful error messages if:

   -  the input is not `line-delimited JSON <https://en.wikipedia.org/wiki/JSON_streaming>`__ data.
   -  the input to the ``indent`` command is not valid JSON.

-  Change default behavior to print UTF-8 characters instead of escape sequences.
-  Add ``--ascii`` option to print escape sequences instead of UTF-8 characters.
-  Rename base exception class from ``ReportError`` to ``OCDSKitError``.

0.0.2 (2018-03-14)
------------------

Added
~~~~~

New CLI options:

-  ``validate``: ``--check-urls`` and ``--timeout``

New CLI commands:

-  ``indent``
-  ``schema-report``
-  ``schema-strict``
-  ``set-closed-codelist-enums``

0.0.1 (2017-12-25)
------------------

Added
~~~~~

New CLI commands:

-  ``combine-record-packages``
-  ``combine-release-packages``
-  ``compile``
-  ``mapping-sheet``
-  ``measure``
-  ``tabulate``
-  ``validate``

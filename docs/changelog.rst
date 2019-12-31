Changelog
=========

0.2.0 (2019-12-31)
------------------

Changed
~~~~~~~

CLI:

-  ``compile`` accepts either release packages or individual releases
-  ``compile`` is memory efficient if given a long list of inputs

Library:

-  Rename ``compile_release_packages`` to ``merge``
-  Add ``packager`` module with ``Packager`` class

Fixed
~~~~~

-  ``--linked-releases`` no longer uses the same linked releases for all records

0.1.5 (2019-12-18)
------------------

Added
~~~~~

New library methods:

-  ``is_record``
-  ``is_release``

The internal methods ``json_load`` and ``json_loads`` are removed.

0.1.4 (2019-11-28)
------------------

Fixed
~~~~~

-  ``detect-format`` correctly detects concatenated JSON, even if subsequent JSON values are non-OCDS values.

Added
~~~~~

New CLI options:

-  combine-record-packages: ``--fake``
-  combine-release-packages: ``--fake``
-  compile: ``--fake``
-  package-records: ``--fake``
-  package-releases: ``--fake``

New CLI commands:

-  package-records

New library methods:

-  ``package_records``

Changed
~~~~~~~

-  mapping-sheet: Improved documentation of ``--extension`` and ``--extension-field``.

0.1.3 (2019-09-26)
------------------

Changed
~~~~~~~

-  Set missing package metadata to ``""`` instead of ``null`` in CLI commands, to mirror library methods.

0.1.2 (2019-09-25)
------------------

Changed
~~~~~~~

-  Align the library methods ``json_dump`` and ``json_dumps``.

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

-  detect-format

New CLI options:

-  package-releases: ``--uri``, ``--published-date``, ``--publisher-name``, ``--publisher-uri``, ``--publisher-scheme``, ``--publisher-uid``
-  compile: ``--publisher-name``, ``--publisher-uri``, ``--publisher-scheme``, ``--publisher-uid``
-  combine-record-packages: ``--publisher-name``, ``--publisher-uri``, ``--publisher-scheme``, ``--publisher-uid``
-  combine-release-packages: ``--publisher-name``, ``--publisher-uri``, ``--publisher-scheme``, ``--publisher-uid``
-  mapping-sheet: ``--order-by``, ``--infer-required``, ``--extension``, ``--extension-field``

The ``--root-path`` option is added to all OCDS commands.

New library methods:

-  ``compile_release_packages``
-  ``package_releases``
-  ``combine_record_packages``
-  ``combine_release_packages``
-  ``mapping_sheet``
-  ``get_schema_fields``

Changed
~~~~~~~

-  **Backwards-incompatible**: ``upgrade_10_10``, ``upgrade_11_11`` and ``upgrade_10_11`` now return data, instead of only editing in-place.
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

-  compile:

   -  ``--schema``: You can create compiled releases and versioned releases using a specific release schema.
   -  ``--linked-releases``: You can have the record package use linked releases instead of full releases.
   -  ``--uri``, ``--published-date``: You can set the ``uri`` and ``publishedDate`` of the record package.

      -  If not set, these will be ``null`` instead of the ``uri`` and ``publishedDate`` of the last package.

-  combine-record-packages: ``--uri``, ``--published-date``
-  combine-release-packages: ``--uri``, ``--published-date``

New CLI commands:

-  upgrade

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

-  schema-report: ``--no-codelists``, ``--no-definitions``, ``--min-occurrences``

Changed
~~~~~~~

-  ``schema-report`` reports definitions that can use a common ``$ref`` in the versioned release schema.
-  ``schema-report`` reports open and closed codelists in CSV format.

0.0.3 (2018-11-01)
------------------

Added
~~~~~

New CLI options:

-  compile: ``--package``, ``--versioned``

New CLI commands:

-  package-releases
-  split-record-packages
-  split-release-packages

Changed
~~~~~~~

-  Add helpful error messages if:

   -  the input is not `line-delimited JSON <https://en.wikipedia.org/wiki/JSON_streaming>`__ data;
   -  the input to the ``indent`` command is not valid JSON.

-  Change default behavior to print UTF-8 characters instead of escape sequences.
-  Add ``--ascii`` option to print escape sequences instead of UTF-8 characters.
-  Rename base exception class from ``ReportError`` to ``OCDSKitError``.

0.0.2 (2018-03-14)
------------------

Added
~~~~~

New CLI options:

-  validate: ``--check-urls`` and ``--timeout``

New CLI commands:

-  indent
-  schema-report
-  schema-strict
-  set-closed-codelist-enums

0.0.1 (2017-12-25)
------------------

Added
~~~~~

New CLI commands:

-  combine-record-packages
-  combine-release-packages
-  compile
-  mapping-sheet
-  measure
-  tabulate
-  validate

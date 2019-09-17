Changelog
=========

0.1.0
-----

Inputs can now be `concatenated JSON <https://en.wikipedia.org/wiki/JSON_streaming#Concatenated_JSON`__ or JSON arrays, not only `line-delimited JSON <https://en.wikipedia.org/wiki/JSON_streaming#Line-delimited_JSON>`__.

Added
~~~~~

New library methods:

-  ``compile_release_packages``
-  ``package_releases``
-  ``combine_record_packages``
-  ``combine_release_packages``
-  ``mapping_sheet``
-  ``get_schema_fields``

New options:

-  package-releases: ``--uri``, ``--published-date``, ``--publisher-name``, ``--publisher-uri``, ``--publisher-scheme``, ``--publisher-uid``
-  compile: ``--publisher-name``, ``--publisher-uri``, ``--publisher-scheme``, ``--publisher-uid``
-  combine-record-packages: ``--publisher-name``, ``--publisher-uri``, ``--publisher-scheme``, ``--publisher-uid``
-  combine-release-packages: ``--publisher-name``, ``--publisher-uri``, ``--publisher-scheme``, ``--publisher-uid``
-  mapping-sheet: ``--order-by``, ``--infer-required``, ``--extension``, ``--extension-field``

The ``--root-path`` option is added to all OCDS commands.

Changed
~~~~~~~

-  **Backwards-incompatible**: ``upgrade_10_10``, ``upgrade_11_11`` and ``upgrade_10_11`` now return data, instead of only editing in-place.
-  **Backwards-incompatible**: ``mapping-sheet`` and ``schema-report`` now read a file argument instead of standard input, to support schema that ``$ref`` other schema.
-  ``mapping-sheet`` and ``schema-report`` support schema from: Open Contracting for Infrastructure Data Standard (OC4IDS), Beneficial Ownership Data Standard (BODS), Social Investment Data Lab Specification (SEDL).
-  ``mapping-sheet`` outputs:

   -  ``enum`` values of ``items``
   -  ``enum`` as “Enum:” instead of “Codelist:”
   -  ``pattern`` as “Pattern:”

-  ``schema-strict`` adds ``"uniqueItems": true`` to all arrays, unless ``--no-unique-items`` is set.
-  Use ``https://`` instead of ``http://`` for ``standard.open-contracting.org``.

Fixed
~~~~~

-  ``mapping-sheet`` fills in the deprecated column if an object field uses ``$ref``.
-  ``schema-strict`` no longer errors if a required field uses ``$ref``.
-  ``upgrade`` no longer errors if ``awards`` or ``contracts`` is ``null``.

0.0.5 (2019-01-11)
------------------

Added
~~~~~

New options:

-  compile:

   -  ``--schema``: You can create compiled releases and versioned releases using a specific release schema.
   -  ``--linked-releases``: You can have the record package use linked releases instead of full releases.
   -  ``--uri``, ``--published-date``: You can set the ``uri`` and ``publishedDate`` of the record package.

      -  If not set, these will be ``null`` instead of the ``uri`` and ``publishedDate`` of the last package.

-  combine-record-packages: ``--uri``, ``--published-date``
-  combine-release-packages: ``--uri``, ``--published-date``

New commands:

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

New options:

-  schema-report: ``--no-codelists``, ``--no-definitions``, ``--min-occurrences``

Changed
~~~~~~~

-  ``schema-report`` reports definitions that can use a common ``$ref`` in the versioned release schema.
-  ``schema-report`` reports open and closed codelists in CSV format.

0.0.3 (2018-11-01)
------------------

Added
~~~~~

New options:

-  compile: ``--package``, ``--versioned``

New commands:

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

New options:

-  validate: ``--check-urls`` and ``--timeout``

New commands:

-  indent
-  schema-report
-  schema-strict
-  set-closed-codelist-enums

0.0.1 (2017-12-25)
------------------

Added
~~~~~

New commands:

-  combine-record-packages
-  combine-release-packages
-  compile
-  mapping-sheet
-  measure
-  tabulate
-  validate

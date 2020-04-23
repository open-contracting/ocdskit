OCDS Commands
=============

Optional arguments for all commands are:

* ``--encoding ENCODING`` the file encoding
* ``--ascii`` print escape sequences instead of UTF-8 characters
* ``--pretty`` pretty print output
* ``--root-path ROOT_PATH`` the path to the items to process within each input

The inputs can be `concatenated JSON <https://en.wikipedia.org/wiki/JSON_streaming#Concatenated_JSON>`__ or JSON arrays.

Handling edge cases
-------------------

Large packages
~~~~~~~~~~~~~~

If you are working with individual packages that are too large to hold in memory, use the :ref:`echo` command to reduce their size.

.. _embedded-data:

Embedded data
~~~~~~~~~~~~~

If you are working with files that embed OCDS data, use the ``--root-path ROOT_PATH`` option to indicate the "root" path to the items to process within each input. For example, if release packages are in an array under a ``results`` key, like so:

.. code:: json

   {
     "results": [
       {
         "uri": "placeholder:",
         "publisher": {"name": ""},
         "publishedDate": "9999-01-01T00:00:00Z",
         "version": "1.1",
         "releases": []
       }
     ]
   }

You can run ``ocdskit <command> --root-path results`` to process the release packages. The root path, in this case, is simply the ``results`` key. OCDS Kit will read the entire ``results`` array into memory, and process each array entry.

If the ``results`` array is very large, you should run ``ocdskit <command> --root-path results.item`` instead. The root path, in this case, is the ``results`` key joined to the ``item`` literal by a period (the ``item`` literal indicates that the items to process are in an array). OCDS Kit will read each array entry into memory, instead of the entire ``results`` array.

For this next example, you can run ``ocdskit <command> --root-path results.item.ocdsReleasePackage``:

.. code:: json

   {
     "results": [
       {
         "ocdsReleasePackage": {
           "uri": "placeholder:",
           "publisher": {"name": ""},
           "publishedDate": "9999-01-01T00:00:00Z",
           "version": "1.1",
           "releases": []
         }
       }
     ]
   }

The root path, in this case, is the ``results`` key joined to the ``item`` literal, joined to the ``ocdsReleasePackage`` key.

detect-format
-------------

Reads OCDS files, and reports whether each is:

* a release package
* a record package
* a release
* a record
* a compiled release
* a versioned release
* a JSON array of one of the above
* `concatenated JSON <https://en.wikipedia.org/wiki/JSON_streaming#Concatenated_JSON>`__ of one of the above

Mandatory positional arguments:

* ``file`` OCDS files

::

    ocdskit detect-format tests/fixtures/realdata/release-package-1.json tests/fixtures/realdata/record-package-1.json

compile
-------

Reads release packages and individual releases from standard input, merges the releases by OCID, and prints the compiled releases.

Optional arguments:

* ``--schema SCHEMA`` the URL or path of the release schema to use
* ``--package`` wrap the compiled releases in a record package
* ``--linked-releases`` if ``--package`` is set, use linked releases instead of full releases, if the input is a release package
* ``--versioned`` if ``--package`` is set, include versioned releases in the record package; otherwise, print versioned releases instead of compiled releases
* ``--uri URI`` if ``--package`` is set, set the record package's ``uri`` to this value
* ``--published-date PUBLISHED_DATE`` if ``--package`` is set, set the record package's ``publishedDate`` to this value
* ``--version VERSION`` if ``--package`` is set, set the record package's ``version`` to this value
* ``--publisher-name PUBLISHER_NAME`` if ``--package`` is set, set the record package's ``publisher``'s ``name`` to this value
* ``--publisher-uri PUBLISHER_URI`` if ``--package`` is set, set the record package's ``publisher``'s ``uri`` to this value
* ``--publisher-scheme PUBLISHER_SCHEME`` if ``--package`` is set, set the record package's ``publisher``'s ``scheme`` to this value
* ``--publisher-uid PUBLISHER_UID`` if ``--package`` is set, set the record package's ``publisher``'s ``uid`` to this value
* ``--fake`` if ``--package`` is set, set the record package's required metadata to dummy values

If ``--package`` is set, and if the ``--publisher-*`` options aren't used, the output package will have the same publisher as the last input package.

::

    cat tests/fixtures/realdata/release-package-1.json | ocdskit compile > out.json

For the Python API, see :meth:`ocdskit.combine.merge`.

upgrade
-------

Upgrades packages, records and releases from an old version of OCDS to a new version. Any data not in the old version is passed through. **Note:** Versioned releases within a record package are not upgraded.

OCDS 1.0 `describes <https://standard.open-contracting.org/1.0/en/schema/reference/#identifier>`__ an organization's ``name``, ``identifier``, ``address`` and ``contactPoint`` as relevant to identifying it. OCDS 1.1 `moves <https://standard.open-contracting.org/1.1/en/schema/reference/#parties>`__ organization data into a ``parties`` array. To upgrade from OCDS 1.0 to 1.1, we create an ``id`` for each organization, based on those identifying fields. This can result in duplicates in the ``parties`` array, if the same organization has different or missing values for identifying fields in different contexts. This can also lead to data loss if the same organization has different values for non-identifying fields in different contexts; the command prints warnings in such cases.

**Note:** OCDS 1.0 uses the `whole-list merge <https://standard.open-contracting.org/1.0/en/schema/merging/#merging-rules>`__ strategy on the ``suppliers`` array to prepare the compiled release and versioned release, whereas OCDS 1.1 uses the `identifier merge <https://standard.open-contracting.org/1.1/en/schema/merging/#identifier-merge>`__ strategy. This means that you should merge first and then upgrade.

Mandatory positional arguments:

* ``versions`` the colon-separated old and new versions

::

    cat tests/fixtures/realdata/release-package-1.json | ocdskit upgrade 1.0:1.1 > out.json

For the Python API, see :doc:`../api/upgrade`.

If a *release* package is too large, you can upgrade its individual releases using ``--root-path releases.item``.

.. _package-records:

package-records
---------------

Reads records from standard input, and prints one record package.

Optional positional arguments:

* ``extension`` add this extension to the package

Optional arguments:

* ``--uri URL`` set the record package's ``uri`` to this value
* ``--published-date PUBLISHED_DATE`` set the record package's ``publishedDate`` to this value
* ``--version VERSION`` set the record package's ``version`` to this value
* ``--publisher-name PUBLISHER_NAME`` set the record package's ``publisher``'s ``name`` to this value
* ``--publisher-uri PUBLISHER_URI`` set the record package's ``publisher``'s ``uri`` to this value
* ``--publisher-scheme PUBLISHER_SCHEME`` set the record package's ``publisher``'s ``scheme`` to this value
* ``--publisher-uid PUBLISHER_UID`` set the record package's ``publisher``'s ``uid`` to this value
* ``--fake`` set the record package's required metadata to dummy values

::

    cat tests/fixtures/record_*.json | ocdskit package-records > out.json

To convert record packages to a record package, you can use the ``--root-path`` option::

    cat tests/fixtures/realdata/record-package* | ocdskit package-records --root-path records.item

If ``--uri`` and ``--published-date`` are not set, the output package will be invalid. Use ``--fake`` to set placeholder values.

For the Python API, see :meth:`ocdskit.combine.package_records`.

.. _package-releases:

package-releases
----------------

Reads releases from standard input, and prints one release package.

Optional positional arguments:

* ``extension`` add this extension to the package

Optional arguments:

* ``--uri URL`` set the release package's ``uri`` to this value
* ``--published-date PUBLISHED_DATE`` set the release package's ``publishedDate`` to this value
* ``--version VERSION`` set the release package's ``version`` to this value
* ``--publisher-name PUBLISHER_NAME`` set the release package's ``publisher``'s ``name`` to this value
* ``--publisher-uri PUBLISHER_URI`` set the release package's ``publisher``'s ``uri`` to this value
* ``--publisher-scheme PUBLISHER_SCHEME`` set the release package's ``publisher``'s ``scheme`` to this value
* ``--publisher-uid PUBLISHER_UID`` set the release package's ``publisher``'s ``uid`` to this value
* ``--fake`` set the release package's required metadata to dummy values

::

    cat tests/fixtures/release_*.json | ocdskit package-releases > out.json

To convert record packages to a release package, you can use the ``--root-path`` option::

    cat tests/fixtures/realdata/record-package* | ocdskit package-releases --root-path records.item.releases.item

If ``--uri`` and ``--published-date`` are not set, the output package will be invalid. Use ``--fake`` to set placeholder values.

For the Python API, see :meth:`ocdskit.combine.package_releases`.

combine-record-packages
-----------------------

Reads record packages from standard input, collects packages and records, and prints one record package.

If the ``--publisher-*`` options aren't used, the output package will have the same publisher as the last input package.

Optional arguments:

* ``--uri URL`` set the record package's ``uri`` to this value
* ``--published-date PUBLISHED_DATE`` set the record package's ``publishedDate`` to this value
* ``--version VERSION`` set the record package's ``version`` to this value
* ``--publisher-name PUBLISHER_NAME`` set the record package's ``publisher``'s ``name`` to this value
* ``--publisher-uri PUBLISHER_URI`` set the record package's ``publisher``'s ``uri`` to this value
* ``--publisher-scheme PUBLISHER_SCHEME`` set the record package's ``publisher``'s ``scheme`` to this value
* ``--publisher-uid PUBLISHER_UID`` set the record package's ``publisher``'s ``uid`` to this value
* ``--fake`` set the record package's required metadata to dummy values

::

    cat tests/fixtures/record-package_*.json | ocdskit combine-record-packages > out.json

If you need to create a single package that is too large to hold in your system's memory, please `comment on this issue <https://github.com/open-contracting/ocdskit/issues/119>`__.

For the Python API, see :meth:`ocdskit.combine.combine_record_packages`.

combine-release-packages
------------------------

Reads release packages from standard input, collects releases, and prints one release package.

If the ``--publisher-*`` options aren't used, the output package will have the same publisher as the last input package.

Optional arguments:

* ``--uri URL`` set the release package's ``uri`` to this value
* ``--published-date PUBLISHED_DATE`` set the release package's ``publishedDate`` to this value
* ``--version VERSION`` set the release package's ``version`` to this value
* ``--publisher-name PUBLISHER_NAME`` set the release package's ``publisher``'s ``name`` to this value
* ``--publisher-uri PUBLISHER_URI`` set the release package's ``publisher``'s ``uri`` to this value
* ``--publisher-scheme PUBLISHER_SCHEME`` set the release package's ``publisher``'s ``scheme`` to this value
* ``--publisher-uid PUBLISHER_UID`` set the release package's ``publisher``'s ``uid`` to this value
* ``--fake`` set the release package's required metadata to dummy values

::

    cat tests/fixtures/release-package_*.json | ocdskit combine-release-packages > out.json

If you need to create a single package that is too large to hold in your system's memory, please `comment on this issue <https://github.com/open-contracting/ocdskit/issues/119>`__.

For the Python API, see :meth:`ocdskit.combine.combine_release_packages`.

.. _split-record-packages:

split-record-packages
---------------------

Reads record packages from standard input, and prints smaller record packages for each.

Mandatory positional arguments:

* ``size`` the number of records per package

::

    cat tests/fixtures/realdata/record-package-1-2.json | ocdskit split-record-packages 2 | split -l 1 -a 4

The ``split`` command will write files named ``xaaaa``, ``xaaab``, ``xaaac``, etc. Don't combine the OCDS Kit ``--pretty`` option with the ``split`` command.

.. _split-release-packages:

split-release-packages
----------------------

Reads release packages from standard input, and prints smaller release packages for each.

Mandatory positional arguments:

* ``size`` the number of releases per package

::

    cat tests/fixtures/realdata/release-package-1-2.json | ocdskit split-release-packages 2 | split -l 1 -a 4

The ``split`` command will write files named ``xaaaa``, ``xaaab``, ``xaaac``, etc. Don't combine the OCDS Kit ``--pretty`` option with the ``split`` command.

tabulate
--------

Load packages into a database.

Mandatory positional arguments:

* ``database_url`` a SQLAlchemy `database URL <https://docs.sqlalchemy.org/en/13/core/engines.html#database-urls>`__

Optional arguments:

* ``--drop`` drop all tables before loading
* ``--schema SCHEMA`` the release-schema.json to use

::

    cat release_package.json | ocdskit tabulate sqlite:///data.db

For the format of ``database_url``, see the `SQLAlchemy documentation <https://docs.sqlalchemy.org/en/rel_1_1/core/engines.html#database-urls>`__.

validate
--------

Reads JSON data from standard input, validates it against the schema, and prints errors.

Optional arguments:

* ``--schema SCHEMA`` the URL or path of the schema to validate against
* ``--check-urls`` check the HTTP status code if "format": "uri"
* ``--timeout TIMEOUT`` timeout (seconds) to GET a URL
* ``--verbose`` print items without validation errors

::

    cat tests/fixtures/* | ocdskit validate

.. _echo:

echo
----

Repeats the input, applying ``--encoding``, ``--ascii``, ``--pretty`` and ``--root-path``, and using the UTF-8 encoding.

You can use this command to reformat data:

-  Use UTF-8 encoding::

      cat iso-8859-1.json | ocdskit --encoding iso-8859-1 echo > utf-8.json

-  Use ASCII characters only::

      cat unicode.json | ocdskit --ascii echo > ascii.json

-  Use UTF-8 characters where possible::

      cat ascii.json | ocdskit echo > unicode.json

-  Pretty print::

      cat compact.json | ocdskit --pretty echo > pretty.json

-  Make compact::

      cat pretty.json | ocdskit echo > compact.json

You can also use this command to extract releases from release packages, and records from record packages. This is especially useful if a single package is too large to hold in memory.

-  Split a large record package into smaller packages of 100 records each::

      cat large-record-package.json | ocdskit echo --root-path records.item | ocdskit package-records --size 100

-  Split a large release package into smaller packages of 1,000 releases each::

      cat large-release-package.json | ocdskit echo --root-path releases.item | ocdskit package-releases --size 1000

Note that the package metadata from the large package won't be retained in the smaller packages; you can use the optional arguments of the :ref:`package-records` and :ref:`package-releases` commands to set the package metadata.

If the single package is small enough to hold in memory, you can use the :ref:`split-record-packages` and :ref:`split-release-packages` commands instead, which retain the package metadata.

convert-to-oc4ids
-----------------

Reads individual releases or release packages from standard input, and prints a single project conforming to the `Open Contracting for Infrastructure Data Standards (OC4IDS) <https://standard.open-contracting.org/infrastructure/>`__. It assumes all inputs belong to the same project.

`The logic for the mappings between OCDS and OC4IDS fields is documented here <https://standard.open-contracting.org/infrastructure/latest/en/cost/#mapping-to-ids-and-from-ocds>`__.

Optional arguments:

* ``--project-id PROJECT_ID`` set the project's ``id`` to this value
* ``--all-transforms`` run all optional transforms
* ``--transforms OPTIONS`` comma-separated list of optional transforms to run
* ``--package`` wrap the project in a project package
* ``--uri URI`` if ``--package`` is set, set the project package's ``uri`` to this value
* ``--published-date PUBLISHED_DATE`` if ``--package`` is set, set the project package's ``publishedDate`` to this value
* ``--version VERSION`` if ``--package`` is set, set the project package's ``version`` to this value
* ``--publisher-name PUBLISHER_NAME`` if ``--package`` is set, set the project package's ``publisher``'s ``name`` to this value
* ``--publisher-uri PUBLISHER_URI`` if ``--package`` is set, set the project package's ``publisher``'s ``uri`` to this value
* ``--publisher-scheme PUBLISHER_SCHEME`` if ``--package`` is set, set the project package's ``publisher``'s ``scheme`` to this value
* ``--publisher-uid PUBLISHER_UID`` if ``--package`` is set, set the project package's ``publisher``'s ``uid`` to this value
* ``--fake`` if ``--package`` is set, set the project package's required metadata to dummy values

::

    cat releases.json | ocdskit convert-to-oc4ids > out.json

Transforms
~~~~~~~~~~

The transforms that are run are described here.

* ``additional_classifications``, ``description``, ``sector``, ``title``: populate top-level fields with their equivalents from ``planning.project`` 
* ``administrative_entity``, ``public_authority_role``, ``procuring_entity``, ``suppliers``: populate the ``parties`` field according to the party ``role``
* ``budget``: populates ``budget.amount`` with its equivalent
* ``budget_approval``, ``environmental_impact``, ``land_and_settlement_impact`` and ``project_scope``: populate the ``documents`` field from ``planning.documents`` according to the ``documentType``
* ``contracting_process_setup``: Sets up the ``contractingProcesses`` array of objects with ``id``, ``summary``, ``releases`` and ``embeddedReleases``. Some of the other transforms depend on this, so it is run first
* ``contract_period``: populates the ``summary.contractPeriod`` field with appropriate values from ``awards`` or ``tender``
* ``contract_price``: populates the ``summary.contractValue`` field with the sum of all ``awards.value`` fields where the currency is the same
* ``cost_estimate``: populates the ``summary.tender.costEstimate`` field with the appropriate ``tender.value``
* ``contract_process_description``: populates the ``summary.description`` field from appropriate values in ``contracts``, ``awards`` or ``tender``
* ``contract_status``: populates the ``summary.status`` field using the ``contractingProcessStatus`` codelist.
* ``contract_title``: populates ``summary.title`` from the title field in ``awards``, ``contracts`` or ``tender``
* ``final_audit``: populate the ``documents`` field from ``contracts.implementation.documents`` according to the ``documentType``
* ``funding_sources``: updates ``parties`` with organizations having ``funder`` in their ``roles`` or from ``planning.budgetBreakdown.sourceParty``
* ``location``: populates the ``locations`` field with an array of location objects from ``planning.projects.locations``
* ``procurement_process``: populates the ``.summary.tender.procurementMethod`` and ``.summary.tender.procurementMethodDetails`` fields with their equivalents from ``tender``
* ``purpose``: populates the ``purpose`` field from ``planning.rationale``

Optional transforms
~~~~~~~~~~~~~~~~~~~

Some transforms are not run automatically, but only if set. The following transforms are included if they are listed in using the ``--transforms`` argument (as part of a comma-separated list) or if ``--all-transforms`` is passed.

* ``buyer_role``: updates the ``parties`` field with parties that have ``buyer`` in their ``roles``
* ``description_tender``: populate the ``description`` field from ``tender.description`` if no other is available
* ``location_from_items``: populate the ``locations`` field from ``deliveryLocation`` or ``deliveryAddress`` in ``tender.items`` if no other is available
* ``project_scope_summary``: updates ``summary.tender`` with ``items`` and ``milestones`` from ``tender``
* ``purpose_needs_assessment``: populate the ``documents`` field from ``planning.documents`` according to the ``documentType`` ``needsAssessment``
* ``title_from_tender``: populate the ``title`` field from ``tender.title`` if no other is available

Transformation Notes
~~~~~~~~~~~~~~~~~~~~

Most transforms follow the logic in the `mapping documentation <https://standard.open-contracting.org/infrastructure>`__.  However, there is some room for interpretation in some of the mappings, so here are some notes about these interpretations.

Differing text across multiple contracting process
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**planning/project/title, project/planning/description (planning and budget extension):**

If there are any contradictions i.e one contract says the title is different from another a warning is raised and the field is ignored in that case.  If all contracting processes agree (when the fields exists in them) then the value is still used.

**tender/title, tender/description, /planning/rationale:**

If there a multiple contradicting process then we concatenate the strings and put the ocid
in angle brackets like:

``<someocid> a tender description <anotherocid> another description``

If there is only one contracting processes then the ocid part is omitted.

Parties ID across multiple contracting processes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When ``parties/id`` from different contracting processes are conflicting and also if there are parties in multiple contracting processes that are the same, we need to identify which are in fact the same party.

The logic that the transforms do to work out matching parties:

* If all ``parties/id`` are unique across contracting processes then do nothing and add all parties to the project.
* If there are conflicting parties/id then look at the ``identifier`` field and if there are ``scheme`` and ``id`` make an id of ``somescheme-someid`` and use that in order to match parties across processes.  If there are different roles then add them to the same party.  Use the other fields from the first party found with this id.
* If there is no ``identifier`` then make up a new auto increment number and use that as the ``id``. **This means the original IDs get replaced and are lost in the mapping**
* If there is no ``identifier`` and all fields apart from ``roles`` and ``id`` are the same across parties then treat that as a single party and add the roles together and use a single generated ``id``.

Document ID across multiple contracting processes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If there are are only unique project/documents/id keep the ids the same. Otherwise create a new auto-increment for all docs.  **This means the original ``documents/id`` are lost**

Project Sector
^^^^^^^^^^^^^^

Sectors are gathered from ``planning/project/sector`` and it gets all unique ``scheme`` and ``id`` of the form ``<scheme>-<id>`` and adds them to the ``sector`` array. This could mean that the sectors generated are not in the `Project Sector Codelist <https://standard.open-contracting.org/infrastructure/latest/en/reference/codelists/#projectsector>`__.

Release Links
^^^^^^^^^^^^^

``contractingProcesses/releases`` within OC4IDS has link to a releases via a URL. This URL will be generated if OCDS release packages are supplied and a ``uri`` is in the package data. However, if this is not case the transform adds an additional field ``contractingProcesses/embeddedReleases`` which contains all releases supplied in their full.

Project Scope Summary
^^^^^^^^^^^^^^^^^^^^^

If ``--all-transforms`` is set or if ``project_scope_summary`` is included in ``--transforms`` it copies over all ``tender/items`` and ``tender/milestones`` to ``contractingProcess/tender``.  This is to give the output enough information in order to infer project scope.

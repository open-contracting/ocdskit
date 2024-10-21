OCDS Commands
=============

The inputs can be `concatenated JSON <https://en.wikipedia.org/wiki/JSON_streaming#Concatenated_JSON>`__ or JSON arrays.

Optional arguments for all commands are:

--encoding ENCODING     the file encoding
--ascii                 print escape sequences instead of UTF-8 characters
--pretty                pretty print output
--root-path ROOT_PATH   the path to the items to process within each input

.. error:: An error is raised if the JSON is malformed or if the ``--encoding`` is incorrect.

.. _handling-edge-cases:

Handling edge cases
-------------------

.. _large-packages:

Large packages
~~~~~~~~~~~~~~

If you are working with individual packages that are too large to hold in memory, use the :ref:`echo` command to reduce their size.

.. _embedded-data:

Embedded data
~~~~~~~~~~~~~

If you are working with files that embed OCDS data, use the ``--root-path ROOT_PATH`` option to indicate the "root" path to the items to process within each input.

For example, if release packages are in an array under a ``results`` key, like so:

.. code-block:: json

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

Then you can run ``ocdskit <command> --root-path results`` to process the release packages. The root path, in this case, is simply the ``results`` key. OCDS Kit will read all array entries at once into memory.

If the ``results`` array is very large, instead run ``ocdskit <command> --root-path results.item``. The root path, in this case, is the ``results`` key joined to the ``item`` literal by a period. The ``item`` literal indicates that the items to process are in an array. OCDS Kit will read one array entry at a time into memory.

For the next example, you can run ``ocdskit <command> --root-path results.item.ocdsReleasePackage``:

.. code-block:: json

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

.. _detect-format:

detect-format
-------------

.. seealso:: For the Python API, see :meth:`ocdskit.util.detect_format`

Reads OCDS files, and reports whether each is:

* a record package
* a release package
* a record
* a release
* a compiled release
* a versioned release
* a JSON array of one of the above
* `concatenated JSON <https://en.wikipedia.org/wiki/JSON_streaming#Concatenated_JSON>`__ of one of the above

Mandatory positional arguments:

* ``file`` OCDS files

.. code-block:: bash
   :caption: Example command

   ocdskit detect-format tests/fixtures/realdata/release-package-1.json tests/fixtures/realdata/record-package-1.json

.. _compile:

compile
-------

.. seealso:: For the Python API, see :meth:`ocdskit.combine.merge`

Reads release packages and individual releases from standard input, merges the releases by OCID, and prints the compiled releases.

Optional arguments:

--schema SCHEMA                       the URL or path of the release schema to use
--package                             wrap the compiled releases in a record package
--linked-releases                     if ``--package`` is set, use linked releases instead of full releases, if the input is a release package
--versioned                           if ``--package`` is set, include versioned releases in the record package; otherwise, print versioned releases instead of compiled releases
--uri URI                             if ``--package`` is set, set the record package's ``uri`` to this value
--published-date PUBLISHED_DATE       if ``--package`` is set, set the record package's ``publishedDate`` to this value
--version VERSION                     if ``--package`` is set, set the record package's ``version`` to this value
--publisher-name PUBLISHER_NAME       if ``--package`` is set, set the record package's ``publisher``'s ``name`` to this value
--publisher-uri PUBLISHER_URI         if ``--package`` is set, set the record package's ``publisher``'s ``uri`` to this value
--publisher-scheme PUBLISHER_SCHEME   if ``--package`` is set, set the record package's ``publisher``'s ``scheme`` to this value
--publisher-uid PUBLISHER_UID         if ``--package`` is set, set the record package's ``publisher``'s ``uid`` to this value
--fake                                if ``--package`` is set, set the record package's required metadata to dummy values

.. code-block:: bash
   :caption: Example command

   cat tests/fixtures/realdata/release-package-1.json | ocdskit compile > out.json

If ``--package`` is set, and if the ``--publisher-*`` options aren't used, the output package will have the same publisher as the last input package.

.. error:: An error is raised if a release is missing an ``ocid`` field, or if the values of the release packages' ``version`` fields are inconsistent.

.. _upgrade:

upgrade
-------

.. seealso:: For the Python API, see :mod:`ocdskit.upgrade`

Upgrades packages, releases and records from an old version of OCDS to a new version.

Any package, release or record that isn't in the old version is passed through. See the source of :meth:`ocdskit.util.get_ocds_minor_version` for determining the version.

.. attention::

   OCDS 1.0 `describes <https://standard.open-contracting.org/1.0/en/schema/reference/#identifier>`__ an organization's ``name``, ``identifier``, ``address`` and ``contactPoint`` as relevant to identifying it. OCDS 1.1 `moves <https://standard.open-contracting.org/1.1/en/schema/reference/#parties>`__ organization data into a ``parties`` array.

   Upgrading from OCDS 1.0 to 1.1 creates an ``id`` for each organization, based on those identifying fields. This can result in duplicates in the ``parties`` array, if the same organization has different or missing values for identifying fields in different contexts. This can also lead to data loss if the same organization has different values for non-identifying fields in different contexts. The command prints warnings about data loss, but not about potential duplicates.

.. attention:: OCDS 1.0 uses the `whole-list merge <https://standard.open-contracting.org/1.0/en/schema/merging/#merging-rules>`__ strategy on the ``suppliers`` array to prepare the compiled release and versioned release, whereas OCDS 1.1 uses the `identifier merge <https://standard.open-contracting.org/1.1/en/schema/merging/#identifier-merge>`__ strategy. This means that you should merge first, using the old version, and then upgrade to the new version.

.. attention:: Versioned releases within a record package are not upgraded.

Mandatory positional arguments:

* ``versions`` the colon-separated old and new versions

.. code-block:: bash
   :caption: Example command

   cat tests/fixtures/realdata/release-package-1.json | ocdskit upgrade 1.0:1.1 > out.json

If a release package or record package is too large, you can upgrade its individual releases or records using ``--root-path releases.item`` or ``--root-path records.item``, respectively.

.. error:: An error is raised if upgrading between the specified ``versions`` is not implemented.

.. _package-records:

package-records
---------------

.. seealso:: For the Python API, see :meth:`ocdskit.combine.package_records`

Reads records from standard input, and prints one record package.

Optional positional arguments:

* ``extension`` add this extension to the package

Optional arguments:

--size SIZE                           the maximum number of records per package
--uri URL                             set the record package's ``uri`` to this value
--published-date PUBLISHED_DATE       set the record package's ``publishedDate`` to this value
--version VERSION                     set the record package's ``version`` to this value
--publisher-name PUBLISHER_NAME       set the record package's ``publisher``'s ``name`` to this value
--publisher-uri PUBLISHER_URI         set the record package's ``publisher``'s ``uri`` to this value
--publisher-scheme PUBLISHER_SCHEME   set the record package's ``publisher``'s ``scheme`` to this value
--publisher-uid PUBLISHER_UID         set the record package's ``publisher``'s ``uid`` to this value
--fake                                set the record package's required metadata to dummy values

.. code-block:: bash
   :caption: Example command

   cat tests/fixtures/record_*.json | ocdskit package-records > out.json

If ``--uri`` and ``--published-date`` are not set, the output package will be invalid. Use ``--fake`` to set placeholder values.

.. _package-releases:

package-releases
----------------

.. seealso:: For the Python API, see :meth:`ocdskit.combine.package_releases`

Reads releases from standard input, and prints one release package.

Optional positional arguments:

* ``extension`` add this extension to the package

Optional arguments:

--size SIZE                           the maximum number of releases per package
--uri URL                             set the release package's ``uri`` to this value
--published-date PUBLISHED_DATE       set the release package's ``publishedDate`` to this value
--version VERSION                     set the release package's ``version`` to this value
--publisher-name PUBLISHER_NAME       set the release package's ``publisher``'s ``name`` to this value
--publisher-uri PUBLISHER_URI         set the release package's ``publisher``'s ``uri`` to this value
--publisher-scheme PUBLISHER_SCHEME   set the release package's ``publisher``'s ``scheme`` to this value
--publisher-uid PUBLISHER_UID         set the release package's ``publisher``'s ``uid`` to this value
--fake                                set the release package's required metadata to dummy values

.. code-block:: bash
   :caption: Example command

   cat tests/fixtures/release_*.json | ocdskit package-releases > out.json

If ``--uri`` and ``--published-date`` are not set, the output package will be invalid. Use ``--fake`` to set placeholder values.

To convert **record** packages to a **release** package, you can use the ``--root-path`` option:

.. code-block:: bash

   cat tests/fixtures/realdata/record-package* |
       ocdskit package-releases --root-path records.item.releases.item

.. _combine-record-packages:

combine-record-packages
-----------------------

.. seealso:: For the Python API, see :meth:`ocdskit.combine.combine_record_packages`

Reads record packages from standard input, collects packages and records, and prints one record package.

Optional arguments:

--uri URL                             set the record package's ``uri`` to this value
--published-date PUBLISHED_DATE       set the record package's ``publishedDate`` to this value
--version VERSION                     set the record package's ``version`` to this value
--publisher-name PUBLISHER_NAME       set the record package's ``publisher``'s ``name`` to this value
--publisher-uri PUBLISHER_URI         set the record package's ``publisher``'s ``uri`` to this value
--publisher-scheme PUBLISHER_SCHEME   set the record package's ``publisher``'s ``scheme`` to this value
--publisher-uid PUBLISHER_UID         set the record package's ``publisher``'s ``uid`` to this value
--fake                                set the record package's required metadata to dummy values

.. code-block:: bash
   :caption: Example command

   cat tests/fixtures/record-package_*.json | ocdskit combine-record-packages > out.json

If the ``--publisher-*`` options aren't used, the output package will have the same publisher as the last input package.

.. warning:: A warning is issued if a package's ``"records"`` field isn't set.

.. admonition:: Open issue

   If you need to create a single package that is too large to hold in your system's memory, please `comment on this issue <https://github.com/open-contracting/ocdskit/issues/119>`__.

.. _combine-release-packages:

combine-release-packages
------------------------

.. seealso:: For the Python API, see :meth:`ocdskit.combine.combine_release_packages`

Reads release packages from standard input, collects releases, and prints one release package.

Optional arguments:

--uri URL                             set the release package's ``uri`` to this value
--published-date PUBLISHED_DATE       set the release package's ``publishedDate`` to this value
--version VERSION                     set the release package's ``version`` to this value
--publisher-name PUBLISHER_NAME       set the release package's ``publisher``'s ``name`` to this value
--publisher-uri PUBLISHER_URI         set the release package's ``publisher``'s ``uri`` to this value
--publisher-scheme PUBLISHER_SCHEME   set the release package's ``publisher``'s ``scheme`` to this value
--publisher-uid PUBLISHER_UID         set the release package's ``publisher``'s ``uid`` to this value
--fake                                set the release package's required metadata to dummy values

.. code-block:: bash
   :caption: Example command

   cat tests/fixtures/release-package_*.json | ocdskit combine-release-packages > out.json

If the ``--publisher-*`` options aren't used, the output package will have the same publisher as the last input package.

.. warning:: A warning is issued if a package's ``"releases"`` field isn't set.

.. admonition:: Open issue

   If you need to create a single package that is too large to hold in your system's memory, please `comment on this issue <https://github.com/open-contracting/ocdskit/issues/119>`__.

.. _split-record-packages:

split-record-packages
---------------------

Reads record packages from standard input, and prints many record packages for each.

Mandatory positional arguments:

* ``size`` the number of records per package

.. code-block:: bash
   :caption: Example command

   cat tests/fixtures/realdata/record-package-1-2.json | ocdskit split-record-packages 2 |
       split -l 1 -a 4

The ``split`` command will write files named ``xaaaa``, ``xaaab``, ``xaaac``, etc., with one file per line of output. Don't combine the OCDS Kit ``--pretty`` option with the ``split`` command.

.. _split-release-packages:

split-release-packages
----------------------

Reads release packages from standard input, and prints many release packages for each.

Mandatory positional arguments:

* ``size`` the number of releases per package

.. code-block:: bash
   :caption: Example command

   cat tests/fixtures/realdata/release-package-1-2.json | ocdskit split-release-packages 2 |
       split -l 1 -a 4

The ``split`` command will write files named ``xaaaa``, ``xaaab``, ``xaaac``, etc., with one file per line of output. Don't combine the OCDS Kit ``--pretty`` option with the ``split`` command.

.. _echo:

echo
----

Repeats the input, applying ``--encoding``, ``--ascii``, ``--pretty`` and ``--root-path``, and using the UTF-8 encoding.

You can use this command to reformat data:

-  Use UTF-8 encoding:

   .. code-block:: bash

      cat iso-8859-1.json | ocdskit --encoding iso-8859-1 echo > utf-8.json

-  Use ASCII characters only:

   .. code-block:: bash

      cat unicode.json | ocdskit --ascii echo > ascii.json

-  Use UTF-8 characters, where possible:

   .. code-block:: bash

      cat ascii.json | ocdskit echo > unicode.json

-  Pretty print:

   .. code-block:: bash

      cat compact.json | ocdskit --pretty echo > pretty.json

-  Make compact:

   .. code-block:: bash

      cat pretty.json | ocdskit echo > compact.json

-  Extract compiled releases from a record package:

   .. code-block:: bash

      cat record-package.json | ocdskit echo --root-path records.item.compiledRelease

-  Extract records from record packages:

   .. code-block:: bash

      cat record-package.json | ocdskit echo --root-path records.item

-  Extract releases from release packages:

   .. code-block:: bash

      cat release-package.json | ocdskit echo --root-path releases.item

For the last two examples, if you intend to re-package the releases or records, and if the initial package is small enough to hold in memory, use the :ref:`split-release-packages` or :ref:`split-record-packages` command. If the initial package is too large to hold in memory, use the ``echo`` command in combination with the :ref:`package-releases` or :ref:`package-records` command. For example:

-  Split a large record package into smaller packages of 100 records each:

   .. code-block:: bash

      cat large-record-package.json | ocdskit echo --root-path records.item |
          ocdskit package-records --size 100

-  Split a large release package into smaller packages of 1,000 releases each:

   .. code-block:: bash

      cat large-release-package.json | ocdskit echo --root-path releases.item |
          ocdskit package-releases --size 1000

The package metadata from the large package won't be retained in the smaller packages. You can set this metadata using optional arguments of the :ref:`package-releases` or :ref:`package-records` command.

OC4IDS Commands
================

The following commands may be used when working with `Open Contracting for Infrastructure <https://standard.open-contracting.org/infrastructure>`__ data.

oc4ids-transforms
-----------------

This command takes a list of OCDS releases and transforms them into a single OC4IDS project.

`The logic for the mappings between OCDS and OC4IDS fields is documented here <https://standard.open-contracting.org/infrastructure/latest/en/cost/#mapping-to-ids-and-from-ocds>`__.

Optional arguments:

* ``--id ID`` the Project ID of the created project
* ``--package`` wrap the project in a package
* ``--options OPTIONS`` a comma seperated list of optional tranforms
* ``--all`` run all optional transforms

Arguments that can be applied if the project is in a package:

* ``--uri URI`` if ``--package`` is set, set the record package's ``uri`` to this value
* ``--published-date PUBLISHED_DATE`` if ``--package`` is set, set the record package's ``publishedDate`` to this value
* ``--publisher-name PUBLISHER_NAME`` if ``--package`` is set, set the record package's ``publisher``'s ``name`` to this value
* ``--publisher-uri PUBLISHER_URI`` if ``--package`` is set, set the record package's ``publisher``'s ``uri`` to this value
* ``--publisher-scheme PUBLISHER_SCHEME`` if ``--package`` is set, set the record package's ``publisher``'s ``scheme`` to this value
* ``--publisher-uid PUBLISHER_UID`` if ``--package`` is set, set the record package's ``publisher``'s ``uid`` to this value
* ``--fake`` if ``--package`` is set, set the record package's required metadata to dummy values

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

Some transforms are not run automatically, but only if set. The following transforms are included if they are listed in using the ``--options`` argument (as part of a comma-separated list) or if ``--all`` is passed.

* ``buyer_role``: updates the ``parties`` field with parties that have ``buyer`` in their ``roles``
* ``description_tender``: populate the ``description`` field from ``tender.description`` if no other is available
* ``location_from_items``: populate the ``locations`` field from ``deliveryLocation`` or ``deliveryAddress`` in ``tender.items`` if no other is available
* ``project_scope_summary``: updates ``summary.tender`` with ``items`` and ``milestones`` from ``tender``
* ``purpose_needs_assessment``: populate the ``documents`` field from ``planning.documents`` according to the ``documentType`` ``needsAssessment``
* ``title_from_tender``: populate the ``title`` field from ``tender.title`` if no other is available

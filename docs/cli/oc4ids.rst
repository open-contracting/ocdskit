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

Transformation Notes
~~~~~~~~~~~~~~~~~~~~

Most transforms follow the logic in the `mapping documentation <https://standard.open-contracting.org/infrastructure>`__.  However, there is some room for interpretation in some of the mappings, so here are some notes about these interpretations.

Differing text across multiple contracting process
##################################################

**planning/project/title, project/planning/description (planning and budget extension):**

If there are any contradictions i.e one contract says the title is different from another a warning is raised and the field is ignored in that case.  If all contracting processes agree (when the fields exists in them) then the value is still used.

**tender/title, tender/description, /planning/rationale:**

If there a multiple contradicting process then we concatenate the strings and put the ocid
in angle brackets like:

``<someocid> a tender description <anotherocid> another description``

If there is only one contracting processes then the ocid part is omitted.


Parties ID across multiple contracting processes
################################################

When ``parties/id`` from different contracting processes are conflicting and also if there are parties in multiple contracting processes that are the same, we need to identify which are in fact the same party.

The logic that the transforms do to work out matching parties:

* If all ``parties/id`` are unique across contracting processes then do nothing and add all parties to the project.
* If there are conflicting parties/id then look at the ``identifier`` field and if there are ``scheme`` and ``id`` make an id of ``somescheme-someid`` and use that in order to match parties across processes.  If there are different roles then add them to the same party.  Use the other fields from the first party found with this id.
* If there is no ``identifier`` then make up a new auto increment number and use that as the ``id``. **This means the original IDs get replaced and are lost in the mapping**
* If there is no ``identifier`` and all fields apart from ``roles`` and ``id`` are the same across parties then treat that as a single party and add the roles together and use a single generated `id`.

Document ID across multiple contracting processes
#################################################

If there are are only unique project/documents/id keep the ids the same. Otherwise create a new auto-increment for all docs.  **This means the original ``documanets/id`` are lost**


Project Sector
##############

Sectors are gathered from ``planning/project/sector`` and it gets all unique ``scheme`` and ``id`` of the form ``<scheme>-<id>`` and adds them to the ``sector`` array. This could mean that the sectors generated are not in the `Project Sector Codelist <https://standard.open-contracting.org/infrastructure/latest/en/reference/codelists/#projectsector>`__.


Release Links
#############

``contractingProcesses/releases`` within OC4IDS has link to a releases via a URL. This URL will be generated if OCDS release packages are supplied and a `uri` is in the package data. However, if this is not case the transform adds an additional field ``contractingProcesses/embeddedReleases`` which contains all releases supplied in their full.


Project Scope Summary
#####################

When the project_scope_summary transform is selected in config then copy over all ``tender/items`` and ``tender/milestones`` to ``contractingProcess/tender``.  This is to give the output enough information in order to infer project scope.





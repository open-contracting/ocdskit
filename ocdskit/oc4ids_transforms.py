import copy
import logging
from collections import OrderedDict
import datetime
from ocdsmerge.util import sorted_releases

import jsonpointer

from ocdskit.combine import merge

logger = logging.getLogger("ocdskit")


def run_transforms(config, releases, project_id=None, records=None, output=None):

    """
    Transforms a list of OCDS releases into a OC4IDS project.

    :param dict config: contains optional tranform options.
    :param list releases: list of OCDS releases
    :param string project_id: project ID of resulting project
    :param list records: pre computed list of records
    :param dict output: initial project output template project where transformed data will be added
    """
    transforms_to_run = []

    for transform in TRANSFORM_LIST:
        transform_name = transform.__name__
        if not config.get(transform_name) and transform_name in OPTIONAL_TRANSFORMS:
            continue
        transforms_to_run.append(transform)

    return _run_transforms(releases, project_id, records, output, transforms_to_run)


def _run_transforms(releases, project_id=None, records=None, output=None, transforms=None):

    state = InitialTransformState(releases, project_id, records, output)
    if not transforms:
        transforms = TRANSFORM_LIST

    for transform in transforms:
        transform(state)

    return state.output


class InitialTransformState:
    def __init__(self, releases, project_id=None, records=None, output=None):
        self.releases = sorted_releases(releases)

        self.project_id = project_id
        records = records

        if not records:
            records = next(merge(self.releases, return_package=True, use_linked_releases=True)).get("records", [])

        compiled_releases = []
        for record in records:
            compiled_release = record.get("compiledRelease", {})
            # projects only have linked releases 'uri' is a good proxy for that.
            linked_releases = [release for release in record.get("releases", []) if release.get("url")]
            embedded_releases = [release for release in record.get("releases", []) if not release.get("url")]

            compiled_release["releases"] = linked_releases
            compiled_release["embeddedReleases"] = embedded_releases

            compiled_releases.append(compiled_release)

        self.compiled_releases = compiled_releases
        self.output = output or {}
        if project_id and "id" not in self.output:
            self.output["id"] = project_id


def copy_party_by_role(state, role, new_roles=None):

    success = False

    for compiled_release in state.compiled_releases:
        parties = compiled_release.get("parties", [])
        if not isinstance(parties, list):
            continue
        for party in compiled_release.get("parties", []):
            if role in party.get("roles", []):
                output_parties = state.output.get("parties", [])
                if not output_parties:
                    state.output["parties"] = output_parties
                output_party = copy.deepcopy(party)
                if new_roles:
                    output_roles = output_party.get("roles", [])
                    output_roles.extend(new_roles)
                    output_party["roles"] = output_roles
                output_parties.append(output_party)
                success = True

    return success

def copy_document_by_type(state, document_type):

    success = False

    if not state.output.get("documents"):
        state.output["documents"] = []

    for compiled_release in state.compiled_releases:
        documents = jsonpointer.resolve_pointer(compiled_release, "/planning/documents", [])
        for document in documents:
            if document_type in document.get("documentType", []):
                state.output["documents"].append(document)
                success = True
    return success

def concat_ocid_and_string(state, path_to_string):

    strings = ""
    for compiled_release in state.compiled_releases:

        ocid = jsonpointer.resolve_pointer(compiled_release, "/ocid")
        a_string = jsonpointer.resolve_pointer(compiled_release, path_to_string, None)

        concat = "<{}> {}\n".format(ocid, a_string)
        strings = strings + concat

    return strings


def public_authority_role(state):
    return copy_party_by_role(state, "publicAuthority")


def buyer_role(state):
    return copy_party_by_role(state, "buyer", ["publicAuthority"])


def sector(state):
    success = False
    for compiled_release in state.compiled_releases:
        sector = jsonpointer.resolve_pointer(compiled_release, "/planning/project/sector", None)
        if sector:
            state.output["sector"] = sector
            success = True
            break
    return success


def additional_classifications(state):
    success = False
    for compiled_release in state.compiled_releases:
        additionalClassifications = jsonpointer.resolve_pointer(
            compiled_release, "/planning/project/additionalClassifications", None
        )
        if additionalClassifications:
            state.output["additionalClassifications"] = additionalClassifications
            success = True
            break
    return success


def title(state):
    success = False
    for compiled_release in state.compiled_releases:
        title = jsonpointer.resolve_pointer(compiled_release, "/planning/project/title", None)
        if title:
            state.output["title"] = title
            success = True
            break
    return success


def title_from_tender(state):
    if state.output.get("title"):
        return True

    success = False
    for compiled_release in state.compiled_releases:
        title = jsonpointer.resolve_pointer(compiled_release, "/tender/title", None)
        if title:
            state.output["title"] = title
            success = True
            break
    return success


def contracting_process_setup(state):
    """ This will initailly create the contracting process objects and the summary object
    within.  All transforms that use contracting processes need to run this tranform first."""

    state.output["contractingProcesses"] = []

    for compiled_release in state.compiled_releases:
        contracting_process = {}
        contracting_process["id"] = compiled_release.get("ocid")
        contracting_process["summary"] = {}
        contracting_process["summary"]["ocid"] = compiled_release.get("ocid")

        releases = compiled_release.get("releases")
        if releases:
            contracting_process["releases"] = releases

        embedded_releases = compiled_release.get("embeddedReleases")
        if embedded_releases:
            contracting_process["embeddedReleases"] = embedded_releases

        state.output["contractingProcesses"].append(contracting_process)

    return True


def procuring_entity(state):
    success = copy_party_by_role(state, "procuringEntity")

    for compiled_release, contracting_process in zip(state.compiled_releases, state.output["contractingProcesses"]):
        procuring_entity = jsonpointer.resolve_pointer(compiled_release, "/tender/procuringEntity", None)
        if procuring_entity:
            tender = contracting_process["summary"].get("tender", {})
            tender["procuringEntity"] = procuring_entity
            contracting_process["summary"]["tender"] = tender

    return success


def administrative_entity(state):
    success = copy_party_by_role(state, "administrativeEntity")

    for compiled_release, contracting_process in zip(state.compiled_releases, state.output["contractingProcesses"]):
        administrative_entities = []
        for party in compiled_release.get("parties", []):
            if "administrativeEntity" in party.get("roles", []):
                administrative_entities.append(party)
        if len(administrative_entities) > 1:
            logger.warning(
                "More than one administrativeEntity in contractingProcesses with ocid {} skipping tranform".format(
                    compiled_release.get("ocid")
                )
            )
            continue
        if administrative_entities:
            tender = contracting_process["summary"].get("tender", {})
            administrative_entity = {}
            administrative_entity["id"] = administrative_entities[0].get("id")
            administrative_entity["name"] = administrative_entities[0].get("name")
            tender["administrativeEntity"] = administrative_entity
            contracting_process["summary"]["tender"] = tender

    return success


def contract_status(state):

    current_iso_datetime = datetime.datetime.now().isoformat()

    for compiled_release, contracting_process in zip(state.compiled_releases, state.output["contractingProcesses"]):
        tender = compiled_release.get("tender", {})
        tender_status = tender.get("status")
        closed_tender = tender_status in ("cancelled", "unsuccessful", "withdrawn")
        contracts = compiled_release.get("contracts", [])
        awards = compiled_release.get("awards", [])

        contract_periods = []
        if tender:
            contract_periods.append(tender.get("contractPeriod", {}))
        for contract in contracts:
            contract_periods.append(contract.get("period", {}))
        for award in awards:
            contract_periods.append(award.get("contractPeriod", {}))

        # pre-award
        if tender and not closed_tender:
            if not compiled_release.get("awards") and not compiled_release.get("contracts"):
                contracting_process["summary"]["status"] = "pre-award"
                continue

            all_contracts_pending = all((contract.get("status") == "pending") for contract in contracts)
            all_awards_pending = all(award.get("status") == "pending" for award in awards)

            if all_contracts_pending and all_awards_pending:
                contracting_process["summary"]["status"] = "pre-award"
                continue

            all_awards_in_future = all(award.get("date", "") > current_iso_datetime for award in awards)

            award_period_in_future = tender.get("awardPeriod", {}).get("startDate", "") > current_iso_datetime

            if all_awards_in_future and award_period_in_future:
                contracting_process["summary"]["status"] = "pre-award"
                continue

        # active

        if any(contract.get("status") == "active" for contract in contracts):
            contracting_process["summary"]["status"] = "active"
            continue

        if any(
            period.get("startDate", "") < current_iso_datetime < period.get("endDate", "9999-12-31")
            for period in contract_periods
            if period
        ):
            contracting_process["summary"]["status"] = "active"
            continue

        # closed

        if closed_tender:
            contracting_process["summary"]["status"] = "closed"
            continue

        if awards:
            if all(award.get("status") in ("cancelled", "withdrawn") for award in awards):
                contracting_process["summary"]["status"] = "closed"
                continue

        if contracts:
            if all(contract.get("status") in ("cancelled", "terminated") for contract in contracts):
                contracting_process["summary"]["status"] = "closed"
                continue

        if all(current_iso_datetime > period.get("endDate", "9999-12-31") for period in contract_periods):
            contracting_process["summary"]["status"] = "closed"
            continue


def procurement_process(state):
    for compiled_release, contracting_process in zip(state.compiled_releases, state.output["contractingProcesses"]):
        input_tender = compiled_release.get("tender", {})
        if input_tender:
            procurement_method = input_tender.get("procurementMethod")
            if procurement_method:
                tender = contracting_process["summary"].get("tender", {})
                tender["procurementMethod"] = procurement_method
                contracting_process["summary"]["tender"] = tender

            procurement_method_details = input_tender.get("procurementMethodDetails")
            if procurement_method_details:
                tender = contracting_process["summary"].get("tender", {})
                tender["procurementMethodDetails"] = procurement_method_details
                contracting_process["summary"]["tender"] = tender


def number_of_tenderers(state):
    for compiled_release, contracting_process in zip(state.compiled_releases, state.output["contractingProcesses"]):
        input_tender = compiled_release.get("tender", {})
        if input_tender:
            number_of_tenderers = input_tender.get("numberOfTenderers")
            if number_of_tenderers:
                tender = contracting_process["summary"].get("tender", {})
                tender["numberOfTenderers"] = number_of_tenderers
                contracting_process["summary"]["tender"] = tender


def location(state):
    success = False
    for compiled_release in state.compiled_releases:
        locations = jsonpointer.resolve_pointer(compiled_release, "/planning/project/locations", None)
        if locations:
            state.output["locations"] = locations
            success = True
            break
    return success


def location_from_items(state):
    if state.output.get("locations"):
        return True

    success = False

    locations = []
    for compiled_release in state.compiled_releases:

        items = jsonpointer.resolve_pointer(compiled_release, "/tender/items", None)
        for item in items:

            delivery_location = jsonpointer.resolve_pointer(item, "/deliveryLocation", None)
            if delivery_location:
                locations.append(delivery_location)

            delivery_address = jsonpointer.resolve_pointer(item, "/deliveryAddress", None)
            if delivery_address:
                locations.append({"address": delivery_address})

        if len(locations) > 0:
            state.output["locations"] = locations
            success = True
            break

    return success


def budget(state):

    success = False

    if len(state.compiled_releases) == 1:
        budget_value = jsonpointer.resolve_pointer(state.compiled_releases[0], "/planning/budget/amount", None)
        if budget_value:
            state.output["budget"] = {"amount": budget_value}
            success = True
    else:
        budget_currencies = set()
        budget_amounts = []

        for compiled_release in state.compiled_releases:
            budget_amounts.append(
                float(jsonpointer.resolve_pointer(compiled_release, "/planning/budget/amount/amount", None))
            )
            budget_currencies.add(
                jsonpointer.resolve_pointer(compiled_release, "/planning/budget/amount/currency", None)
            )

        if len(budget_currencies) > 1:
            logger.warning("Can't get budget total, {} different currencies found.".format(len(budget_currencies)))
        else:
            state.output["budget"] = {
                "amount": {"amount": sum(budget_amounts), "currency": next(iter(budget_currencies))}
            }
            success = True
    return success


def budget_approval(state):
    return copy_document_by_type(state, "budgetApproval")


def environmental_impact(state):
    return copy_document_by_type(state, "environmentalImpact")


def land_and_settlement_impact(state):
    return copy_document_by_type(state, "landAndSettlementImpact")


def purpose(state):
    if len(state.compiled_releases) == 1:
        rationale = jsonpointer.resolve_pointer(state.compiled_releases[0], "/planning/rationale", None)
        if rationale:
            state.output["purpose"] = rationale
            return True

    else:
        purposes = concat_ocid_and_string(state, "/planning/rationale")
        if purposes is not "":
            state.output["purpose"] = purposes
            return True

    return False


def purpose_needs_assessment(state):
    return copy_document_by_type(state, "needsAssessment")


def description(state):

    if len(state.compiled_releases) == 1:
        description = jsonpointer.resolve_pointer(state.compiled_releases[0], "/planning/project/description", None)
        if description:
            state.output["description"] = description
            return True

    else:
        descriptions = concat_ocid_and_string(state, "/planning/project/description")
        if descriptions is not "":
            state.output["description"] = descriptions
            return True
    return False


def description_tender(state):
    if state.output.get("description"):
        return True

    if len(state.compiled_releases) == 1:
        description = jsonpointer.resolve_pointer(state.compiled_releases[0], "/tender/description", None)
        if description:
            state.output["description"] = description
            return True

    else:
        descriptions = concat_ocid_and_string(state, "/tender/description")
        if descriptions is not "":
            state.output["description"] = descriptions
            return True

    return False


def funding_sources(state):
    success = False

    if not state.output.get("parties"):
        state.output["parties"] = []

    for compiled_release in state.compiled_releases:

        parties = jsonpointer.resolve_pointer(compiled_release, "/parties", None)

        # Get parties from budgetBreakdown.sourceParty
        breakdowns = jsonpointer.resolve_pointer(compiled_release, "/planning/budget/budgetBreakdown", None)
        if breakdowns:
            for breakdown in breakdowns:
                source_party = jsonpointer.resolve_pointer(breakdown, "/sourceParty", None)
                party_id = source_party.get("id")
                # Look up party data by id in parties
                if parties and party_id:
                    for party in parties:
                        if party.get("id") == party_id:
                            # Add to parties and set funder in roles
                            if party.get("roles"):
                                party["roles"].append("funder")
                            else:
                                party["roles"] = ["funder"]
                            state.output["parties"].append(party)
                            success = True

        # If no parties from the budget breakdown, copy from top level with 'funder' roles
        if len(state.output["parties"]) == 0:
            copy_party_by_role(state, "funder")
            success = True
    return success


TRANSFORM_LIST = [
    contracting_process_setup,
    public_authority_role,
    buyer_role,
    sector,
    additional_classifications,
    title,
    title_from_tender,
    procuring_entity,
    administrative_entity,
    contract_status,
    procurement_process,
    location,
    location_from_items,
    budget,
    budget_approval,
    purpose,
    purpose_needs_assessment,
    description,
    description_tender,
    environmental_impact,
    land_and_settlement_impact,
    funding_sources,
]

OPTIONAL_TRANSFORMS = [
    'buyer_role',
    'title_from_tender',
    'location_from_items',
    'purpose_needs_assessment',
    'description_tender',
]

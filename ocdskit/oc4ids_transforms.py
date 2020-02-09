import copy
import datetime
import json
import logging
from collections import defaultdict

from jsonpointer import resolve_pointer
from ocdsmerge.util import sorted_releases

from ocdskit.combine import merge

logger = logging.getLogger("ocdskit")


def check_type(item, item_type):
    """ Check type and if incorrect return empty version of type so that future processing works with bad data"""
    if not isinstance(item, item_type):
        if item:
            logger.warn("item {} is not of type {} so skipping".format(item, item_type.__name__))
        return item_type()
    return item


def cast(item, item_type):
    """ Cast to type and if casting fails return empty version of type """
    try:
        return item_type(item)
    except ValueError:
        return item_type()


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
        if not config.get("all") and not config.get(transform_name) and transform_name in OPTIONAL_TRANSFORMS:
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
        self.releases_by_ocid = defaultdict(list)
        for release in self.releases:
            ocid = check_type(release.get("ocid"), str)
            if ocid:
                self.releases_by_ocid[ocid].append(release)

        self.project_id = project_id
        records = records

        if not records:
            record_package = next(merge(self.releases, return_package=True, use_linked_releases=True))
            records = check_type(record_package.get("records"), list)

        compiled_releases = []
        for record in records:
            compiled_release = check_type(record.get("compiledRelease"), dict)
            # projects only have linked releases 'uri' is a good proxy for that.
            record_releases = check_type(record.get("releases"), list)
            linked_releases = [release for release in record_releases if release.get("url")]
            embedded_releases = [release for release in record_releases if not release.get("url")]

            compiled_release["releases"] = linked_releases
            compiled_release["embeddedReleases"] = embedded_releases

            compiled_releases.append(compiled_release)

        self.compiled_releases = compiled_releases
        self.output = output or {}
        if project_id and "id" not in self.output:
            self.output["id"] = project_id

        self.party_analysis()

    def party_analysis(self):

        all_parties = []
        party_ids = set()
        duplicate_party_ids = False

        for compiled_release in self.compiled_releases:
            parties = check_type(compiled_release.get("parties"), list)
            for party in parties:
                full_party_copy = copy.deepcopy(party)
                partial_party_copy = copy.deepcopy(party)
                partial_party_copy.pop("id", None)
                partial_party_copy.pop("roles", None)

                # A guess at the identity of the party. i.e id and roles missing
                party_fingerprint = json.dumps(partial_party_copy, sort_keys=True)

                unique_identifier = None
                identifier = check_type(party.get("identifier"), dict)
                id_ = check_type(identifier.get("id"), str)
                scheme = check_type(identifier.get("scheme"), str)
                if identifier and scheme:
                    unique_identifier = scheme + "-" + id_

                all_parties.append(
                    {
                        "party": full_party_copy,
                        "original_party": party,
                        "party_fingerprint": party_fingerprint,
                        "unique_identifier": unique_identifier,
                    }
                )
                party_id = party.get("id")
                if party_id in party_ids:
                    duplicate_party_ids = True
                party_ids.add(party_id)

        party_num = 1
        unique_parties = []

        for party in all_parties:
            found_party = None
            for unique_party in unique_parties:
                if party["unique_identifier"] and party["unique_identifier"] == unique_party["unique_identifier"]:
                    found_party = unique_party
                    break
                if party["party_fingerprint"] == unique_party["party_fingerprint"]:
                    found_party = unique_party
                    break
            if found_party:
                new_roles = set(
                    check_type(found_party["party"].get("roles"), list) + check_type(party["party"].get("roles"), list)
                )
                found_party["party"]["roles"] = list(new_roles)
            else:
                if duplicate_party_ids:
                    if party["unique_identifier"]:
                        party["party"]["id"] = party["unique_identifier"]
                    else:
                        party["party"]["id"] = str(party_num)
                        party_num += 1
                unique_parties.append(party)
            party["original_party"]["_new_id"] = party["party"]["id"]

        self.parties = [party["party"] for party in unique_parties]


def copy_party_by_role(state, role, new_roles=None):

    for party in state.parties:
        if role in check_type(party.get("roles"), list):
            output_parties = state.output.get("parties", [])
            if not output_parties:
                state.output["parties"] = output_parties
            output_party = copy.deepcopy(party)
            if new_roles:
                output_roles = output_party.get("roles", [])
                output_roles.extend(new_roles)
                output_party["roles"] = output_roles
            output_parties.append(output_party)


def copy_document_by_type(state, document_type):

    success = False

    if not state.output.get("documents"):
        state.output["documents"] = []

    for compiled_release in state.compiled_releases:
        documents = resolve_pointer(compiled_release, "/planning/documents", [])
        for document in check_type(documents, list):
            document = check_type(document, dict)
            if document_type == document.get("documentType"):
                state.output["documents"].append(document)
                success = True
    return success


def concat_ocid_and_string(state, path_to_string):

    strings = ""
    for compiled_release in state.compiled_releases:

        ocid = check_type(resolve_pointer(compiled_release, "/ocid", None), str)
        a_string = check_type(resolve_pointer(compiled_release, path_to_string, None), str)

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
        sector = resolve_pointer(compiled_release, "/planning/project/sector", None)
        if sector:
            state.output["sector"] = sector
            success = True
            break
    return success


def additional_classifications(state):
    success = False
    for compiled_release in state.compiled_releases:
        additionalClassifications = resolve_pointer(
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
        title = resolve_pointer(compiled_release, "/planning/project/title", None)
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
        title = resolve_pointer(compiled_release, "/tender/title", None)
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
        procuring_entities = []
        for party in check_type(compiled_release.get("parties"), list):
            if "procuringEntity" in check_type(party.get("roles"), list):
                procuring_entities.append(party)
        if len(procuring_entities) > 1:
            logger.warning(
                "More than one procuringEntity in contractingProcesses with ocid {} skipping tranform".format(
                    compiled_release.get("ocid")
                )
            )
            continue
        if procuring_entities:
            tender = check_type(contracting_process["summary"].get("tender"), dict)
            procuring_entity = {}
            procuring_entity["id"] = procuring_entities[0].get("_new_id")
            name = procuring_entities[0].get("name")
            if name:
                procuring_entity["name"] = name
            tender["procuringEntity"] = procuring_entity
            contracting_process["summary"]["tender"] = tender

    return success


def administrative_entity(state):
    success = copy_party_by_role(state, "administrativeEntity")

    for compiled_release, contracting_process in zip(state.compiled_releases, state.output["contractingProcesses"]):
        administrative_entities = []
        for party in check_type(compiled_release.get("parties"), list):
            if "administrativeEntity" in check_type(party.get("roles"), list):
                administrative_entities.append(party)
        if len(administrative_entities) > 1:
            logger.warning(
                "More than one administrativeEntity in contractingProcesses with ocid {} skipping tranform".format(
                    compiled_release.get("ocid")
                )
            )
            continue
        if administrative_entities:
            tender = check_type(contracting_process["summary"].get("tender"), dict)
            administrative_entity = {}
            administrative_entity["id"] = administrative_entities[0].get("_new_id")
            administrative_entity["name"] = administrative_entities[0].get("name")
            tender["administrativeEntity"] = administrative_entity
            contracting_process["summary"]["tender"] = tender

    return success


def contract_status(state):

    current_iso_datetime = datetime.datetime.now().isoformat()

    for compiled_release, contracting_process in zip(state.compiled_releases, state.output["contractingProcesses"]):
        tender = check_type(compiled_release.get("tender"), dict)
        tender_status = tender.get("status")
        closed_tender = tender_status in ("cancelled", "unsuccessful", "withdrawn")
        contracts = check_type(compiled_release.get("contracts"), list)
        awards = check_type(compiled_release.get("awards"), list)

        contract_periods = []
        if tender:
            contract_periods.append(check_type(tender.get("contractPeriod"), dict))
        for contract in contracts:
            contract_periods.append(check_type(contract.get("period"), dict))
        for award in awards:
            contract_periods.append(check_type(award.get("contractPeriod"), dict))

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

            all_awards_in_future = all(check_type(award.get("date"), str) > current_iso_datetime for award in awards)

            award_period_start_date = check_type(resolve_pointer(tender, "/awardPeriod/startDate", ""), str)
            award_period_in_future = award_period_start_date > current_iso_datetime

            if all_awards_in_future and award_period_in_future:
                contracting_process["summary"]["status"] = "pre-award"
                continue

        # active

        if any(contract.get("status") == "active" for contract in contracts):
            contracting_process["summary"]["status"] = "active"
            continue

        if any(
            (check_type(period.get("startDate"), str) < current_iso_datetime)
            and (current_iso_datetime < check_type(period.get("endDate", "9999-12-31"), str))
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
            if all(check_type(award, dict).get("status") in ("cancelled", "withdrawn") for award in awards):
                contracting_process["summary"]["status"] = "closed"
                continue

        if contracts:
            if all(check_type(contract, dict).get("status") in ("cancelled", "terminated") for contract in contracts):
                contracting_process["summary"]["status"] = "closed"
                continue

        if all(
            current_iso_datetime > check_type(period.get("endDate", "9999-12-31"), str) for period in contract_periods
        ):
            contracting_process["summary"]["status"] = "closed"
            continue


def procurement_process(state):
    for compiled_release, contracting_process in zip(state.compiled_releases, state.output["contractingProcesses"]):
        input_tender = check_type(compiled_release.get("tender"), dict)
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
        input_tender = check_type(compiled_release.get("tender"), dict)
        if input_tender:
            number_of_tenderers = input_tender.get("numberOfTenderers")
            if number_of_tenderers:
                tender = contracting_process["summary"].get("tender", {})
                tender["numberOfTenderers"] = number_of_tenderers
                contracting_process["summary"]["tender"] = tender


def location(state):
    success = False
    all_locations = []
    for compiled_release in state.compiled_releases:
        locations = resolve_pointer(compiled_release, "/planning/project/locations", None)
        if locations:
            all_locations.extend(locations)
            success = True

    if all_locations:
        state.output["locations"] = all_locations

    return success


def location_from_items(state):
    if state.output.get("locations"):
        return True

    success = False

    locations = []
    for compiled_release in state.compiled_releases:

        items = resolve_pointer(compiled_release, "/tender/items", [])
        for item in check_type(items, list):

            delivery_location = resolve_pointer(item, "/deliveryLocation", None)
            if delivery_location:
                locations.append(delivery_location)

            delivery_address = resolve_pointer(item, "/deliveryAddress", None)
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
        budget_value = resolve_pointer(state.compiled_releases[0], "/planning/budget/amount", None)
        if budget_value:
            state.output["budget"] = {"amount": budget_value}
            success = True
    else:
        budget_currencies = set()
        budget_amounts = []

        for compiled_release in state.compiled_releases:
            budget_amounts.append(
                cast(resolve_pointer(compiled_release, "/planning/budget/amount/amount", None), float)
            )
            budget_currencies.add(resolve_pointer(compiled_release, "/planning/budget/amount/currency", None))

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
        rationale = resolve_pointer(state.compiled_releases[0], "/planning/rationale", None)
        if rationale:
            state.output["purpose"] = rationale
            return True

    else:
        purposes = concat_ocid_and_string(state, "/planning/rationale")
        if purposes != "":
            state.output["purpose"] = purposes
            return True

    return False


def purpose_needs_assessment(state):
    return copy_document_by_type(state, "needsAssessment")


def description(state):

    if len(state.compiled_releases) == 1:
        description = resolve_pointer(state.compiled_releases[0], "/planning/project/description", None)
        if description:
            state.output["description"] = description
            return True

    else:
        descriptions = concat_ocid_and_string(state, "/planning/project/description")
        if descriptions != "":
            state.output["description"] = descriptions
            return True
    return False


def description_tender(state):
    if state.output.get("description"):
        return True

    if len(state.compiled_releases) == 1:
        description = resolve_pointer(state.compiled_releases[0], "/tender/description", None)
        if description:
            state.output["description"] = description
            return True

    else:
        descriptions = concat_ocid_and_string(state, "/tender/description")
        if descriptions != "":
            state.output["description"] = descriptions
            return True

    return False


def funding_sources(state):
    success = False

    if not state.output.get("parties"):
        state.output["parties"] = []

    for compiled_release in state.compiled_releases:

        parties = check_type(resolve_pointer(compiled_release, "/parties", None), list)

        # Get parties from budgetBreakdown.sourceParty
        breakdowns = check_type(resolve_pointer(compiled_release, "/planning/budget/budgetBreakdown", None), list)
        if breakdowns:
            for breakdown in breakdowns:
                source_party = check_type(resolve_pointer(breakdown, "/sourceParty", None), dict)
                party_id = source_party.get("id")
                # Look up party data by id in parties
                if parties and party_id:
                    for party in parties:
                        party = check_type(party, dict)
                        if party.get("id") == party_id:
                            # Add to parties and set funder in roles
                            if check_type(party.get("roles"), list):
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


def cost_estimate(state):

    for contracting_process in state.output["contractingProcesses"]:
        ocid = contracting_process.get("id")
        latest_planning_value = None
        for release in state.releases_by_ocid.get(ocid, []):
            tender_status = resolve_pointer(release, "/tender/status", None)
            tender_value = resolve_pointer(release, "/tender/value", None)
            if tender_status == "planning" and tender_value:
                latest_planning_value = tender_value

        if latest_planning_value:
            tender = contracting_process["summary"].get("tender", {})
            tender["costEstimate"] = latest_planning_value
            contracting_process["summary"]["tender"] = tender


def contract_title(state):
    for compiled_release, contracting_process in zip(state.compiled_releases, state.output["contractingProcesses"]):
        contract_titles = []
        for contract in check_type(compiled_release.get("contracts"), list):
            contract = check_type(contract, dict)
            contract_title = contract.get("title")
            contract_titles.append(contract_title)

        if len(contract_titles) == 1:
            contracting_process["summary"]["title"] = contract_titles[0]
            continue

        award_titles = []
        for award in check_type(compiled_release.get("awards", []), list):
            award = check_type(award, dict)
            award_title = award.get("title")
            award_titles.append(award_title)

        if len(award_titles) == 1:
            contracting_process["summary"]["title"] = award_titles[0]
            continue

        tender_title = resolve_pointer(compiled_release, "/tender/title", None)

        if tender_title:
            contracting_process["summary"]["title"] = tender_title


def suppliers(state):
    copy_party_by_role(state, "supplier")

    for compiled_release, contracting_process in zip(state.compiled_releases, state.output["contractingProcesses"]):
        parties = check_type(compiled_release.get("parties"), list)
        suppliers = []
        for party in parties:
            if "supplier" in check_type(party.get("roles"), list):
                suppliers.append({"id": party.get("id"), "name": party.get("name")})

        if suppliers:
            contracting_process["summary"]["suppliers"] = suppliers


def contract_price(state):
    for compiled_release, contracting_process in zip(state.compiled_releases, state.output["contractingProcesses"]):
        awards = check_type(compiled_release.get("awards"), list)
        award_currency = None
        award_amount = 0
        for award in awards:
            award = check_type(award, dict)
            amount = cast(resolve_pointer(award, "/value/amount", None), float)
            award_amount += amount

            currency = check_type(resolve_pointer(award, "/value/currency", None), str)
            if currency:
                if award_currency is None:
                    award_currency = currency
                else:
                    if currency != award_currency:
                        logger.warning("Multiple currencies not supported {}, {}".format(award_currency, currency))
                        award_amount = 0
                        break

        if award_amount:
            contracting_process["summary"]["contractValue"] = {"amount": award_amount, "currency": award_currency}


def contract_process_description(state):

    for compiled_release, contracting_process in zip(state.compiled_releases, state.output["contractingProcesses"]):
        contract_descriptions = []
        contract_items_descriptions = []
        for contract in check_type(compiled_release.get("contracts"), list):
            contract = check_type(contract, dict)
            contract_description = contract.get("description")
            if contract_description:
                contract_descriptions.append(contract_description)
            for contract_item in check_type(contract.get("items"), list):
                contract_item = check_type(contract_item, dict)
                contract_item_description = contract_item.get("description")
                if contract_item_description:
                    contract_items_descriptions.append(contract_item_description)
        if len(contract_descriptions) == 1:
            contracting_process["summary"]["description"] = contract_descriptions[0]
            continue
        if len(contract_items_descriptions) == 1:
            contracting_process["summary"]["description"] = contract_items_descriptions[0]
            continue

        award_descriptions = []
        award_items_descriptions = []
        for award in check_type(compiled_release.get("awards"), list):
            award = check_type(award, dict)
            award_description = award.get("description")
            if award_description:
                award_descriptions.append(award_description)
            for award_item in check_type(award.get("items"), list):
                award_item = check_type(award_item, dict)
                award_item_description = award_item.get("description")
                if award_item_description:
                    award_items_descriptions.append(award_item_description)
        if len(award_descriptions) == 1:
            contracting_process["summary"]["description"] = award_descriptions[0]
            continue
        if len(award_items_descriptions) == 1:
            contracting_process["summary"]["description"] = award_items_descriptions[0]
            continue

        tender = check_type(compiled_release.get("tender"), dict)
        tender_description = tender.get("description")
        if tender_description:
            contracting_process["summary"]["description"] = tender_description
            continue

        tender_items_descriptions = []
        for tender_item in check_type(tender.get("items"), list):
            tender_item = check_type(tender_item, dict)
            tender_item_description = tender_item.get("description")
            if tender_item_description:
                tender_items_descriptions.append(tender_item_description)

        if len(tender_items_descriptions) == 1:
            contracting_process["summary"]["description"] = tender_items_descriptions[0]
            continue


def contract_period(state):

    for compiled_release, contracting_process in zip(state.compiled_releases, state.output["contractingProcesses"]):
        awards = check_type(compiled_release.get("awards"), list)
        start_dates = []
        end_dates = []
        for award in awards:
            contract_period = check_type(award.get("contractPeriod"), dict)
            start_date = check_type(contract_period.get("startDate"), str)
            if start_date:
                start_dates.append(start_date)
            end_date = check_type(contract_period.get("endDate"), str)
            if end_date:
                end_dates.append(start_date)
        if start_dates and end_dates:
            contracting_process["summary"]["contractPeriod"] = {
                "startDate": min(start_dates),
                "endDate": max(end_dates),
            }
            continue

        tender = check_type(compiled_release.get("tender"), dict)
        contract_period = tender.get("contractPeriod")
        if contract_period:
            contracting_process["summary"]["contractPeriod"] = contract_period


def project_scope(state):
    return copy_document_by_type(state, "projectScope")


def project_scope_summary(state):
    for compiled_release, contracting_process in zip(state.compiled_releases, state.output["contractingProcesses"]):

        release_tender = compiled_release.get("tender", {})
        items = check_type(release_tender.get("items"), list)
        milestones = check_type(release_tender.get("milestones"), list)

        tender = contracting_process["summary"].get("tender", {})

        if items:
            tender.setdefault("items", []).extend(items)
        if milestones:
            tender.setdefault("milestones", []).extend(milestones)

        contracting_process["summary"]["tender"] = tender


def final_audit(state):

    if not state.output.get("documents"):
        state.output["documents"] = []

    for compiled_release in state.compiled_releases:

        contracts = resolve_pointer(compiled_release, "/contracts", [])
        for contract in contracts:
            documents = resolve_pointer(contract, "/implementation/documents", [])
            for document in check_type(documents, list):
                document = check_type(document, dict)
                if document.get("documentType") == "finalAudit":
                    state.output["documents"].append(document)


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
    cost_estimate,
    contract_title,
    suppliers,
    contract_price,
    contract_process_description,
    contract_period,
    project_scope,
    project_scope_summary,
    final_audit,
]


OPTIONAL_TRANSFORMS = [
    "buyer_role",
    "title_from_tender",
    "location_from_items",
    "purpose_needs_assessment",
    "description_tender",
    "project_scope_summary",
]

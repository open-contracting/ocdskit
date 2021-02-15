# The following document was used during development:
# https://docs.google.com/spreadsheets/d/1xyKXbNktcfKm6siSzM_C7aHCOsOjWUQro5aU8ZYIHyc/edit#gid=1993217545

import copy
import datetime
import decimal
import json
import logging
from collections import defaultdict

import jsonpointer
from ocdsmerge.util import sorted_releases

from ocdskit.combine import merge
from ocdskit.util import is_package

logger = logging.getLogger("ocdskit")


def resolve(doc, pointer):
    return jsonpointer.resolve_pointer(doc, pointer, None)


def resolve_list(doc, pointer):
    return check_type(resolve(doc, pointer), list)


def append_if(array, item):
    if item:
        array.append(item)


def check_type(item, item_type):
    """
    Check type and if incorrect return empty version of type so that future processing works with bad data.
    Should be used with dicts or lists that are then accessed later.
    """
    if not isinstance(item, item_type):
        if item:
            logger.warning("item %s is not of type %s so skipping", item, item_type.__name__)
        return item_type()
    return item


def cast_number_or_zero(item):
    """ Cast to decimal if fail return 0 so summing still works."""
    try:
        return decimal.Decimal(item)
    except (ValueError, TypeError):
        if item:
            logger.warning("item %s is not a number treating as zero", item)
        return 0


def cast_string(item):
    """
    Cast to string if possible. Does not try to convert dict, list, or None to string.
    Returns empty string on failure so future processing works.
    """
    if isinstance(item, (str, float, int, decimal.Decimal)):
        return str(item)

    if item:
        logger.warning("item %s is not able to be converted to a string", item)
    return ""


def run_transforms(config, releases, project_id=None, records=None, output=None):
    """
    Transforms a list of OCDS releases into a OC4IDS project.

    :param dict config: contains optional tranform options.
    :param list releases: list of OCDS releases or release packages
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
    def __init__(self, releases_or_release_packages, project_id=None, records=None, output=None):
        # coerce generator into list as we iterate over it twice.
        releases_or_release_packages = list(releases_or_release_packages)
        all_releases = []
        for releases_or_release_package in releases_or_release_packages:
            if is_package(releases_or_release_package):
                all_releases.extend(check_type(releases_or_release_package.get("releases"), list))
            else:
                all_releases.append(releases_or_release_package)

        self.releases = sorted_releases(all_releases)
        self.releases_by_ocid = defaultdict(list)
        for release in self.releases:
            ocid = cast_string(release.get("ocid"))
            if ocid:
                self.releases_by_ocid[ocid].append(release)

        self.project_id = project_id

        if not records:
            record_package = next(merge(releases_or_release_packages, return_package=True, use_linked_releases=True))
            records = check_type(record_package.get("records"), list)

        compiled_releases = []
        for record in records:
            # projects only have linked releases 'uri' is a good proxy for that.
            record_releases = check_type(record.get("releases"), list)

            compiled_release = check_type(record.get("compiledRelease"), dict)
            compiled_release["releases"] = [release for release in record_releases if release.get("url")]
            compiled_release["embeddedReleases"] = [release for release in record_releases if not release.get("url")]

            compiled_releases.append(compiled_release)

        self.compiled_releases = compiled_releases
        self.output = output or {}
        if project_id and "id" not in self.output:
            self.output["id"] = project_id

        self.party_analysis()

        self.generate_document_ids = False

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
                id_ = cast_string(identifier.get("id"))
                scheme = cast_string(identifier.get("scheme"))
                if id_ and scheme:
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
                found_party["party"]["roles"] = list(set(
                    check_type(found_party["party"].get("roles"), list) + check_type(party["party"].get("roles"), list)
                ))
            else:
                if duplicate_party_ids:
                    if party["unique_identifier"]:
                        party["party"]["id"] = party["unique_identifier"]
                    else:
                        party["party"]["id"] = str(party_num)
                        party_num += 1
                unique_parties.append(party)
            party["original_party"]["_new_id"] = party["party"].get("id")

        self.parties = [party["party"] for party in unique_parties]


def copy_party_to_party_list(state, party):
    output_parties = state.output.get("parties", [])
    if not output_parties:
        state.output["parties"] = output_parties

    output_party = None
    for party_to_match in output_parties:
        if party.get("id") == party_to_match.get("id"):
            output_party = party_to_match

    if not output_party:
        output_party = copy.deepcopy(party)
        output_parties.append(output_party)
    return output_party


def copy_party_by_role(state, role, new_roles=None):
    for party in state.parties:
        if role in check_type(party.get("roles"), list):
            output_party = copy_party_to_party_list(state, party)
            if new_roles:
                output_roles = output_party.get("roles", [])
                output_roles.extend(new_roles)
                output_party["roles"] = list(set(output_roles))


def copy_document(state, document):
    """
    Copies a document. If it finds clashing ids change ids to autoincrement numbers
    """
    output_documents = state.output.get("documents")
    if not output_documents:
        output_documents = []
        state.output["documents"] = output_documents

    duplicate_doc_id = False

    for output_document in output_documents:
        if output_document.get("id") == document.get("id"):
            duplicate_doc_id = True
            break

    output_documents.append(document)

    if duplicate_doc_id:
        for num, doc in enumerate(output_documents):
            doc["id"] = str(num + 1)


def copy_document_by_type(state, documents, document_type):
    """
    Copies documents of specific documentType from planning.documents to documents
    """
    for document in documents(state):
        document = check_type(document, dict)
        if document.get("documentType") == document_type:
            copy_document(state, document)


def concat_ocid_and_string(state, path_to_string):
    """
    Places the ocid of a release in front of a string (eg. description or title)
    so that it can be joined unambiguously with others, separated by new lines
    """
    strings = ""
    for compiled_release in state.compiled_releases:

        ocid = cast_string(resolve(compiled_release, "/ocid"))
        a_string = cast_string(resolve(compiled_release, path_to_string))

        if a_string:
            concat = "<{}> {}\n".format(ocid, a_string)
            strings = strings + concat

    return strings


def public_authority_role(state):
    """
    CoST IDS element: Project owner
    """
    copy_party_by_role(state, "publicAuthority")


def buyer_role(state):
    """
    CoST IDS element: Project owner
    """
    copy_party_by_role(state, "buyer", ["publicAuthority"])


def sector(state):
    """
    CoST IDS element: Sector
    """
    sectors = []
    for compiled_release in state.compiled_releases:
        sector_id = cast_string(resolve(compiled_release, "/planning/project/sector/id"))
        sector_scheme = cast_string(resolve(compiled_release, "/planning/project/sector/scheme"))
        if sector_scheme:
            sector_name = sector_scheme + "-" + sector_id
        else:
            sector_name = sector_id

        if sector_name:
            sectors.append(sector_name)

    if sectors:
        state.output["sector"] = list(set(sectors))


def additional_classifications(state):
    """
    CoST IDS element: Subsector
    """
    for compiled_release in state.compiled_releases:
        additionalclassifications = resolve(compiled_release, "/planning/project/additionalClassifications")
        if additionalclassifications:
            state.output.setdefault("additionalClassifications", [])
            for classification in additionalclassifications:
                if classification not in state.output["additionalClassifications"]:
                    state.output["additionalClassifications"].append(classification)


def title(state):
    """
    CoST IDS element: Project name
    """
    found_title = None
    for compiled_release in state.compiled_releases:
        project_title = resolve(compiled_release, "/planning/project/title")
        if project_title:
            if found_title and found_title != project_title:
                logger.warning("Multiple differing titles found for project %s", state.project_id)
                return
        found_title = project_title
    if found_title:
        state.output["title"] = project_title


def title_from_tender(state):
    """
    CoST IDS element: Project name
    """
    if state.output.get("title"):
        return

    titles = []
    for compiled_release in state.compiled_releases:
        append_if(titles, resolve(compiled_release, "/tender/title"))
    if len(titles) > 1:
        state.output["title"] = concat_ocid_and_string(state, "/tender/title")
    elif len(titles) == 1:
        state.output["title"] = titles[0]


def contracting_process_setup(state):
    """
    This will initailly create the contracting process objects and the summary object within. All transforms that use
    contracting processes need to run this tranform first.
    """
    state.output["contractingProcesses"] = []

    for compiled_release in state.compiled_releases:
        contracting_process = {
            "id": compiled_release.get("ocid"),
            "summary": {
                "ocid": compiled_release.get("ocid"),
            },
        }

        releases = compiled_release.get("releases")
        if releases:
            contracting_process["releases"] = releases

        embedded_releases = compiled_release.get("embeddedReleases")
        if embedded_releases:
            contracting_process["embeddedReleases"] = embedded_releases

        state.output["contractingProcesses"].append(contracting_process)


def procuring_entity(state):
    """
    CoST IDS element: Procuring entity
    """
    copy_party_by_role(state, "procuringEntity")

    for compiled_release, contracting_process in zip(state.compiled_releases, state.output["contractingProcesses"]):
        procuring_entities = []
        for party in check_type(compiled_release.get("parties"), list):
            if "procuringEntity" in check_type(party.get("roles"), list):
                procuring_entities.append(party)
        if len(procuring_entities) > 1:
            logger.warning("More than one procuringEntity in contractingProcesses with ocid %s skipping tranform",
                           compiled_release.get("ocid"))
            continue
        if procuring_entities:
            contracting_process["summary"].setdefault("tender", {})
            organization_reference = {"id": procuring_entities[0].get("_new_id")}
            name = procuring_entities[0].get("name")
            if name:
                organization_reference["name"] = name
            contracting_process["summary"]["tender"]["procuringEntity"] = organization_reference


def administrative_entity(state):
    """
    CoST IDS element: Contract administrative entity
    """
    copy_party_by_role(state, "administrativeEntity")

    for compiled_release, contracting_process in zip(state.compiled_releases, state.output["contractingProcesses"]):
        administrative_entities = []
        for party in check_type(compiled_release.get("parties"), list):
            if "administrativeEntity" in check_type(party.get("roles"), list):
                administrative_entities.append(party)
        if len(administrative_entities) > 1:
            logger.warning("More than one administrativeEntity in contractingProcesses with ocid %s skipping tranform",
                           compiled_release.get("ocid"))
            continue
        if administrative_entities:
            contracting_process["summary"].setdefault("tender", {})
            contracting_process["summary"]["tender"]["administrativeEntity"] = {
                "id": administrative_entities[0].get("_new_id"),
                "name": administrative_entities[0].get("name"),
            }


def contract_status(state):
    """
    CoST IDS element: Contract status
    """
    current_iso_datetime = datetime.datetime.now().isoformat()

    for compiled_release, contracting_process in zip(state.compiled_releases, state.output["contractingProcesses"]):
        tender = check_type(compiled_release.get("tender"), dict)
        contracts = check_type(compiled_release.get("contracts"), list)
        awards = check_type(compiled_release.get("awards"), list)

        closed_tender = tender.get("status") in ("cancelled", "unsuccessful", "withdrawn")

        contract_periods = []
        if tender:
            append_if(contract_periods, check_type(tender.get("contractPeriod"), dict))
        for contract in contracts:
            append_if(contract_periods, check_type(contract.get("period"), dict))
        for award in awards:
            append_if(contract_periods, check_type(award.get("contractPeriod"), dict))

        # pre-award
        if tender and not closed_tender:
            if not awards and not contracts:
                contracting_process["summary"]["status"] = "pre-award"
                continue

            all_contracts_pending = all((contract.get("status") == "pending") for contract in contracts)
            all_awards_pending = all(award.get("status") == "pending" for award in awards)

            if all_contracts_pending and all_awards_pending:
                contracting_process["summary"]["status"] = "pre-award"
                continue

            all_awards_in_future = all(cast_string(award.get("date")) > current_iso_datetime for award in awards)

            award_period_start_date = cast_string(resolve(tender, "/awardPeriod/startDate"))
            award_period_in_future = award_period_start_date > current_iso_datetime

            if all_awards_in_future and award_period_in_future:
                contracting_process["summary"]["status"] = "pre-award"
                continue

        # active

        if any(contract.get("status") == "active" for contract in contracts):
            contracting_process["summary"]["status"] = "active"
            continue

        if any(
            cast_string(period.get("startDate")) < current_iso_datetime <
            cast_string(period.get("endDate", "9999-12-31"))
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
            if all(check_type(award, dict).get("status") in ("cancelled", "unsuccessful") for award in awards):
                contracting_process["summary"]["status"] = "closed"
                continue

        if contracts:
            if all(check_type(contract, dict).get("status") in ("cancelled", "terminated") for contract in contracts):
                contracting_process["summary"]["status"] = "closed"
                continue

        if all(current_iso_datetime > cast_string(period.get("endDate", "9999-12-31")) for period in contract_periods):
            contracting_process["summary"]["status"] = "closed"
            continue


def procurement_process(state):
    """
    CoST IDS element: Procurement process
    """
    for compiled_release, contracting_process in zip(state.compiled_releases, state.output["contractingProcesses"]):
        input_tender = check_type(compiled_release.get("tender"), dict)
        if input_tender:
            procurement_method = input_tender.get("procurementMethod")
            if procurement_method:
                contracting_process["summary"].setdefault("tender", {})
                contracting_process["summary"]["tender"]["procurementMethod"] = procurement_method

            procurement_method_details = input_tender.get("procurementMethodDetails")
            if procurement_method_details:
                contracting_process["summary"].setdefault("tender", {})
                contracting_process["summary"]["tender"]["procurementMethodDetails"] = procurement_method_details


def number_of_tenderers(state):
    """
    CoST IDS element: Number of firms tendering
    """
    for compiled_release, contracting_process in zip(state.compiled_releases, state.output["contractingProcesses"]):
        input_tender = check_type(compiled_release.get("tender"), dict)
        if input_tender:
            numberoftenderers = input_tender.get("numberOfTenderers")
            if numberoftenderers:
                contracting_process["summary"].setdefault("tender", {})
                contracting_process["summary"]["tender"]["numberOfTenderers"] = numberoftenderers


def location(state):
    """
    CoST IDS element: Project location
    """
    all_locations = []
    for compiled_release in state.compiled_releases:
        locations = resolve(compiled_release, "/planning/project/locations")
        if locations:
            all_locations.extend(locations)

    if all_locations:
        state.output["locations"] = all_locations


def location_from_items(state):
    """
    CoST IDS element: Project location
    """
    if state.output.get("locations"):
        return

    locations = []
    for compiled_release in state.compiled_releases:

        items = resolve_list(compiled_release, "/tender/items")
        for item in check_type(items, list):

            append_if(locations, resolve(item, "/deliveryLocation"))

            delivery_address = resolve(item, "/deliveryAddress")
            if delivery_address:
                locations.append({"address": delivery_address})

        if len(locations) > 0:
            state.output["locations"] = locations
            break


def budget(state):
    """
    CoST IDS element: Budget
    """
    if len(state.compiled_releases) == 1:
        budget_value = resolve(state.compiled_releases[0], "/planning/budget/amount")
        if budget_value:
            state.output["budget"] = {"amount": budget_value}
    else:
        budget_currencies = set()
        budget_amounts = []

        for compiled_release in state.compiled_releases:
            budget_amounts.append(
                cast_number_or_zero(resolve(compiled_release, "/planning/budget/amount/amount"))
            )
            budget_currencies.add(resolve(compiled_release, "/planning/budget/amount/currency"))

        if len(budget_currencies) > 1:
            logger.warning("Can't get budget total, %s different currencies found.", len(budget_currencies))
        else:
            state.output["budget"] = {
                "amount": {"amount": sum(budget_amounts), "currency": next(iter(budget_currencies))}
            }


def budget_approval(state):
    """
    CoST IDS element: Project budget approval date
    """
    copy_document_by_type(state, _planning_documents, "budgetApproval")


def environmental_impact(state):
    """
    CoST IDS element: Environmental impact
    """
    copy_document_by_type(state, _planning_documents, "environmentalImpact")


def land_and_settlement_impact(state):
    """
    CoST IDS element: Land and settlement impact
    """
    copy_document_by_type(state, _planning_documents, "landAndSettlementImpact")


def purpose(state):
    """
    CoST IDS element: Purpose
    """
    if len(state.compiled_releases) == 1:
        rationale = resolve(state.compiled_releases[0], "/planning/rationale")
        if rationale:
            state.output["purpose"] = rationale
    else:
        purposes = concat_ocid_and_string(state, "/planning/rationale")
        if purposes != "":
            state.output["purpose"] = purposes


def purpose_needs_assessment(state):
    """
    CoST IDS element: Purpose
    """
    copy_document_by_type(state, _planning_documents, "needsAssessment")


def description(state):
    """
    CoST IDS element: Project description
    """
    output_description = None

    for compiled_release in state.compiled_releases:
        project_description = resolve(compiled_release, "/planning/project/description")
        if project_description:
            if output_description and output_description != project_description:
                logger.warning("Multiple differing planning/project/description found e.g. %s, %s, skipping transform",
                               project_description, output_description)
                return
            output_description = project_description

    if output_description:
        state.output["description"] = output_description


def description_tender(state):
    """
    CoST IDS element: Project description
    """
    if state.output.get("description"):
        return

    if len(state.compiled_releases) == 1:
        tender_description = resolve(state.compiled_releases[0], "/tender/description")
        if tender_description:
            state.output["description"] = tender_description
            return

    else:
        descriptions = concat_ocid_and_string(state, "/tender/description")
        if descriptions != "":
            state.output["description"] = descriptions
            return


def funding_sources(state):
    """
    CoST IDS element: Funding sources
    """
    found_funding_source = False
    for compiled_release in state.compiled_releases:
        parties = resolve_list(compiled_release, "/parties")

        # Get parties from budgetBreakdown.sourceParty
        breakdowns = resolve_list(compiled_release, "/planning/budget/budgetBreakdown")
        if not breakdowns:
            continue

        for breakdown in breakdowns:
            source_party = check_type(resolve(breakdown, "/sourceParty"), dict)
            party_id = source_party.get("id")
            # Look up party data by id in parties
            if parties and party_id:
                for party in parties:
                    party = check_type(party, dict)
                    if party.get("id") == party_id:
                        output_party = copy.deepcopy(party)
                        # Add to parties and set funder in roles
                        if check_type(output_party.get("roles"), list):
                            output_party["roles"].append("funder")
                        else:
                            output_party["roles"] = ["funder"]
                        output_party["id"] = output_party.pop("_new_id")
                        copy_party_to_party_list(state, output_party)
                        found_funding_source = True

    # If no parties from the budget breakdown, copy from top level with 'funder' roles
    if not found_funding_source:
        copy_party_by_role(state, "funder")


def cost_estimate(state):
    """
    CoST IDS element: Cost estimate
    """
    for contracting_process in state.output["contractingProcesses"]:
        ocid = contracting_process.get("id")
        latest_planning_value = None
        for release in state.releases_by_ocid.get(ocid, []):
            tender_status = resolve(release, "/tender/status")
            tender_value = resolve(release, "/tender/value")
            if tender_status == "planning" and tender_value:
                latest_planning_value = tender_value

        if latest_planning_value:
            contracting_process["summary"].setdefault("tender", {})
            contracting_process["summary"]["tender"]["costEstimate"] = latest_planning_value


def contract_title(state):
    """
    CoST IDS element: Contract title
    """
    for compiled_release, contracting_process in zip(state.compiled_releases, state.output["contractingProcesses"]):
        awards = check_type(compiled_release.get("awards"), list)
        contracts = check_type(compiled_release.get("contracts"), list)

        if len(awards) > 1 or len(contracts) > 1:
            tender_title = resolve(compiled_release, "/tender/title")

            if tender_title:
                contracting_process["summary"]["title"] = tender_title
            continue

        for entries in (contracts, awards):
            if len(entries) == 1:
                entry_title = check_type(entries[0], dict).get("title")
                if entry_title:
                    contracting_process["summary"]["title"] = entry_title
                break


def suppliers(state):
    """
    CoST IDS element: Contract firm(s)
    """
    copy_party_by_role(state, "supplier")

    for compiled_release, contracting_process in zip(state.compiled_releases, state.output["contractingProcesses"]):
        parties = check_type(compiled_release.get("parties"), list)
        organization_references = []
        for party in parties:
            if "supplier" in check_type(party.get("roles"), list):
                organization_references.append({"id": party.get("id"), "name": party.get("name")})

        if organization_references:
            contracting_process["summary"]["suppliers"] = organization_references


def contract_price(state):
    """
    CoST IDS element: Contract price
    """
    for compiled_release, contracting_process in zip(state.compiled_releases, state.output["contractingProcesses"]):
        awards = check_type(compiled_release.get("awards"), list)
        award_currency = None
        award_amount = 0
        for award in awards:
            award = check_type(award, dict)
            amount = cast_number_or_zero(resolve(award, "/value/amount"))
            award_amount += amount

            currency = cast_string(resolve(award, "/value/currency"))
            if currency:
                if award_currency is None:
                    award_currency = currency
                else:
                    if currency != award_currency:
                        logger.warning("Multiple currencies not supported %s, %s", award_currency, currency)
                        award_amount = 0
                        break

        if award_amount:
            contracting_process["summary"]["contractValue"] = {"amount": award_amount, "currency": award_currency}


def contract_process_description(state):
    """
    CoST IDS element: Contract scope of work
    """
    for compiled_release, contracting_process in zip(state.compiled_releases, state.output["contractingProcesses"]):
        awards = check_type(compiled_release.get("awards"), list)
        contracts = check_type(compiled_release.get("contracts"), list)

        if len(contracts) > 1 or len(awards) > 1:
            tender = check_type(compiled_release.get("tender"), dict)
            tender_description = tender.get("description")
            if tender_description:
                contracting_process["summary"]["description"] = tender_description
                continue

            tender_items_descriptions = []
            for tender_item in check_type(tender.get("items"), list):
                tender_item = check_type(tender_item, dict)
                append_if(tender_items_descriptions, tender_item.get("description"))

            if len(tender_items_descriptions) == 1:
                contracting_process["summary"]["description"] = tender_items_descriptions[0]
            continue

        for entries in (contracts, awards):
            descriptions = []
            items_descriptions = []
            for entry in entries:
                entry = check_type(entry, dict)
                append_if(descriptions, entry.get("description"))
                for item in check_type(entry.get("items"), list):
                    item = check_type(item, dict)
                    append_if(items_descriptions, item.get("description"))

            if len(descriptions) == 1:
                contracting_process["summary"]["description"] = descriptions[0]
                break
            if len(items_descriptions) == 1:
                contracting_process["summary"]["description"] = items_descriptions[0]
                break


def contract_period(state):
    """
    CoST IDS element: Contract start date and contract period (duration)
    """
    for compiled_release, contracting_process in zip(state.compiled_releases, state.output["contractingProcesses"]):
        start_dates = []
        end_dates = []

        for award in check_type(compiled_release.get("awards"), list):
            period = check_type(award.get("contractPeriod"), dict)
            append_if(start_dates, cast_string(period.get("startDate")))
            append_if(end_dates, cast_string(period.get("endDate")))

        if start_dates and end_dates:
            contracting_process["summary"]["contractPeriod"] = {
                "startDate": min(start_dates),
                "endDate": max(end_dates),
            }
            continue

        period = resolve(compiled_release, "/tender/contractPeriod")
        if period:
            contracting_process["summary"]["contractPeriod"] = period


def project_scope(state):
    """
    CoST IDS element: Project Scope (main output) and Project Scope (projected)
    """
    copy_document_by_type(state, _planning_documents, "projectScope")


def project_scope_summary(state):
    """
    CoST IDS element: Project Scope (main output)
    """
    for compiled_release, contracting_process in zip(state.compiled_releases, state.output["contractingProcesses"]):
        release_tender = compiled_release.get("tender", {})
        tender = contracting_process["summary"].get("tender", {})

        items = check_type(release_tender.get("items"), list)
        if items:
            tender.setdefault("items", []).extend(items)
        milestones = check_type(release_tender.get("milestones"), list)
        if milestones:
            tender.setdefault("milestones", []).extend(milestones)

        contracting_process["summary"]["tender"] = tender


def final_audit(state):
    """
    CoST IDS element: Reference to audit and evaluation reports
    """
    copy_document_by_type(state, _contract_implementation_documents, "finalAudit")


def _contract_implementation_documents(state):
    for compiled_release in state.compiled_releases:
        for contract in resolve_list(compiled_release, "/contracts"):
            yield from resolve_list(contract, "/implementation/documents")


def _planning_documents(state):
    for compiled_release in state.compiled_releases:
        yield from resolve_list(compiled_release, "/planning/documents")


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

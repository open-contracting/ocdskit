import copy
import logging
from collections import OrderedDict
import datetime
from ocdsmerge.util import sorted_releases

import jsonpointer

from ocdskit.combine import merge

logger = logging.getLogger("ocdskit")


def run_transforms(config, releases, project_id=None, dict_cls=None, records=None, output=None, transform_list=None):

    """
    Transforms a list of OCDS releases into a OC4IDS project.

    :param dict config: contains optional tranform options.
    :param list releases: list of OCDS releases
    :param string project_id: project ID of resulting project
    :param cls dict_cls: dict class you want to use in output default OrderedDict
    :param list records: pre computed list of records
    :param dict output: initial project output template project where transformed data will be added
    :param list tranform_list: list of tranform classes, defaults to all classes
    """

    transforms = [InitialTransformState(config, releases, project_id, dict_cls, records, output)]
    if not transform_list:
        transform_list = transform_cls_list

    for transform_cls in transform_list:
        transform = transform_cls(transforms)
        transforms.append(transform)

    return transform.output


class InitialTransformState:
    def __init__(self, config, releases, project_id=None, dict_cls=None, records=None, output=None):
        self.config = config
        self.dict_cls = dict_cls or OrderedDict
        self.releases = sorted_releases(releases)

        self.project_id = project_id
        self.records = records

        if not records:
            self.records = next(merge(self.releases, return_package=True, use_linked_releases=True)).get("records", [])

        compiled_releases = []
        for record in self.records:
            compiled_release = record.get("compiledRelease", self.dict_cls())
            # projects only have linked releases 'uri' is a good proxy for that.
            linked_releases = [release for release in record.get("releases", []) if release.get("url")]
            embeded_releases = [release for release in record.get("releases", []) if not release.get("url")]

            compiled_release["releases"] = linked_releases
            compiled_release["embededReleases"] = embeded_releases

            compiled_releases.append(compiled_release)

        self.compiled_releases = compiled_releases
        self.output = output or self.dict_cls()
        if project_id and "id" not in self.output:
            self.output["id"] = project_id
        self.success = True


class BaseTransform:
    def __init__(self, last_transforms):
        last_transform = last_transforms[-1]
        self.last_transforms = last_transforms
        self.config = last_transform.config
        self.dict_cls = last_transform.dict_cls
        self.releases = last_transform.releases
        self.compiled_releases = last_transform.compiled_releases
        self.records = last_transform.records
        self.output = last_transform.output
        self.last_transform_success = last_transform.success
        self.success = False

        self.run()

    def run(self):
        pass

    def copy_party_by_role(self, role, new_roles=None):

        for compiled_release in self.compiled_releases:
            parties = compiled_release.get("parties", [])
            if not isinstance(parties, list):
                continue
            for party in compiled_release.get("parties", []):
                if role in party.get("roles", []):
                    output_parties = self.output.get("parties", [])
                    if not output_parties:
                        self.output["parties"] = output_parties
                    output_party = copy.deepcopy(party)
                    if new_roles:
                        output_roles = output_party.get("roles", [])
                        output_roles.extend(new_roles)
                        output_party["roles"] = output_roles
                    output_parties.append(output_party)
                    self.success = True

    def copy_document_by_type(self, documentType):

        if not self.output.get("documents"):
            self.output["documents"] = []

        for compiled_release in self.compiled_releases:
            documents = jsonpointer.resolve_pointer(compiled_release, "/planning/documents", [])
            for document in documents:
                if documentType in document.get("documentType", []):
                    self.output["documents"].append(document)
                    self.success = True


class PublicAuthorityRole(BaseTransform):
    def run(self):
        self.copy_party_by_role("publicAuthority")


class BuyerRole(BaseTransform):
    def run(self):
        if self.config.get("copy_buyer_role"):
            self.copy_party_by_role("buyer", ["publicAuthority"])
        else:
            self.success = True


class Sector(BaseTransform):
    def run(self):
        for compiled_release in self.compiled_releases:
            sector = jsonpointer.resolve_pointer(compiled_release, "/planning/project/sector", None)
            if sector:
                self.output["sector"] = sector
                self.success = True
                break


class AdditionalClassifications(BaseTransform):
    def run(self):
        for compiled_release in self.compiled_releases:
            additionalClassifications = jsonpointer.resolve_pointer(
                compiled_release, "/planning/project/additionalClassifications", None
            )
            if additionalClassifications:
                self.output["additionalClassifications"] = additionalClassifications
                self.success = True
                break


class Title(BaseTransform):
    def run(self):
        for compiled_release in self.compiled_releases:
            title = jsonpointer.resolve_pointer(compiled_release, "/planning/project/title", None)
            if title:
                self.output["title"] = title
                self.success = True
                break


class TitleFromTender(BaseTransform):
    def run(self):
        if not self.config.get("use_tender_title"):
            self.success = True
            return
        if self.last_transforms[-1].success:
            self.success = True
            return

        for compiled_release in self.compiled_releases:
            title = jsonpointer.resolve_pointer(compiled_release, "/tender/title", None)
            if title:
                self.output["title"] = title
                self.success = True
                break


class ContractingProcessSetup(BaseTransform):
    """ This will initailly create the contracting process objects and the summary object
    within.  All transforms that use contracting processes need to run this tranform first."""

    def run(self):

        self.output["contractingProcesses"] = []

        for compiled_release in self.compiled_releases:
            contracting_process = self.dict_cls()
            contracting_process["id"] = compiled_release.get("ocid")
            contracting_process["summary"] = self.dict_cls()
            contracting_process["summary"]["ocid"] = compiled_release.get("ocid")

            releases = compiled_release.get("releases")
            if releases:
                contracting_process["releases"] = releases

            embeded_releases = compiled_release.get("embededReleases")
            if embeded_releases:
                contracting_process["embededReleases"] = embeded_releases

            self.output["contractingProcesses"].append(contracting_process)


class ProcuringEntity(BaseTransform):
    def run(self):
        self.copy_party_by_role("procuringEntity")

        for compiled_release, contracting_process in zip(self.compiled_releases, self.output["contractingProcesses"]):
            procuring_entity = jsonpointer.resolve_pointer(compiled_release, "/tender/procuringEntity", None)
            if procuring_entity:
                tender = contracting_process["summary"].get("tender", self.dict_cls())
                tender["procuringEntity"] = procuring_entity
                contracting_process["summary"]["tender"] = tender


class AdministrativeEntity(BaseTransform):
    def run(self):
        self.copy_party_by_role("administrativeEntity")

        for compiled_release, contracting_process in zip(self.compiled_releases, self.output["contractingProcesses"]):
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
                tender = contracting_process["summary"].get("tender", self.dict_cls())
                administrative_entity = self.dict_cls()
                administrative_entity["id"] = administrative_entities[0].get("id")
                administrative_entity["name"] = administrative_entities[0].get("name")
                tender["administrativeEntity"] = administrative_entity
                contracting_process["summary"]["tender"] = tender


class ContractStatus(BaseTransform):
    def run(self):

        current_iso_datetime = datetime.datetime.now().isoformat()

        for compiled_release, contracting_process in zip(self.compiled_releases, self.output["contractingProcesses"]):
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


class ProcurementProcess(BaseTransform):
    def run(self):
        for compiled_release, contracting_process in zip(self.compiled_releases, self.output["contractingProcesses"]):
            input_tender = compiled_release.get("tender", {})
            if input_tender:
                procurement_method = input_tender.get("procurementMethod")
                if procurement_method:
                    tender = contracting_process["summary"].get("tender", self.dict_cls())
                    tender["procurementMethod"] = procurement_method
                    contracting_process["summary"]["tender"] = tender

                procurement_method_details = input_tender.get("procurementMethodDetails")
                if procurement_method_details:
                    tender = contracting_process["summary"].get("tender", self.dict_cls())
                    tender["procurementMethodDetails"] = procurement_method_details
                    contracting_process["summary"]["tender"] = tender


class NumberOfTenderers(BaseTransform):
    def run(self):
        for compiled_release, contracting_process in zip(self.compiled_releases, self.output["contractingProcesses"]):
            input_tender = compiled_release.get("tender", {})
            if input_tender:
                number_of_tenderers = input_tender.get("numberOfTenderers")
                if number_of_tenderers:
                    tender = contracting_process["summary"].get("tender", self.dict_cls())
                    tender["numberOfTenderers"] = number_of_tenderers
                    contracting_process["summary"]["tender"] = tender


class Location(BaseTransform):
    def run(self):
        for compiled_release in self.compiled_releases:
            locations = jsonpointer.resolve_pointer(compiled_release, "/planning/project/locations", None)
            if locations:
                self.output["locations"] = locations
                self.success = True
                break


class LocationFromItems(BaseTransform):
    def run(self):
        if not self.config.get("infer_location"):
            self.success = True
            return
        if self.last_transforms[-1].success:
            self.success = True
            return

        locations = []
        for compiled_release in self.compiled_releases:

            items = jsonpointer.resolve_pointer(compiled_release, "/items", None)
            for item in items:

                delivery_location = jsonpointer.resolve_pointer(item, "/deliveryLocation", None)
                if delivery_location:
                    locations.append(delivery_location)

                delivery_address = jsonpointer.resolve_pointer(item, "/deliveryAddress", None)
                if delivery_address:
                    locations.append({"address": delivery_address})

            if len(locations) > 0:
                self.output["locations"] = locations
                self.success = True
                break


class Budget(BaseTransform):
    def run(self):
        if len(self.compiled_releases) == 1:
            budget_value = jsonpointer.resolve_pointer(self.compiled_releases[0], "/planning/budget/amount", None)
            self.output["budget"] = {"amount": budget_value}
            self.success = True
        else:
            budget_currencies = set()
            budget_amounts = []

            for compiled_release in self.compiled_releases:
                budget_amounts.append(
                    float(jsonpointer.resolve_pointer(compiled_release, "/planning/budget/amount/amount", None))
                )
                budget_currencies.add(
                    jsonpointer.resolve_pointer(compiled_release, "/planning/budget/amount/currency", None)
                )

            if len(budget_currencies) > 1:
                logger.warning("Can't get budget total, {} different currencies found.".format(len(budget_currencies)))
            else:
                self.output["budget"] = {
                    "amount": {"amount": sum(budget_amounts), "currency": next(iter(budget_currencies))}
                }
                self.success = True


class BudgetApproval(BaseTransform):
    def run(self):
        self.copy_document_by_type("budgetApproval")


transform_cls_list = [
    ContractingProcessSetup,
    PublicAuthorityRole,
    BuyerRole,
    Sector,
    AdditionalClassifications,
    Title,
    TitleFromTender,
    ProcuringEntity,
    AdministrativeEntity,
    ContractStatus,
    ProcurementProcess,
    Location,
    LocationFromItems,
    Budget,
    BudgetApproval,
]

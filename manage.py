#!/usr/bin/env python
import csv
import json
import warnings
from collections import defaultdict
from pathlib import Path
from unittest.mock import Mock

import click
from libcove.lib.common import (
    _get_schema_deprecated_paths,
    _get_schema_non_required_ids,
    get_schema_codelist_paths,
    schema_dict_fields_generator,
)
from ocdsextensionregistry import ExtensionRegistry, ProfileBuilder
from ocdsextensionregistry.exceptions import VersionedReleaseTypeWarning
from ocdsextensionregistry.util import replace_refs

URL = "https://raw.githubusercontent.com/open-contracting/extension_registry/main/extension_versions.csv"

# "Extension registry determinations (evaluations)" spreadsheet.
# 2024-10-31: Excludes 1 broken below and 12 in pluck-package-extensions.json.
MANUAL_DISCOVERY = {
    "https://bitbucket.org/izelayas/ocds_releasesource_extension/raw/master/extension.json",
    "https://gitlab.com/MaEliK/ocds_etiquette_extension/-/raw/master/extension.json",
    "https://raw.githubusercontent.com/CompraNet/ocds_cycle_extension/master/extension.json",
    "https://raw.githubusercontent.com/CompraNet/ocds_schemeUrl_extension/master/extension.json",
    "https://raw.githubusercontent.com/INAImexico/ocds_awardRationale_extension/master/extension.json",
    "https://raw.githubusercontent.com/INAImexico/ocds_budgetLines_extension/master/extension.json",
    "https://raw.githubusercontent.com/INAImexico/ocds_clarificationMeetings_extension/master/extension.json",
    "https://raw.githubusercontent.com/INAImexico/ocds_contactPointType_extension/master/extension.json",
    "https://raw.githubusercontent.com/INAImexico/ocds_extendedProcurementCategory_extension/master/extension.json",
    "https://raw.githubusercontent.com/INAImexico/ocds_implementationStatus_extension/master/extension.json",
    "https://raw.githubusercontent.com/INAImexico/ocds_nameBreakdown_extension/master/extension.json",
    "https://raw.githubusercontent.com/INAImexico/ocds_paymentMethod_extension/master/extension.json",
    "https://raw.githubusercontent.com/INAImexico/ocds_publicNotices_extension/master/extension.json",
    "https://raw.githubusercontent.com/INAImexico/ocds_requestForQuotes_extension/master/extension.json",
    "https://raw.githubusercontent.com/INAImexico/ocds_surveillanceMechanisms_extension/master/extension.json",
    "https://raw.githubusercontent.com/INAImexico/ocds_taxes_extension/master/extension.json",
    "https://raw.githubusercontent.com/SEFINHN-UIT/EDCA-SEFIN/master/financialObligations/extension.json",
    "https://raw.githubusercontent.com/emanuelzh/ocds-exchangerate-extension/master/extension.json",
    "https://raw.githubusercontent.com/kyv/ocds_compranet_extension/master/extension.json",
    "https://raw.githubusercontent.com/leobaz/ocds_deductionAmountFromContract_extension/master/extension.json",
    "https://raw.githubusercontent.com/leobaz/ocds_estimatedSizeOfProcurementValue_extension/master/extension.json",
    "https://raw.githubusercontent.com/leobaz/ocds_expectedNumberOfTransactions_extension/master/extension.json",
    "https://raw.githubusercontent.com/leobaz/ocds_isAcceleratedProcedure_extension/master/extension.json",
    "https://raw.githubusercontent.com/openprocurement/ocds_auction_extension/master/extension.json",
    "https://raw.githubusercontent.com/openprocurement/ocds_currentStage_extension/master/extension.json",
    "https://raw.githubusercontent.com/openprocurement/ocds_deliveryDate_extension/master/extension.json",
    "https://raw.githubusercontent.com/openprocurement/ocds_eligibility_extension/master/extension.json",
    "https://raw.githubusercontent.com/openprocurement/ocds_guarantee_extension/master/extension.json",
    "https://raw.githubusercontent.com/openprocurement/ocds_linkedDocument_extension/master/extension.json",
    "https://raw.githubusercontent.com/openprocurement/ocds_negotiation_extension/master/extension.json",
    "https://raw.githubusercontent.com/openprocurement/ocds_pendingCancellation_extension/master/extension.json",
    "https://raw.githubusercontent.com/openprocurement/ocds_procurementMethodType_extension/master/extension.json",
    "https://raw.githubusercontent.com/openprocurement/ocds_qualification_extension/master/extension.json",
    "https://raw.githubusercontent.com/openprocurement/ocds_valueAddedTax_extension/master/extension.json",
    "https://raw.githubusercontent.com/sdd1982/IsSmallCompany/master/extension.json",
    "https://raw.githubusercontent.com/sdd1982/additionalContactPoint/master/extension.json",
    "https://raw.githubusercontent.com/sdd1982/awardAddress/master/extension.json",
    "https://raw.githubusercontent.com/sdd1982/branch/master/extension.json",
    "https://raw.githubusercontent.com/sdd1982/businessOperationName/master/extension.json",
    "https://raw.githubusercontent.com/sdd1982/expressionAddress/master/extension.json",
    "https://raw.githubusercontent.com/sdd1982/expressionEmail/master/extension.json",
    "https://raw.githubusercontent.com/sdd1982/isGroup/master/extension.json",
    "https://raw.githubusercontent.com/sdd1982/lastUpdate/master/extension.json",
    "https://raw.githubusercontent.com/sdd1982/level/master/extension.json",
    "https://raw.githubusercontent.com/sdd1982/obligada/master/extension.json",
    "https://raw.githubusercontent.com/sdd1982/order/master/extension.json",
    "https://raw.githubusercontent.com/sdd1982/processStatistics/master/extension.json",
    "https://raw.githubusercontent.com/sdd1982/sector/master/extension.json",
    "https://raw.githubusercontent.com/sdd1982/socialMediaUrls/master/extension.json",
    "https://raw.githubusercontent.com/transpresupuestaria/ocds_multiple_buyers_extension/master/extension.json",
    "https://raw.githubusercontent.com/uStudioCompany/eOCDS-addressDetails/master/extension.json",
    "https://raw.githubusercontent.com/uStudioCompany/eOCDS-conversions/master/extension.json",
    "https://raw.githubusercontent.com/uStudioCompany/eOCDS-options/master/extension.json",
    "https://raw.githubusercontent.com/viktor992/budget-breakdown/master/extension.json",
    "https://raw.githubusercontent.com/viktor992/dncp-contract-code/master/extension.json",
    "https://raw.githubusercontent.com/viktor992/record-package-uri/master/extension.json",
    "https://raw.githubusercontent.com/viktor992/transactions/master/extension.json",
    "https://raw.githubusercontent.com/yshalenyk/ocds_contractNumber_extension/master/extension.json",
    "https://raw.githubusercontent.com/austender/austender-ocds-api/refs/heads/master/schema/release-schema.json",
}

BROKEN_EXTENSIONS = {
    # "#/definitions/value" is an unresolvable reference, and "budgetClassifications" is nested incorrectly.
    "https://raw.githubusercontent.com/transpresupuestaria/ocds_budget_classifications_extension/master/extension.json",
    # New South Wales uses a patched OCDS 1.0 release schema, which changes OrganizationReference to Organization.
    "https://tenders.nsw.gov.au/public_data/API/NSW-eTendering-API-release-schema.json",
}

CONFLICTING_EXTENSIONS = {
    # ocds_secondStageDescription_extension has Lot.secondStage and SecondStage. DNCP's ocds_secondStage_extension has
    # SecondStage.invitations and Invitation.lots. Mixing them causes a circular reference.
    #
    # DNCP's ocds_complaints_extension and Open Procurement's ocds_complaint_extension define Complaint, but only DNCP
    # requires "id".
    #
    # DNCP's ocds_clarification_meetings_extension and Contrataciones Abiertas's ocds_clarificationMeetings_extension
    # define ClarificationMeeting, but only DNCP requires "id".
    #
    # Guatecompras' ocds_partyDetails_publicEntitiesLevelDetails_extension and sdd1982's legalEntityTypeDetail and
    # level define Organization.details.legalEntityTypeDetail and .type, as object and string, respectively.
    "a": {
        "https://gitlab.com/dncp-opendata/ocds_secondStage_extension/raw/master/extension.json",
        "https://gitlab.com/dncp-opendata/ocds_complaints_extension/raw/master/extension.json",
        "https://gitlab.com/dncp-opendata/ocds_clarification_meetings_extension/raw/master/extension.json",
        "https://raw.githubusercontent.com/guatecompras/ocds_partyDetails_publicEntitiesLevelDetails_extension/main/extension.json",
    },
    "b": {
        "https://raw.githubusercontent.com/open-contracting-extensions/ocds_secondStageDescription_extension/master/extension.json",
        "https://raw.githubusercontent.com/openprocurement/ocds_complaint_extension/master/extension.json",
        "https://raw.githubusercontent.com/contratacionesabiertas/ocds_clarificationMeetings_extension/master/extension.json",
        "https://raw.githubusercontent.com/sdd1982/legalEntityTypeDetail/master/extension.json",
        "https://raw.githubusercontent.com/sdd1982/level/master/release-schema.json",
        # The OCDS for EU and OCDS for eForms profiles contain ocds_secondStage_extension.
        # `netherlands` doesn't use "https://standard.open-contracting.org/profiles/eforms/latest/en/extension.json".
        # https://standard.open-contracting.org/profiles/eforms/latest/en/reference/
        # https://standard.open-contracting.org/profiles/eu/latest/en/reference/
        "https://raw.githubusercontent.com/open-contracting-extensions/eforms/latest/schema/profile/extension.json",
        "https://standard.open-contracting.org/profiles/eu/master/en/extension.json",
    },
}

BASEDIR = Path("tests") / "fixtures"


def read(path):
    with path.open() as f:
        return json.load(f)


def write(path, data, **kwargs):
    if "indent" not in kwargs:
        kwargs["separators"] = (",", ":")
    with path.open("w") as f:
        json.dump(data, f, **kwargs)
        f.write("\n")


@click.command()
@click.argument("file", type=click.File())
@click.option("--tag", default="1__1__5")
@click.option("--clobber", is_flag=True)
@click.option("-k", "--keep", multiple=True, type=click.Choice(["release-package", "release-schema"]))
@click.option("-v", "--verbose", is_flag=True)
def main(file, tag, clobber, keep, verbose):
    """
    Write test fixtures under tests/fixtures/ for test_regression.py.

    Apply extensions from the Extension Registry and Kingfisher Collect.

    To prepare the input file, run:

        \b
        scrapy pluck --loglevel=ERROR --package-pointer /extensions

        \b
        for spider in paraguay_dncp_releases paraguay_hacienda; do
            env \\
                KINGFISHER_PARAGUAY_HACIENDA_REQUEST_TOKEN=... \\
                KINGFISHER_PARAGUAY_HACIENDA_CLIENT_SECRET=... \\
                KINGFISHER_PARAGUAY_DNCP_REQUEST_TOKEN=... \\
                scrapy crawl $spider -a sample=1
        done

        \b
        find data -mtime -1 -path '*_sample/*.json' -exec jq -c .extensions {} + |
            tr '"' "'" | sed 's/^/"/;s/$/"/' >> pluck-package-extensions.csv

    To debug "ValueError: Circular reference detected", write `script.js`:

        \b
        const schemaObject = {}
        import { analyzeTypes, analyzeTypesFast } from 'json-schema-cycles'
        const { cycles, entrypoints, dependencies, dependents, all, graph } = analyzeTypes( schemaObject );
        console.log(cycles)

    Copy-paste the relevant release schema into `schemaObject`, and run:

        \b
        npm install json-schema-cycles
        node script.js
    """  # noqa: D301 # click escapes
    # The first column of pluck-package-extensions.csv can be JSON text or an error message.
    universe = {f"{version.base_url}extension.json" for version in ExtensionRegistry(URL) if not version.date} | {
        extension for value, *rest in csv.reader(file) if value.startswith("[") for extension in json.loads(value)
    }

    if intersection := universe & MANUAL_DISCOVERY:
        click.secho("These extensions can be removed from `MANUAL_DISCOVERY` in manage.py:", fg="yellow")
        click.echo("\n".join(intersection))

    universe.update(MANUAL_DISCOVERY)
    universe -= BROKEN_EXTENSIONS

    for name, exclude in CONFLICTING_EXTENSIONS.items():
        directory = BASEDIR / name
        directory.mkdir(exist_ok=True)

        release_package_path = directory / "release-package.json"
        release_schema_path = directory / "release-schema.json"

        extensions = sorted(universe.copy() - exclude)
        builder = ProfileBuilder(tag, extensions)

        # Skip writing files if the extensions list hasn't changed.
        if clobber:
            overwrite = True
        else:
            overwrite = not release_package_path.exists() or read(release_package_path)["extensions"] != extensions

        if overwrite and "release-package" not in keep:
            write(release_package_path, {"extensions": extensions, "releases": []}, indent=2)

        if (overwrite and "release-schema" not in keep) or not release_schema_path.exists():
            patched = builder.patched_release_schema(extension_field="extension", extension_value="url")
            write(release_schema_path, patched, indent=2)
        else:
            patched = read(release_schema_path)

        for package_type in ("release", "record"):
            package_schema_path = directory / f"{package_type}-package-schema-dereferenced.json"
            additional_path = directory / f"{package_type}-additional.json"
            codelist_path = directory / f"{package_type}-codelist.json"
            deprecated_path = directory / f"{package_type}-deprecated.json"
            missing_ids_path = directory / f"{package_type}-missing-ids.json"

            # See libcoveocds.schema.SchemaOCDS.patched_package_schema().
            if overwrite or not package_schema_path.exists():
                with warnings.catch_warnings(record=verbose) as wlist:
                    if not verbose:
                        warnings.filterwarnings("ignore", category=VersionedReleaseTypeWarning)

                    # Replace package-level `$ref`s, like in `records`.
                    package_schema = replace_refs(getattr(builder, f"{package_type}_package_schema")(patched=patched))

                messages_by_extension = defaultdict(list)
                if wlist:
                    for w in wlist:
                        if issubclass(w.category, VersionedReleaseTypeWarning):
                            messages_by_extension[w.message.schema.get("extension", "N/A")].append(w.message)
                        else:
                            click.echo(w, err=True)
                if messages_by_extension:
                    click.secho(package_schema_path, fg="red", err=True)
                    for extension, messages in sorted(messages_by_extension.items()):
                        click.secho(f"  {extension}", fg="yellow", err=True)
                        for message in messages:
                            click.echo(f"    {message}", err=True)

                write(package_schema_path, package_schema)
            else:
                package_schema = read(package_schema_path)

            mock = Mock()
            mock.get_pkg_schema_obj = Mock(return_value=package_schema)

            if overwrite or not additional_path.exists():
                write(additional_path, sorted(set(schema_dict_fields_generator(package_schema))))
            if overwrite or not codelist_path.exists():
                write(codelist_path, [[key, value] for key, value in get_schema_codelist_paths(mock).items()])
            if overwrite or not deprecated_path.exists():
                write(deprecated_path, _get_schema_deprecated_paths(mock))
            if overwrite or not missing_ids_path.exists():
                write(missing_ids_path, _get_schema_non_required_ids(mock))


if __name__ == "__main__":
    main()

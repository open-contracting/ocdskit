import json
import copy

import ocdskit.oc4ids_transforms as transforms
from tests import read


def test_initial_tranform_state():
    releases = json.loads(read("release-package_additional-contact-points.json"))["releases"]
    initial_transform = transforms.InitialTransformState({}, releases, "1")
    assert len(initial_transform.compiled_releases) == 1


def test_run_all():
    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "parties": [{"id": "1", "roles": ["publicAuthority"]}],
        }
    ]
    output = transforms.run_transforms({}, releases, "1")
    assert output["parties"] == releases[0]["parties"]


def test_public_authority_role():
    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "parties": [{"id": "1", "roles": ["publicAuthority"]}, {"id": "2", "roles": ["publicAuthority"]}],
        }
    ]

    output = transforms.run_transforms({}, releases, "1", transform_list=[transforms.PublicAuthorityRole])
    assert output["parties"] == releases[0]["parties"]

    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "parties": [{"id": "1", "roles": ["publicAuthority"]}, {"id": "2", "roles": ["buyer"]}],
        }
    ]

    output = transforms.run_transforms({}, releases, "1", transform_list=[transforms.PublicAuthorityRole])
    assert len(output["parties"]) == 1


def test_buyer_role():
    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "parties": [{"id": "1", "roles": ["buyer"]}],
        }
    ]

    initial_transform = transforms.InitialTransformState({}, copy.deepcopy(releases), "1")
    transform = transforms.BuyerRole([initial_transform])

    # No config to say to convert buyers
    assert "parties" not in transform.output
    assert transform.success

    initial_transform = transforms.InitialTransformState({"copy_buyer_role": True}, copy.deepcopy(releases), "1")
    transform = transforms.BuyerRole([initial_transform])

    assert transform.success
    assert "publicAuthority" in transform.output["parties"][0]["roles"]
    assert "buyer" in transform.output["parties"][0]["roles"]


def test_sector():
    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "planning": {"project": {"sector": "a"}},
        }
    ]

    initial_transform = transforms.InitialTransformState({}, copy.deepcopy(releases), "1")
    transform = transforms.Sector([initial_transform])
    assert transform.success
    assert transform.output["sector"] == "a"


def test_additional_classifications():
    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "planning": {"project": {"additionalClassifications": [{"scheme": "a", "id": "1"}]}},
        }
    ]

    initial_transform = transforms.InitialTransformState({}, copy.deepcopy(releases), "1")
    transform = transforms.AdditionalClassifications([initial_transform])
    assert transform.success
    assert transform.output["additionalClassifications"] == [{"scheme": "a", "id": "1"}]


def test_title():
    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "planning": {"project": {"title": "a title"}},
        }
    ]

    initial_transform = transforms.InitialTransformState({}, copy.deepcopy(releases), "1")
    transform = transforms.Title([initial_transform])
    assert transform.success
    assert transform.output["title"] == "a title"


def test_title_from_tender():
    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "tender": {"title": "a title"},
        }
    ]

    initial_transform = transforms.InitialTransformState({"use_tender_title": True}, copy.deepcopy(releases), "1")
    title_transform = transforms.Title([initial_transform])
    transform = transforms.TitleFromTender([initial_transform, title_transform])
    assert transform.success
    assert transform.output["title"] == "a title"

    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "planning": {"project": {"title": "a title"}},
            "tender": {"title": "a non used title"},
        }
    ]

    initial_transform = transforms.InitialTransformState({"use_tender_title": True}, copy.deepcopy(releases), "1")
    title_transform = transforms.Title([initial_transform])
    transform = transforms.TitleFromTender([initial_transform, title_transform])
    assert transform.success
    assert transform.output["title"] == "a title"


def test_contracting_process_setup_releases():
    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "tender": {"title": "a title"},
        },
        {
            "ocid": "ocds-213czf-2",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "tender": {"title": "a title"},
        },
    ]

    output = transforms.run_transforms(
        {}, copy.deepcopy(releases), "1", dict_cls=dict, transform_list=[transforms.ContractingProcessSetup]
    )

    expected = """
    {
      "id": "1",
      "contractingProcesses": [
        {
          "id": "ocds-213czf-1",
          "summary": {
            "ocid": "ocds-213czf-1"
          },
          "embededReleases": [
            {
              "ocid": "ocds-213czf-1",
              "id": "1",
              "tag": "planning",
              "date": "2001-02-03T04:05:06Z",
              "tender": {
                "title": "a title"
              }
            }
          ]
        },
        {
          "id": "ocds-213czf-2",
          "summary": {
            "ocid": "ocds-213czf-2"
          },
          "embededReleases": [
            {
              "ocid": "ocds-213czf-2",
              "id": "1",
              "tag": "planning",
              "date": "2001-02-03T04:05:06Z",
              "tender": {
                "title": "a title"
              }
            }
          ]
        }
      ]
    }
    """

    assert output == json.loads(expected)


def test_contracting_process_setup_release_packages():

    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "tender": {"title": "a title"},
        },
        {
            "ocid": "ocds-213czf-2",
            "id": "2",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "tender": {"title": "a title"},
        },
    ]

    release_packages = [{"uri": "example.com", "releases": releases}]

    output = transforms.run_transforms(
        {}, copy.deepcopy(release_packages), "1", dict_cls=dict, transform_list=[transforms.ContractingProcessSetup]
    )

    expected = """
    {
      "id": "1",
      "contractingProcesses": [
        {
          "id": "ocds-213czf-1",
          "summary": {
            "ocid": "ocds-213czf-1"
          },
          "releases": [
            {
              "url": "example.com#1",
              "date": "2001-02-03T04:05:06Z",
              "tag": "planning"
            }
          ]
        },
        {
          "id": "ocds-213czf-2",
          "summary": {
            "ocid": "ocds-213czf-2"
          },
          "releases": [
            {
              "url": "example.com#2",
              "date": "2001-02-03T04:05:06Z",
              "tag": "planning"
            }
          ]
        }
      ]
    }
    """

    assert output == json.loads(expected)


def test_procuring_entity():

    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "tender": {"procuringEntity": {"id": 1}},
            "parties": [{"id": "1", "roles": ["procuringEntity"]}],
        },
    ]

    output = transforms.run_transforms(
        {},
        copy.deepcopy(releases),
        "1",
        dict_cls=dict,
        transform_list=[transforms.ContractingProcessSetup, transforms.ProcuringEntity],
    )

    assert output["parties"] == releases[0]["parties"]
    assert output["contractingProcesses"][0]["summary"]["tender"] == releases[0]["tender"]


def test_administrative_entity():

    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "parties": [{"id": "1", "name": "a", "roles": ["administrativeEntity"]}],
        },
    ]

    output = transforms.run_transforms(
        {},
        copy.deepcopy(releases),
        "1",
        dict_cls=dict,
        transform_list=[transforms.ContractingProcessSetup, transforms.AdministrativeEntity],
    )

    assert output["parties"] == releases[0]["parties"]
    assert output["contractingProcesses"][0]["summary"]["tender"]["administrativeEntity"] == {"id": "1", "name": "a"}


def test_multiple_administrative_entity_in_process():
    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "parties": [
                {"id": "1", "name": "a", "roles": ["administrativeEntity"]},
                {"id": "2", "name": "b", "roles": ["administrativeEntity"]},
            ],
        },
    ]

    output = transforms.run_transforms(
        {},
        copy.deepcopy(releases),
        "1",
        transform_list=[transforms.ContractingProcessSetup, transforms.AdministrativeEntity],
    )

    assert output["parties"] == releases[0]["parties"]

    # tender is not created as there are multiple adminastrative entities
    assert "tender" not in output["contractingProcesses"][0]["summary"]


def test_contract_status_pre_award():

    releases = [
        {"ocid": "ocds-213czf-1", "id": "1", "tag": "planning", "date": "2001-02-03T04:05:06Z", "tender": {"id": 1}},
        {
            "ocid": "ocds-213czf-2",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "contracts": [{"status": "pending"}],
            "awards": [{"status": "pending"}],
            "tender": {"id": 1},
        },
        {
            "ocid": "ocds-213czf-3",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "contracts": [{"status": "active"}],
            "awards": [{"status": "pending"}],
            "tender": {"id": 1},
        },
        {
            "ocid": "ocds-213czf-4",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "awards": [{"status": "pending", "date": "3000-01-01"}],
            "tender": {"id": 1, "awardPeriod": {"startDate": "3000-01-01"}},
        },
        {
            "ocid": "ocds-213czf-5",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "awards": [{"date": "3000-01-01"}],
            "tender": {"id": 1, "awardPeriod": {"startDate": "2000-01-01"}},
        },
        {
            "ocid": "ocds-213czf-6",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "awards": [{"date": "2000-01-01"}],
            "tender": {"id": 1, "awardPeriod": {"startDate": "3000-01-01"}},
        },
    ]

    output = transforms.run_transforms(
        {},
        copy.deepcopy(releases),
        "1",
        transform_list=[transforms.ContractingProcessSetup, transforms.ContractStatus],
    )

    assert output["contractingProcesses"][0]["summary"]["status"] == "pre-award"
    assert output["contractingProcesses"][1]["summary"]["status"] == "pre-award"
    assert output["contractingProcesses"][2]["summary"]["status"] != "pre-award"
    assert output["contractingProcesses"][3]["summary"]["status"] == "pre-award"

    # Currently no status at all as fits no status
    assert output["contractingProcesses"][4]["summary"].get("status") != "pre-award"
    assert output["contractingProcesses"][5]["summary"].get("status") != "pre-award"


def test_contract_status_active():

    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "contracts": [{"status": "active"}, {"status": "pending"}],
            "tender": {"id": 1},
        },
        {
            "ocid": "ocds-213czf-2",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "contracts": [{"period": {"startDate": "2000-01-01"}}],
            "tender": {"id": 1},
        },
        {
            "ocid": "ocds-213czf-3",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "contracts": [{"period": {"startDate": "2000-01-01", "endDate": "2000-01-01"}}],
            "tender": {"id": 1},
        },
        {
            "ocid": "ocds-213czf-4",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "contracts": [{"period": {"startDate": "2000-01-01", "endDate": "2000-01-01"}}],
            "awards": [{"contractPeriod": {"startDate": "2000-01-01", "endDate": "3000-01-01"}}],
            "tender": {"id": 1},
        },
        {
            "ocid": "ocds-213czf-5",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "contracts": [{"period": {"startDate": "2000-01-01", "endDate": "2000-01-01"}}],
            "tender": {"id": 1, "contractPeriod": {"startDate": "2000-01-01", "endDate": "3000-01-01"}},
        },
    ]

    output = transforms.run_transforms(
        {},
        copy.deepcopy(releases),
        "1",
        transform_list=[transforms.ContractingProcessSetup, transforms.ContractStatus],
    )

    assert output["contractingProcesses"][0]["summary"]["status"] == "active"
    assert output["contractingProcesses"][1]["summary"]["status"] == "active"

    # Currently no status at all as fits no status
    assert output["contractingProcesses"][2]["summary"].get("status") != "active"

    assert output["contractingProcesses"][3]["summary"]["status"] == "active"
    assert output["contractingProcesses"][4]["summary"]["status"] == "active"


def test_contract_status_closed():

    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "tender": {"status": "cancelled"},
        },
        {
            "ocid": "ocds-213czf-2",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "awards": [{"status": "cancelled"}],
            "tender": {"id": 1},
        },
        {
            "ocid": "ocds-213czf-3",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "contracts": [{"status": "cancelled"}],
            "tender": {"id": 1},
        },
        {
            "ocid": "ocds-213czf-4",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "contracts": [{"period": {"endDate": "2000-01-01"}}],
            "awards": [{"contractPeriod": {"endDate": "2000-01-01"}}],
            "tender": {"id": 1, "contractPeriod": {"endDate": "2000-01-01"}},
        },
        {
            "ocid": "ocds-213czf-5",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "contracts": [{"period": {"endDate": "3000-01-01"}}],
            "awards": [{"contractPeriod": {"endDate": "2000-01-01"}}],
            "tender": {"id": 1, "contractPeriod": {"endDate": "2000-01-01"}},
        },
        {
            "ocid": "ocds-213czf-6",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "contracts": [{"period": {"endDate": "2000-01-01"}}],
            "awards": [{"contractPeriod": {"endDate": "3000-01-01"}}],
            "tender": {"id": 1, "contractPeriod": {"endDate": "2000-01-01"}},
        },
        {
            "ocid": "ocds-213czf-7",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "contracts": [{"period": {"endDate": "2000-01-01"}}],
            "awards": [{"contractPeriod": {"endDate": "2000-01-01"}}],
            "tender": {"id": 1, "contractPeriod": {"endDate": "3000-01-01"}},
        },
    ]

    output = transforms.run_transforms(
        {},
        copy.deepcopy(releases),
        "1",
        transform_list=[transforms.ContractingProcessSetup, transforms.ContractStatus],
    )

    assert output["contractingProcesses"][0]["summary"]["status"] == "closed"
    assert output["contractingProcesses"][1]["summary"]["status"] == "closed"
    assert output["contractingProcesses"][2]["summary"]["status"] == "closed"
    assert output["contractingProcesses"][3]["summary"]["status"] == "closed"
    assert output["contractingProcesses"][4]["summary"]["status"] != "closed"
    assert output["contractingProcesses"][5]["summary"]["status"] != "closed"
    assert output["contractingProcesses"][6]["summary"]["status"] != "closed"


def test_procurment_process():

    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "tender": {"procurementMethod": "method", "procurementMethodDetails": "details"},
        }
    ]

    output = transforms.run_transforms(
        {},
        copy.deepcopy(releases),
        "1",
        transform_list=[transforms.ContractingProcessSetup, transforms.ProcurementProcess],
    )

    assert output["contractingProcesses"][0]["summary"]["tender"] == releases[0]["tender"]


def test_number_of_tenderers():

    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "tender": {"numberOfTenderers": 123},
        }
    ]

    output = transforms.run_transforms(
        {},
        copy.deepcopy(releases),
        "1",
        dict_cls=dict,
        transform_list=[transforms.ContractingProcessSetup, transforms.NumberOfTenderers],
    )

    assert output["contractingProcesses"][0]["summary"]["tender"]["numberOfTenderers"] == 123


def test_location():
    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "planning": {"project": {"locations": [{"description": "Mars"}]}},
        }
    ]

    output = transforms.run_transforms(
        {}, copy.deepcopy(releases), "1", dict_cls=dict, transform_list=[transforms.Location],
    )

    assert output["locations"] == [{"description": "Mars"}]


def test_location_from_item_location():
    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "items": [
                {
                    "id": "item1",
                    "deliveryLocation": {
                        "geometry": {"type": "Point", "coordinates": [51.751944, -1.257778]},
                        "uri": "http://www.geonames.org/2640729/oxford.html",
                    },
                }
            ],
        }
    ]

    output = transforms.run_transforms(
        {"infer_location": True},
        copy.deepcopy(releases),
        "1",
        dict_cls=dict,
        transform_list=[transforms.Location, transforms.LocationFromItems],
    )
    assert output["locations"] == [releases[0]["items"][0]["deliveryLocation"]]


def test_location_from_delivery_address():
    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "items": [
                {
                    "id": "item2",
                    "deliveryAddress": {
                        "postalCode": "OX1 1BX",
                        "countryName": "United Kingdom",
                        "streetAddress": "Town Hall, St Aldate's",
                        "region": "Oxfordshire",
                        "locality": "Oxford",
                    },
                }
            ],
        }
    ]

    output = transforms.run_transforms(
        {"infer_location": True},
        copy.deepcopy(releases),
        "1",
        dict_cls=dict,
        transform_list=[transforms.Location, transforms.LocationFromItems],
    )

    assert output["locations"] == [{"address": releases[0]["items"][0]["deliveryAddress"]}]


def test_location_multiple():
    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "items": [
                {
                    "id": "item1",
                    "deliveryLocation": {
                        "geometry": {"type": "Point", "coordinates": [51.751944, -1.257778]},
                        "uri": "http://www.geonames.org/2640729/oxford.html",
                    },
                    "deliveryAddress": {
                        "postalCode": "OX1 1BX",
                        "countryName": "United Kingdom",
                        "streetAddress": "Town Hall, St Aldate's",
                        "region": "Oxfordshire",
                        "locality": "Oxford",
                    },
                }
            ],
        }
    ]

    output = transforms.run_transforms(
        {"infer_location": True},
        copy.deepcopy(releases),
        "1",
        dict_cls=dict,
        transform_list=[transforms.Location, transforms.LocationFromItems],
    )

    assert output["locations"] == [
        releases[0]["items"][0]["deliveryLocation"],
        {"address": releases[0]["items"][0]["deliveryAddress"]},
    ]


def test_location_not_inferred():
    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "items": [
                {
                    "id": "item1",
                    "deliveryLocation": {
                        "geometry": {"type": "Point", "coordinates": [51.751944, -1.257778]},
                        "uri": "http://www.geonames.org/2640729/oxford.html",
                    },
                    "deliveryAddress": {
                        "postalCode": "OX1 1BX",
                        "countryName": "United Kingdom",
                        "streetAddress": "Town Hall, St Aldate's",
                        "region": "Oxfordshire",
                        "locality": "Oxford",
                    },
                }
            ],
        }
    ]

    output = transforms.run_transforms(
        {},
        copy.deepcopy(releases),
        "1",
        dict_cls=dict,
        transform_list=[transforms.Location, transforms.LocationFromItems],
    )

    assert "locations" not in output


def test_budget():
    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "planning": {"budget": {"amount": {"amount": "1000", "currency": "USD"}}},
        }
    ]

    output = transforms.run_transforms(
        {}, copy.deepcopy(releases), "1", dict_cls=dict, transform_list=[transforms.Budget],
    )
    assert output["budget"]["amount"] == releases[0]["planning"]["budget"]["amount"]


def test_budget_multiple():
    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "planning": {"budget": {"amount": {"amount": "1000", "currency": "USD"}}},
        },
        {
            "ocid": "ocds-213czf-2",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T06:07:08Z",
            "planning": {"budget": {"amount": {"amount": "1234", "currency": "USD"}}},
        },
    ]

    output = transforms.run_transforms(
        {}, copy.deepcopy(releases), "1", dict_cls=dict, transform_list=[transforms.Budget],
    )
    total = float(releases[0]["planning"]["budget"]["amount"]["amount"]) + float(
        releases[1]["planning"]["budget"]["amount"]["amount"]
    )
    assert output["budget"]["amount"]["amount"] == total
    assert output["budget"]["amount"]["currency"] == releases[0]["planning"]["budget"]["amount"]["currency"]


def test_budget_fail():
    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "planning": {"budget": {"amount": {"amount": "999", "currency": "USD"}}},
        },
        {
            "ocid": "ocds-213czf-2",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T06:07:08Z",
            "planning": {"budget": {"amount": {"amount": "6464", "currency": "EUR"}}},
        },
    ]

    output = transforms.run_transforms(
        {}, copy.deepcopy(releases), "1", dict_cls=dict, transform_list=[transforms.Budget],
    )
    # Different currencies could not be totalled
    assert "budget" not in output


def test_budget_approval():
    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "planning": {
                "documents": [
                    {"id": "doc1", "documentType": "projectPlan", "title": "A Document"},
                    {"id": "doc2", "documentType": "budgetApproval", "title": "Another Document"},
                ]
            },
        },
    ]

    output = transforms.run_transforms(
        {}, copy.deepcopy(releases), "1", dict_cls=dict, transform_list=[transforms.BudgetApproval],
    )
    assert output["documents"] == [releases[0]["planning"]["documents"][1]]


def test_purpose_one():
    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "planning": {"rationale": "We were hungry."},
        },
    ]

    output = transforms.run_transforms(
        {}, copy.deepcopy(releases), "1", dict_cls=dict, transform_list=[transforms.Purpose],
    )
    assert output["purpose"] == releases[0]["planning"]["rationale"]


def test_purpose_multiple():
    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "planning": {"rationale": "We were hungry."},
        },
        {
            "ocid": "ocds-213czf-2",
            "id": "2",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "planning": {"rationale": "There are never enough post-its."},
        },
    ]

    rationales = "<ocds-213czf-1> We were hungry.\n<ocds-213czf-2> There are never enough post-its.\n"

    output = transforms.run_transforms(
        {}, copy.deepcopy(releases), "1", dict_cls=dict, transform_list=[transforms.Purpose],
    )
    assert output["purpose"] == rationales


def test_needs_assessment():
    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "planning": {
                "documents": [
                    {"id": "doc1", "documentType": "needsAssessment", "title": "A Document"},
                    {"id": "doc2", "documentType": "budgetApproval", "title": "Another Document"},
                ]
            },
        },
    ]

    output = transforms.run_transforms(
        {"copy_documents_needsassessment": True},
        copy.deepcopy(releases),
        "1",
        dict_cls=dict,
        transform_list=[transforms.PurposeNeedsAssessment],
    )
    assert output["documents"] == [releases[0]["planning"]["documents"][0]]


def test_description_one():
    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "planning": {"project": {"description": "A project description"}},
        },
    ]

    output = transforms.run_transforms(
        {}, copy.deepcopy(releases), "1", dict_cls=dict, transform_list=[transforms.Description],
    )
    assert output["description"] == releases[0]["planning"]["project"]["description"]


def test_description_multiple():
    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "planning": {"project": {"description": "A project description"}},
        },
        {
            "ocid": "ocds-213czf-2",
            "id": "2",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "planning": {"project": {"description": "Another project description"}},
        },
    ]

    rationales = "<ocds-213czf-1> A project description\n<ocds-213czf-2> Another project description\n"

    output = transforms.run_transforms(
        {}, copy.deepcopy(releases), "1", dict_cls=dict, transform_list=[transforms.Description],
    )
    assert output["description"] == rationales


def test_description_tender():
    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "tender": {"description": "A project description"},
        },
    ]

    output = transforms.run_transforms(
        {"description_from_tender": True},
        copy.deepcopy(releases),
        "1",
        dict_cls=dict,
        transform_list=[transforms.Description, transforms.DescriptionTender],
    )
    assert output["description"] == releases[0]["tender"]["description"]


def test_description_not_tender():
    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "planning": {"project": {"description": "Another project description"}},
            "tender": {"description": "A project description"},
        },
    ]

    output = transforms.run_transforms(
        {"description_from_tender": True},
        copy.deepcopy(releases),
        "1",
        dict_cls=dict,
        transform_list=[transforms.Description, transforms.DescriptionTender],
    )
    assert output["description"] == releases[0]["planning"]["project"]["description"]


def test_description_not_project():
    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "tender": {"description": "A project description"},
        },
    ]

    output = transforms.run_transforms(
        {},
        copy.deepcopy(releases),
        "1",
        dict_cls=dict,
        transform_list=[transforms.Description, transforms.DescriptionTender],
    )
    assert "description" not in output

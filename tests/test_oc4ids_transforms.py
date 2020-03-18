import copy
import json

from ocdskit import oc4ids
from tests import read


def test_initial_tranform_state():
    releases = json.loads(read("release-package_additional-contact-points.json"))["releases"]
    transform_state = oc4ids.InitialTransformState(releases, "1")
    assert len(transform_state.compiled_releases) == 1
    assert len(transform_state.releases_by_ocid["ocds-213czf-1"]) == 2


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
    output = oc4ids.run_transforms({}, releases, "1")
    assert output["parties"] == releases[0]["parties"]


def test_run_all_release_package():
    releases_package_1 = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "parties": [{"id": "1", "roles": ["publicAuthority"]}],
        }
    ]
    releases_package_2 = [
        {
            "ocid": "ocds-213czf-2",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "parties": [{"id": "2", "name": "a", "roles": ["publicAuthority"]}],
        }
    ]

    release_packages = [{"uri": "example.com", "releases": releases_package_1},
                        {"uri": "example.com", "releases": releases_package_2}]

    output = oc4ids.run_transforms({}, release_packages, "1")

    assert len(output["contractingProcesses"]) == 2
    assert len(output["parties"]) == 2
    assert output["contractingProcesses"][0]['releases'] == [
        {'url': 'example.com#1', 'date': '2001-02-03T04:05:06Z', 'tag': 'planning'}
    ]


def test_public_authority_role():
    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "parties": [
                {"id": "1", "name": "a", "roles": ["publicAuthority"]},
                {"id": "2", "name": "b", "roles": ["publicAuthority"]},
            ],
        }
    ]

    output = oc4ids._run_transforms(releases, "1", transforms=[oc4ids.public_authority_role])
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

    output = oc4ids._run_transforms(releases, "1", transforms=[oc4ids.public_authority_role])
    assert len(output["parties"]) == 1


def test_duplicate_public_authority_role():

    # Match on identifier
    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "parties": [{"id": "a", "roles": ["publicAuthority"], "identifier": {"id": "a", "scheme": "b"}}],
        },
        {
            "ocid": "ocds-213czf-2",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "parties": [{"id": "a", "roles": ["publicAuthority"], "identifier": {"id": "a", "scheme": "b"}}],
        },
    ]

    output = oc4ids._run_transforms(releases, "1", transforms=[oc4ids.public_authority_role])
    assert len(output["parties"]) == 1
    assert output["parties"][0]["id"] == "b-a"

    # No match on identifier
    releases[0]["parties"][0]["identifier"]["id"] = "b"

    output = oc4ids._run_transforms(releases, "1", transforms=[oc4ids.public_authority_role])

    assert len(output["parties"]) == 2
    print(output["parties"])
    assert output["parties"][0]["id"] == "b-b"
    assert output["parties"][1]["id"] == "b-a"

    # Match on name
    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "parties": [{"id": "a", "name": "org 1", "roles": ["publicAuthority"]}],
        },
        {
            "ocid": "ocds-213czf-2",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "parties": [{"id": "a", "name": "org 1", "roles": ["publicAuthority"]}],
        },
    ]

    output = oc4ids._run_transforms(releases, "1", transforms=[oc4ids.public_authority_role])
    assert len(output["parties"]) == 1
    assert output["parties"][0]["id"] == "1"

    # No match on name
    releases[0]["parties"][0]["name"] = "org 2"

    output = oc4ids._run_transforms(releases, "1", transforms=[oc4ids.public_authority_role])
    assert len(output["parties"]) == 2
    # Generated autoincrement party ids
    assert output["parties"][0]["id"] == "1"
    assert output["parties"][1]["id"] == "2"

    # Match on name but different address
    releases[0]["parties"][0]["name"] = "org 1"
    releases[0]["parties"][0]["address"] = {"streetAddress": "1 the street"}

    output = oc4ids._run_transforms(releases, "1", transforms=[oc4ids.public_authority_role])
    assert len(output["parties"]) == 2
    assert output["parties"][0]["id"] == "1"
    assert output["parties"][1]["id"] == "2"

    # Match on name and address
    releases[1]["parties"][0]["address"] = {"streetAddress": "1 the street"}
    output = oc4ids._run_transforms(releases, "1", transforms=[oc4ids.public_authority_role])
    assert len(output["parties"]) == 1
    assert output["parties"][0]["id"] == "1"

    # all roles if match
    releases[1]["parties"][0]["roles"].append("some role")
    releases[1]["parties"][0]["roles"].append("some other role")

    output = oc4ids._run_transforms(releases, "1", transforms=[oc4ids.public_authority_role])
    assert len(output["parties"]) == 1

    assert len(output["parties"][0]["roles"]) == 3
    assert output["parties"][0]["id"] == "1"


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

    output = oc4ids._run_transforms(releases, "1", transforms=[oc4ids.buyer_role])

    assert "publicAuthority" in output["parties"][0]["roles"]
    assert "buyer" in output["parties"][0]["roles"]


def test_sector():
    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "planning": {
                "project": {"sector": {"scheme": "COFOG", "description": "Road transportation", "id": "04.5.1"}}
            },
        }
    ]

    output = oc4ids._run_transforms(releases, "1", transforms=[oc4ids.sector])
    assert output["sector"] == ["COFOG-04.5.1"]

    # 2 contracting processes but same sector
    releases.append(
        {
            "ocid": "ocds-213czf-2",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "planning": {
                "project": {"sector": {"scheme": "COFOG", "description": "Road transportation", "id": "04.5.1"}}
            },
        }
    )

    output = oc4ids._run_transforms(releases, "1", transforms=[oc4ids.sector])
    assert output["sector"] == ["COFOG-04.5.1"]

    # 2 contracting processes but differnt sector
    releases[1]["planning"]["project"]["sector"]["id"] = "2"
    output = oc4ids._run_transforms(releases, "1", transforms=[oc4ids.sector])
    assert set(output["sector"]) == set(["COFOG-04.5.1", "COFOG-2"])


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

    output = oc4ids._run_transforms(releases, "1", transforms=[oc4ids.additional_classifications])
    assert output["additionalClassifications"] == [{"scheme": "a", "id": "1"}]

    # same classification
    releases.append(
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "planning": {"project": {"additionalClassifications": [{"scheme": "a", "id": "1"}]}},
        }
    )

    output = oc4ids._run_transforms(releases, "1", transforms=[oc4ids.additional_classifications])
    assert output["additionalClassifications"] == [{"scheme": "a", "id": "1"}]

    # new classification
    releases.append(
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "planning": {"project": {"additionalClassifications": [{"scheme": "a", "id": "2"}]}},
        }
    )
    output = oc4ids._run_transforms(releases, "1", transforms=[oc4ids.additional_classifications])
    assert output["additionalClassifications"] == [{"scheme": "a", "id": "1"}, {"scheme": "a", "id": "2"}]


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

    output = oc4ids._run_transforms(releases, "1", transforms=[oc4ids.title])
    assert output["title"] == releases[0]["planning"]["project"]["title"]

    # clashing titles give warning and no output
    releases.append(
        {
            "ocid": "ocds-213czf-2",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "planning": {"project": {"title": "b title"}},
        }
    )

    output = oc4ids._run_transforms(releases, "1", transforms=[oc4ids.title])
    assert "title" not in output


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

    output = oc4ids._run_transforms(releases, "1", transforms=[oc4ids.title, oc4ids.title_from_tender])
    assert output["title"] == releases[0]["tender"]["title"]

    releases.append(
        {
            "ocid": "ocds-213czf-2",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "tender": {"title": "b title"},
        }
    )

    output = oc4ids._run_transforms(releases, "1", transforms=[oc4ids.title, oc4ids.title_from_tender])

    assert output["title"] == "<ocds-213czf-1> a title\n<ocds-213czf-2> b title\n"

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

    output = oc4ids._run_transforms(releases, "1", transforms=[oc4ids.title, oc4ids.title_from_tender])

    assert output["title"] == releases[0]["planning"]["project"]["title"]


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

    output = oc4ids._run_transforms(
        copy.deepcopy(releases), "1", transforms=[oc4ids.contracting_process_setup]
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
          "embeddedReleases": [
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
          "embeddedReleases": [
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

    output = oc4ids._run_transforms(
        copy.deepcopy(release_packages), "1", transforms=[oc4ids.contracting_process_setup]
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
            "tender": {"procuringEntity": {"id": "1"}},
            "parties": [{"id": "1", "roles": ["procuringEntity"]}],
        },
    ]

    output = oc4ids._run_transforms(
        copy.deepcopy(releases), "1", transforms=[oc4ids.contracting_process_setup, oc4ids.procuring_entity],
    )

    assert output["parties"] == releases[0]["parties"]
    assert output["contractingProcesses"][0]["summary"]["tender"] == releases[0]["tender"]

    # with identifier no duplicate party id
    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "parties": [{"id": "1", "roles": ["procuringEntity"], "identifier": {"id": "a", "scheme": "a"}}],
        },
    ]
    output = oc4ids._run_transforms(
        copy.deepcopy(releases), "1", transforms=[oc4ids.contracting_process_setup, oc4ids.procuring_entity],
    )

    assert output["parties"][0]["id"] == "1"
    assert output["contractingProcesses"][0]["summary"]["tender"]["procuringEntity"]["id"] == "1"

    # with identifier and duplicate party id
    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "parties": [{"id": "1", "roles": ["procuringEntity"], "identifier": {"id": "a", "scheme": "a"}}],
        },
        {
            "ocid": "ocds-213czf-2",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "parties": [{"id": "1", "roles": ["procuringEntity"], "identifier": {"id": "a", "scheme": "a"}}],
        },
    ]
    output = oc4ids._run_transforms(
        copy.deepcopy(releases), "1", transforms=[oc4ids.contracting_process_setup, oc4ids.procuring_entity],
    )

    assert output["parties"][0]["id"] == "a-a"
    assert output["contractingProcesses"][0]["summary"]["tender"]["procuringEntity"]["id"] == "a-a"

    # with genderated id
    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "parties": [{"id": "1", "name": "org1", "roles": ["procuringEntity"]}],
        },
        {
            "ocid": "ocds-213czf-2",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "parties": [{"id": "1", "name": "org2", "roles": ["procuringEntity"]}],
        },
    ]
    output = oc4ids._run_transforms(
        copy.deepcopy(releases), "1", transforms=[oc4ids.contracting_process_setup, oc4ids.procuring_entity],
    )

    assert output["parties"][0]["id"] == "1"
    assert output["parties"][1]["id"] == "2"
    assert output["contractingProcesses"][0]["summary"]["tender"]["procuringEntity"]["id"] == "1"
    assert output["contractingProcesses"][1]["summary"]["tender"]["procuringEntity"]["id"] == "2"


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

    output = oc4ids._run_transforms(
        copy.deepcopy(releases),
        "1",
        transforms=[oc4ids.contracting_process_setup, oc4ids.administrative_entity],
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

    output = oc4ids._run_transforms(
        copy.deepcopy(releases),
        "1",
        transforms=[oc4ids.contracting_process_setup, oc4ids.administrative_entity],
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

    output = oc4ids._run_transforms(
        copy.deepcopy(releases), "1", transforms=[oc4ids.contracting_process_setup, oc4ids.contract_status],
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

    output = oc4ids._run_transforms(
        copy.deepcopy(releases), "1", transforms=[oc4ids.contracting_process_setup, oc4ids.contract_status],
    )

    assert output["contractingProcesses"][0]["summary"]["status"] == "active"
    assert output["contractingProcesses"][1]["summary"]["status"] == "active"
    assert output["contractingProcesses"][2]["summary"]["status"] != "active"

    # Currently no status at all as fits no status

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

    output = oc4ids._run_transforms(
        copy.deepcopy(releases), "1", transforms=[oc4ids.contracting_process_setup, oc4ids.contract_status],
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

    output = oc4ids._run_transforms(
        copy.deepcopy(releases),
        "1",
        transforms=[oc4ids.contracting_process_setup, oc4ids.procurement_process],
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

    output = oc4ids._run_transforms(
        copy.deepcopy(releases),
        "1",
        transforms=[oc4ids.contracting_process_setup, oc4ids.number_of_tenderers],
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

    output = oc4ids._run_transforms(copy.deepcopy(releases), "1", transforms=[oc4ids.location],)

    assert output["locations"] == [{"description": "Mars"}]


def test_location_multiple_releases():
    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "planning": {"project": {"locations": [{"description": "Mars"}, {"description": "Jupiter"}]}},
        },
        {
            "ocid": "ocds-213czf-2",
            "id": "2",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "planning": {"project": {"locations": [{"description": "Earth"}]}},
        },
    ]

    output = oc4ids._run_transforms(copy.deepcopy(releases), "1", transforms=[oc4ids.location],)

    assert output["locations"] == [{"description": "Mars"}, {"description": "Jupiter"}, {"description": "Earth"}]


def test_location_from_item_location():
    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "tender": {
                "items": [
                    {
                        "id": "item1",
                        "deliveryLocation": {
                            "geometry": {"type": "Point", "coordinates": [51.751944, -1.257778]},
                            "uri": "http://www.geonames.org/2640729/oxford.html",
                        },
                    }
                ],
            },
        }
    ]

    output = oc4ids._run_transforms(
        copy.deepcopy(releases), "1", transforms=[oc4ids.location, oc4ids.location_from_items],
    )
    assert output["locations"] == [releases[0]["tender"]["items"][0]["deliveryLocation"]]


def test_location_from_delivery_address():
    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "tender": {
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
            },
        }
    ]

    output = oc4ids._run_transforms(
        copy.deepcopy(releases), "1", transforms=[oc4ids.location, oc4ids.location_from_items],
    )

    assert output["locations"] == [{"address": releases[0]["tender"]["items"][0]["deliveryAddress"]}]


def test_location_multiple():
    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "tender": {
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
            },
        }
    ]

    output = oc4ids._run_transforms(
        copy.deepcopy(releases), "1", transforms=[oc4ids.location, oc4ids.location_from_items],
    )

    assert output["locations"] == [
        releases[0]["tender"]["items"][0]["deliveryLocation"],
        {"address": releases[0]["tender"]["items"][0]["deliveryAddress"]},
    ]


def test_location_not_inferred():
    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "tender": {
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
            },
        }
    ]

    output = oc4ids._run_transforms(copy.deepcopy(releases), "1", transforms=[oc4ids.location],)

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

    output = oc4ids._run_transforms(copy.deepcopy(releases), "1", transforms=[oc4ids.budget],)
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

    output = oc4ids._run_transforms(copy.deepcopy(releases), "1", transforms=[oc4ids.budget],)
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

    output = oc4ids._run_transforms(copy.deepcopy(releases), "1", transforms=[oc4ids.budget],)
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

    output = oc4ids._run_transforms(copy.deepcopy(releases), "1", transforms=[oc4ids.budget_approval],)
    assert output["documents"] == [releases[0]["planning"]["documents"][1]]

    # duplicate document id in different process, auto increment new doc ids.
    releases.append(
        {
            "ocid": "ocds-213czf-2",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "planning": {
                "documents": [{"id": "doc2", "documentType": "budgetApproval", "title": "Another Another Document"}]
            },
        }
    )

    output = oc4ids._run_transforms(copy.deepcopy(releases), "1", transforms=[oc4ids.budget_approval],)

    assert len(output["documents"]) == 2
    assert output["documents"][0]["id"] == "1"
    assert output["documents"][1]["id"] == "2"


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

    output = oc4ids._run_transforms(copy.deepcopy(releases), "1", transforms=[oc4ids.purpose],)
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

    output = oc4ids._run_transforms(copy.deepcopy(releases), "1", transforms=[oc4ids.purpose],)
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

    output = oc4ids._run_transforms(
        copy.deepcopy(releases), "1", transforms=[oc4ids.purpose_needs_assessment],
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

    output = oc4ids._run_transforms(copy.deepcopy(releases), "1", transforms=[oc4ids.description],)
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
            "planning": {"project": {"description": "A project description"}},
        },
    ]

    output = oc4ids._run_transforms(copy.deepcopy(releases), "1", transforms=[oc4ids.description],)
    assert output["description"] == releases[0]["planning"]["project"]["description"]

    # contraditing descriptions
    releases[0]["planning"]["project"]["description"] = "another description"

    output = oc4ids._run_transforms(copy.deepcopy(releases), "1", transforms=[oc4ids.description],)

    assert "description" not in output


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

    output = oc4ids._run_transforms(
        copy.deepcopy(releases), "1", transforms=[oc4ids.description, oc4ids.description_tender],
    )
    assert output["description"] == releases[0]["tender"]["description"]

    releases.append(
        {
            "ocid": "ocds-213czf-2",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "tender": {"description": "A new project description"},
        }
    )
    output = oc4ids._run_transforms(
        copy.deepcopy(releases), "1", transforms=[oc4ids.description, oc4ids.description_tender],
    )
    assert (
        output["description"] == "<ocds-213czf-1> A project description\n<ocds-213czf-2> A new project description\n"
    )


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

    output = oc4ids._run_transforms(
        copy.deepcopy(releases), "1", transforms=[oc4ids.description, oc4ids.description_tender],
    )
    assert output["description"] == releases[0]["planning"]["project"]["description"]


def test_environmental_impact():
    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "planning": {
                "documents": [
                    {"id": "doc1", "documentType": "environmentalImpact", "title": "A Document"},
                    {"id": "doc2", "documentType": "budgetApproval", "title": "Another Document"},
                ]
            },
        },
    ]

    output = oc4ids._run_transforms(copy.deepcopy(releases), "1", transforms=[oc4ids.environmental_impact],)
    assert output["documents"] == [releases[0]["planning"]["documents"][0]]


def test_land_and_settlement_impact():
    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "planning": {
                "documents": [
                    {"id": "doc1", "documentType": "environmentalImpact", "title": "A Document"},
                    {"id": "doc2", "documentType": "landAndSettlementImpact", "title": "Another Document"},
                ]
            },
        },
    ]

    output = oc4ids._run_transforms(
        copy.deepcopy(releases), "1", transforms=[oc4ids.land_and_settlement_impact],
    )
    assert output["documents"] == [releases[0]["planning"]["documents"][1]]


def test_project_scope():
    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "planning": {
                "documents": [
                    {"id": "doc1", "documentType": "projectScope", "title": "A Document"},
                    {"id": "doc2", "documentType": "budgetApproval", "title": "Another Document"},
                ]
            },
        },
    ]

    output = oc4ids._run_transforms(copy.deepcopy(releases), "1", transforms=[oc4ids.project_scope],)
    assert output["documents"] == [releases[0]["planning"]["documents"][0]]


def test_project_scope_summary():
    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "tender": {
                "description": "c",
                "items": [{"description": "Some item"}],
                "milestones": [{"description": "Some milestone"}, {"description": "Another milestone"}],
            },
        }
    ]

    output = oc4ids._run_transforms(
        releases, "1", transforms=[oc4ids.contracting_process_setup, oc4ids.project_scope_summary],
    )

    assert "items" in output["contractingProcesses"][0]["summary"]["tender"]
    assert "milestones" in output["contractingProcesses"][0]["summary"]["tender"]
    assert output["contractingProcesses"][0]["summary"]["tender"]["items"] == releases[0]["tender"]["items"]
    assert output["contractingProcesses"][0]["summary"]["tender"]["milestones"] == releases[0]["tender"]["milestones"]


def test_funders_budget():
    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "parties": [
                {
                    "id": "GB-LAC-E09000003-557",
                    "name": "London Borough of Barnet - Transport Services",
                    "details": "This is just a test.",
                },
                {"id": "GB-GOV-23", "name": "Department for Transport", "details": "This is also a test."},
            ],
            "planning": {
                "budget": {
                    "id": "1",
                    "description": "Multi-source budget, see budget breakdown for details.",
                    "amount": {"amount": 300000, "currency": "GBP"},
                    "budgetBreakdown": [
                        {
                            "sourceParty": {
                                "id": "GB-LAC-E09000003-557",
                                "name": "London Borough of Barnet - Transport Services",
                            },
                            "period": {"startDate": "2016-01-01T00:00:00Z", "endDate": "2016-12-31T23:59:59Z"},
                            "id": "001",
                            "description": "Budget contribution from the local government",
                            "amount": {"amount": 150000, "currency": "GBP"},
                        },
                        {
                            "sourceParty": {"id": "GB-GOV-23", "name": "Department for Transport"},
                            "period": {"startDate": "2016-01-01T00:00:00Z", "endDate": "2016-12-31T23:59:59Z"},
                            "id": "002",
                            "description": "Budget contribution from the national government",
                            "amount": {"amount": 150000, "currency": "GBP"},
                        },
                    ],
                }
            },
        }
    ]

    output = oc4ids._run_transforms(copy.deepcopy(releases), "1", transforms=[oc4ids.funding_sources],)

    assert output["parties"][0]["id"] == "GB-LAC-E09000003-557"
    assert output["parties"][0]["details"] == "This is just a test."
    assert "funder" in output["parties"][0]["roles"]


def test_funders():
    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "parties": [
                {
                    "id": "GB-LAC-E09000003-557",
                    "name": "London Borough of Barnet - Transport Services",
                    "details": "This is just a test.",
                    "roles": ["funder"],
                },
                {
                    "id": "GB-GOV-23",
                    "name": "Department for Transport",
                    "details": "This is also a test.",
                    "roles": ["funder"],
                },
            ],
        }
    ]

    output = oc4ids._run_transforms(copy.deepcopy(releases), "1", transforms=[oc4ids.funding_sources],)

    assert output["parties"][0]["id"] == "GB-LAC-E09000003-557"
    assert output["parties"][0]["details"] == "This is just a test."
    assert "funder" in output["parties"][0]["roles"]


def test_cost_estimate():

    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "tender": {"status": "planning", "value": {"amount": 1}},
        },
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2100-02-03T04:05:06Z",
            "tender": {"status": "planning", "value": {"amount": 10}},
        },
    ]

    output = oc4ids._run_transforms(
        releases, "1", transforms=[oc4ids.contracting_process_setup, oc4ids.cost_estimate],
    )

    assert output["contractingProcesses"][0]["summary"]["tender"]["costEstimate"] == {"amount": 10}

    # reverse releases
    releases[0]["date"], releases[1]["date"] = releases[1]["date"], releases[0]["date"]

    output = oc4ids._run_transforms(
        releases, "1", transforms=[oc4ids.contracting_process_setup, oc4ids.cost_estimate],
    )

    assert output["contractingProcesses"][0]["summary"]["tender"]["costEstimate"] == {"amount": 1}

    releases.append(
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2200-02-03T04:05:06Z",
            "tender": {"status": "active", "value": {"amount": 100}},
        }
    )

    # last releases is not planning
    output = oc4ids._run_transforms(
        releases, "1", transforms=[oc4ids.contracting_process_setup, oc4ids.cost_estimate],
    )
    assert output["contractingProcesses"][0]["summary"]["tender"]["costEstimate"] == {"amount": 1}


def test_contract_title():

    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "contracts": [{"title": "a"}],
            "awards": [{"title": "b"}],
            "tender": {"title": "c"},
        }
    ]

    output = oc4ids._run_transforms(
        releases, "1", transforms=[oc4ids.contracting_process_setup, oc4ids.contract_title],
    )

    assert output["contractingProcesses"][0]["summary"]["title"] == "a"

    # with second contract we use tender title
    releases[0]["contracts"].append({"title": "a"})

    output = oc4ids._run_transforms(
        releases, "1", transforms=[oc4ids.contracting_process_setup, oc4ids.contract_title],
    )

    assert output["contractingProcesses"][0]["summary"]["title"] == "c"

    # if we remove contracts we use award title
    releases[0].pop("contracts")

    output = oc4ids._run_transforms(
        releases, "1", transforms=[oc4ids.contracting_process_setup, oc4ids.contract_title],
    )

    assert output["contractingProcesses"][0]["summary"]["title"] == "b"


def test_supplier():

    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "parties": [
                {"id": "a", "name": "A", "roles": ["supplier"]},
                {"id": "b", "name": "B", "roles": ["supplier"]},
            ],
        }
    ]

    output = oc4ids._run_transforms(
        releases, "1", transforms=[oc4ids.contracting_process_setup, oc4ids.suppliers],
    )

    assert output["parties"] == releases[0]["parties"]

    assert output["contractingProcesses"][0]["summary"]["suppliers"] == [
        {"id": "a", "name": "A"},
        {"id": "b", "name": "B"},
    ]


def test_contract_value():

    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "awards": [
                {"value": {"amount": 10, "currency": "USD"}},
                {"value": {"amount": 10, "currency": "USD"}},
                {"value": {"amount": 10, "currency": "USD"}},
            ],
        }
    ]

    output = oc4ids._run_transforms(
        releases, "1", transforms=[oc4ids.contracting_process_setup, oc4ids.contract_price],
    )

    assert output["contractingProcesses"][0]["summary"]["contractValue"] == {"amount": 30, "currency": "USD"}

    # change an currency
    releases[0]["awards"][1]["value"]["currency"] = "CAD"

    output = oc4ids._run_transforms(
        releases, "1", transforms=[oc4ids.contracting_process_setup, oc4ids.contract_price],
    )

    assert "contractValue" not in output["contractingProcesses"][0]["summary"]


def test_contracting_process_description():

    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "contracts": [{"description": "a", "items": [{"description": "item_a"}]}],
            "awards": [{"description": "b", "items": [{"description": "item_b"}]}],
            "tender": {"description": "c", "items": [{"description": "item_c"}]},
        }
    ]

    output = oc4ids._run_transforms(
        releases, "1", transforms=[oc4ids.contracting_process_setup, oc4ids.contract_process_description],
    )

    assert output["contractingProcesses"][0]["summary"]["description"] == "a"

    # with no contract description we do not use contract description but item description
    releases[0]["contracts"][0].pop("description")

    output = oc4ids._run_transforms(
        releases, "1", transforms=[oc4ids.contracting_process_setup, oc4ids.contract_process_description],
    )

    assert output["contractingProcesses"][0]["summary"]["description"] == "item_a"

    # with no contracts we use awards
    releases[0].pop("contracts")

    output = oc4ids._run_transforms(
        releases, "1", transforms=[oc4ids.contracting_process_setup, oc4ids.contract_process_description],
    )

    assert output["contractingProcesses"][0]["summary"]["description"] == "b"

    # with no award description use award item
    releases[0]["awards"][0].pop("description")

    output = oc4ids._run_transforms(
        releases, "1", transforms=[oc4ids.contracting_process_setup, oc4ids.contract_process_description],
    )

    assert output["contractingProcesses"][0]["summary"]["description"] == "item_b"

    # with second award item nothing is populated

    releases[0]["awards"][0]["items"].append({"description": "item_b"})

    output = oc4ids._run_transforms(
        releases, "1", transforms=[oc4ids.contracting_process_setup, oc4ids.contract_process_description],
    )

    assert "description" not in output["contractingProcesses"][0]["summary"]

    # with a second award uses tender
    releases[0]["awards"].append({"description": "b"})

    output = oc4ids._run_transforms(
        releases, "1", transforms=[oc4ids.contracting_process_setup, oc4ids.contract_process_description],
    )

    assert output["contractingProcesses"][0]["summary"]["description"] == "c"

    # with no tender description use items
    releases[0]["tender"].pop("description")

    output = oc4ids._run_transforms(
        releases, "1", transforms=[oc4ids.contracting_process_setup, oc4ids.contract_process_description],
    )

    assert output["contractingProcesses"][0]["summary"]["description"] == "item_c"

    # with second tender item we do not have a viable description
    releases[0]["tender"]["items"].append({"description": "item_c"})

    output = oc4ids._run_transforms(
        releases, "1", transforms=[oc4ids.contracting_process_setup, oc4ids.contract_process_description],
    )

    assert "description" not in output["contractingProcesses"][0]["summary"]


def test_contracting_period():

    releases = [
        {
            "ocid": "ocds-213czf-4",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "awards": [
                {"contractPeriod": {"startDate": "2000-01-01", "endDate": "3000-02-01"}},
                {"contractPeriod": {"startDate": "1999-01-01", "endDate": "3000-01-01"}},
            ],
            "tender": {"contractPeriod": {"startDate": "2100-01-01", "endDate": "2200-01-01"}},
        }
    ]

    output = oc4ids._run_transforms(
        releases, "1", transforms=[oc4ids.contracting_process_setup, oc4ids.contract_period],
    )

    assert output["contractingProcesses"][0]["summary"]["contractPeriod"] == {
        "startDate": "1999-01-01",
        "endDate": "3000-02-01",
    }

    # remove awards so we get tender contract period
    releases[0].pop("awards")

    output = oc4ids._run_transforms(
        releases, "1", transforms=[oc4ids.contracting_process_setup, oc4ids.contract_period],
    )

    assert output["contractingProcesses"][0]["summary"]["contractPeriod"] == releases[0]["tender"]["contractPeriod"]


def test_final_audit():
    releases = [
        {
            "ocid": "ocds-213czf-1",
            "id": "1",
            "tag": "planning",
            "date": "2001-02-03T04:05:06Z",
            "contracts": [
                {
                    "implementation": {
                        "documents": [
                            {"id": "doc1", "documentType": "finalAudit", "title": "A Document"},
                            {"id": "doc2", "documentType": "budgetApproval", "title": "Another Document"},
                        ]
                    },
                },
                {
                    "implementation": {
                        "documents": [
                            {"id": "doc3", "documentType": "finalAudit", "title": "B Document"},
                            {"id": "doc4", "documentType": "projectScope", "title": "Yet another Document"},
                        ]
                    },
                },
            ],
        },
    ]

    output = oc4ids._run_transforms(copy.deepcopy(releases), "1", transforms=[oc4ids.final_audit],)
    assert output["documents"] == [
        releases[0]["contracts"][0]["implementation"]["documents"][0],
        releases[0]["contracts"][1]["implementation"]["documents"][0],
    ]

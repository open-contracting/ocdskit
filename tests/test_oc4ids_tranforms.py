import json
import copy

import ocdskit.oc4ids_transforms as transforms
from tests import read


def test_initial_tranform_state():
    releases = json.loads(read('release-package_additional-contact-points.json'))['releases']
    initial_transform = transforms.InitialTransformState({}, releases, '1', compiled_releases=None)
    assert len(initial_transform.compiled_releases) == 1


def test_run_all():
    releases = [
        {"ocid":"ocds-213czf-1",
         "id":"1",
         "tag":"planning",
         "date":"2001-02-03T04:05:06Z",
         "parties":[{"id": "1", "roles": ["publicAuthority"]}]
        }
    ]
    output = transforms.run_transforms({}, releases, '1')
    assert output == {'id': '1', 'parties': [{'id': '1', 'roles': ['publicAuthority']}]}


def test_public_authority_role():
    releases = [
        {"ocid":"ocds-213czf-1",
         "id":"1",
         "tag":"planning",
         "date":"2001-02-03T04:05:06Z",
         "parties":[{"id": "1", "roles": ["publicAuthority"]}, 
                    {"id": "2", "roles": ["publicAuthority"]}]
        }
    ]

    initial_transform = transforms.InitialTransformState({}, releases, '1', compiled_releases=None)
    transform = transforms.PublicAuthorityRole([initial_transform])
    assert transform.success
    assert transform.output['parties'] == releases[0]['parties']

    releases = [
        {"ocid":"ocds-213czf-1",
         "id":"1",
         "tag":"planning",
         "date":"2001-02-03T04:05:06Z",
         "parties":[{"id": "1", "roles": ["publicAuthority"]}, 
                    {"id": "2", "roles": ["buyer"]}]
        }
    ]

    initial_transform = transforms.InitialTransformState({}, releases, '1', compiled_releases=None)
    transform = transforms.PublicAuthorityRole([initial_transform])
    assert transform.success
    assert len(transform.output['parties']) == 1


def test_buyer_role():
    releases = [
        {"ocid":"ocds-213czf-1",
         "id":"1",
         "tag":"planning",
         "date":"2001-02-03T04:05:06Z",
         "parties":[{"id": "1", "roles": ["buyer"]}]
        }
    ]

    initial_transform = transforms.InitialTransformState({}, copy.deepcopy(releases), '1', compiled_releases=None)
    transform = transforms.BuyerRole([initial_transform])

    # No config to say to convert buyers
    assert 'parties' not in transform.output
    assert transform.success

    initial_transform = transforms.InitialTransformState({'copy_buyer_role': True},
                                                         copy.deepcopy(releases), 
                                                         '1', 
                                                         compiled_releases=None)
    transform = transforms.BuyerRole([initial_transform])

    assert transform.success
    assert "publicAuthority" in transform.output['parties'][0]['roles']
    assert "buyer" in transform.output['parties'][0]['roles']


def test_sector():
    releases = [
        {"ocid":"ocds-213czf-1",
         "id":"1",
         "tag":"planning",
         "date":"2001-02-03T04:05:06Z",
         "planning": {"project": {"sector": "a"}},
        }
    ]

    initial_transform = transforms.InitialTransformState({}, copy.deepcopy(releases), '1', compiled_releases=None)
    transform = transforms.Sector([initial_transform])
    assert transform.success
    assert transform.output['sector'] == 'a'


def test_additional_classifications():
    releases = [
        {"ocid":"ocds-213czf-1",
         "id":"1",
         "tag":"planning",
         "date":"2001-02-03T04:05:06Z",
         "planning": {"project": {"additionalClassifications": [{"scheme": "a", "id": "1"}]}},
        }
    ]

    initial_transform = transforms.InitialTransformState({}, copy.deepcopy(releases), '1', compiled_releases=None)
    transform = transforms.AdditionalClassifications([initial_transform])
    assert transform.success
    assert transform.output['additionalClassifications'] == [{"scheme": "a", "id": "1"}]


def test_title():
    releases = [
        {"ocid":"ocds-213czf-1",
         "id":"1",
         "tag":"planning",
         "date":"2001-02-03T04:05:06Z",
         "planning": {"project": {"title": "a title"}},
        }
    ]

    initial_transform = transforms.InitialTransformState({}, copy.deepcopy(releases), '1', compiled_releases=None)
    transform = transforms.Title([initial_transform])
    assert transform.success
    assert transform.output['title'] == "a title"


def test_title_from_tender():
    releases = [
        {"ocid":"ocds-213czf-1",
         "id":"1",
         "tag":"planning",
         "date":"2001-02-03T04:05:06Z",
         "tender": {"title": "a title"},
        }
    ]

    initial_transform = transforms.InitialTransformState({'use_tender_title': True}, copy.deepcopy(releases), '1', compiled_releases=None)
    title_transform = transforms.Title([initial_transform])
    transform = transforms.TitleFromTender([initial_transform, title_transform])
    assert transform.success
    assert transform.output['title'] == "a title"

    releases = [
        {"ocid":"ocds-213czf-1",
         "id":"1",
         "tag":"planning",
         "date":"2001-02-03T04:05:06Z",
         "planning": {"project": {"title": "a title"}},
         "tender": {"title": "a non used title"},
        }
    ]

    initial_transform = transforms.InitialTransformState({'use_tender_title': True}, copy.deepcopy(releases), '1', compiled_releases=None)
    title_transform = transforms.Title([initial_transform])
    transform = transforms.TitleFromTender([initial_transform, title_transform])
    assert transform.success
    assert transform.output['title'] == "a title"

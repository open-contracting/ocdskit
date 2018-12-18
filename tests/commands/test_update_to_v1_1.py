import json
import os
import sys
from io import StringIO
from tempfile import TemporaryDirectory
from unittest.mock import patch

from ocdskit.cli.__main__ import main

record_package_1_0 = '''{
  "uri": "https://www.contrataciones.gov.py/datos/record-package/193399.json",
  "publishedDate": "2018-12-17T17:31:43Z",
  "records": [
    {
      "ocid": "ocds-03ad3f-193399",
      "releases": [
        {
          "date": "2013-03-05T08:24:59Z",
          "tag": [
            "planning"
          ],
          "url": "https://www.contrataciones.gov.py/datos/id/planning/193399-adquisicion-scanner.json"
        }
      ],
      "compiledRelease": {
        "language": "es",
        "ocid": "ocds-03ad3f-193399",
        "id": "193399-adquisicion-scanner",
        "date": "2018-12-17T17:31:43Z",
        "tag": [
          "compiled"
        ],
        "initiationType": "tender",
        "tender": {
          "id": "193399-adquisicion-scanner",
          "title": "Adquisición de Scanner",
          "status": "complete",
          "value": {
            "currency": "PYG",
            "amount": null
          },
          "procuringEntity": {
            "name": "Dirección Nacional de Contrataciones Públicas (DNCP)",
            "contactPoint": {
              "name": "Abog. Cynthia Leite de Lezcano",
              "email": "uoc@contrataciones.gov.py",
              "telephone": "415-4000"
            }
          },
          "tenderPeriod": {
            "endDate": null,
            "startDate": "2010-03-15T09:00:00Z"
          },
          "submissionMethod": [
            "electronicAuction"
          ],
          "url": "https://www.contrataciones.gov.py/datos/id/convocatorias/193399-adquisicion-scanner"
        },
        "buyer": {
          "name": "Dirección Nacional de Contrataciones Públicas (DNCP)",
          "contactPoint": {
            "name": "Abog. Cynthia Leite de Lezcano",
            "email": "uoc@contrataciones.gov.py",
            "telephone": "415-4000"
          }
        },
        "awards": [
          {
            "id": "193399-adquisicion-scanner",
            "title": "Adquisición de Scanner",
            "status": "active",
            "date": "2010-04-23T12:25:10Z",
            "value": {
              "amount": 135630400.0,
              "currency": "PYG"
            },
            "suppliers": [
              {
                "name": "MASTER SOFT SRL",
                "identifier": {
                  "id": "80007525-0",
                  "legalName": "MASTER SOFT SRL",
                  "scheme": "Registro Único de Contribuyente emitido por el Ministerio de Hacienda del Gobierno de Paraguay"
                },
                "address": {
                  "streetAddress": "CHOFERES DEL CHACO Nº1956",
                  "postalCode": "",
                  "locality": "ASUNCION",
                  "countryName": "Paraguay",
                  "region": "Asunción"
                },
                "contactPoint": {
                  "name": "LUIS MARIA OREGGIONI, GISELA SELMA WEIBERLEN DE OREGGIONI",
                  "faxNumber": "",
                  "telephone": "662831",
                  "email": "mastersoft@tigo.com.py",
                  "url": null
                }
              }
            ],
            "url": "https://www.contrataciones.gov.py/datos/id/adjudicaciones/193399-adquisicion-scanner"
          }
        ]
      }
    }
  ]
}
'''


release_package_1_0 = '''{
  "uri": "https://www.contrataciones.gov.py/datos/record-package/193399.json",
  "publishedDate": "2018-12-17T17:31:43Z",
  "releases": [
   {
        "language": "es",
        "ocid": "ocds-03ad3f-193399",
        "id": "193399-adquisicion-scanner",
        "date": "2018-12-17T17:31:43Z",
        "tag": [
          "compiled"
        ],
        "initiationType": "tender",
        "tender": {
          "id": "193399-adquisicion-scanner",
          "title": "Adquisición de Scanner",
          "status": "complete",
          "value": {
            "currency": "PYG",
            "amount": null
          },
          "procuringEntity": {
            "name": "Dirección Nacional de Contrataciones Públicas (DNCP)",
            "contactPoint": {
              "name": "Abog. Cynthia Leite de Lezcano",
              "email": "uoc@contrataciones.gov.py",
              "telephone": "415-4000"
            }
          },
          "tenderPeriod": {
            "endDate": null,
            "startDate": "2010-03-15T09:00:00Z"
          },
          "submissionMethod": [
            "electronicAuction"
          ],
          "url": "https://www.contrataciones.gov.py/datos/id/convocatorias/193399-adquisicion-scanner"
        },
        "buyer": {
          "name": "Dirección Nacional de Contrataciones Públicas (DNCP)",
          "contactPoint": {
            "name": "Abog. Cynthia Leite de Lezcano",
            "email": "uoc@contrataciones.gov.py",
            "telephone": "415-4000"
          }
        },
        "awards": [
          {
            "id": "193399-adquisicion-scanner",
            "title": "Adquisición de Scanner",
            "status": "active",
            "date": "2010-04-23T12:25:10Z",
            "value": {
              "amount": 135630400.0,
              "currency": "PYG"
            },
            "suppliers": [
              {
                "name": "MASTER SOFT SRL",
                "identifier": {
                  "id": "80007525-0",
                  "legalName": "MASTER SOFT SRL",
                  "scheme": "Registro Único de Contribuyente emitido por el Ministerio de Hacienda del Gobierno de Paraguay"
                },
                "address": {
                  "streetAddress": "CHOFERES DEL CHACO Nº1956",
                  "postalCode": "",
                  "locality": "ASUNCION",
                  "countryName": "Paraguay",
                  "region": "Asunción"
                },
                "contactPoint": {
                  "name": "LUIS MARIA OREGGIONI, GISELA SELMA WEIBERLEN DE OREGGIONI",
                  "faxNumber": "",
                  "telephone": "662831",
                  "email": "mastersoft@tigo.com.py",
                  "url": null
                }
              }
            ],
            "url": "https://www.contrataciones.gov.py/datos/id/adjudicaciones/193399-adquisicion-scanner"
          }
        ]
      }
   ]
}
'''


def test_command_record(monkeypatch):

    with TemporaryDirectory() as d:
        with open(os.path.join(d, 'release-1.0.json'), 'w') as f:
            f.write(record_package_1_0)

        with patch('sys.stdout', new_callable=StringIO) as actual:
            monkeypatch.setattr(sys, 'argv', ['ocdskit', 'update-to-v1_1', d])
            main()

        assert actual.getvalue() == ''

        with open(os.path.join(d, 'release-1.0.json')) as f:
            data = json.load(f)
            assert data['version'] == '1.1'
            assert len(data['records'][0]['compiledRelease']['parties']) == 2
            assert 'contactPoint' not in data['records'][0]['compiledRelease']['buyer']


def test_command_release(monkeypatch):

    with TemporaryDirectory() as d:
        with open(os.path.join(d, 'release-1.0.json'), 'w') as f:
            f.write(release_package_1_0)

        with patch('sys.stdout', new_callable=StringIO) as actual:
            monkeypatch.setattr(sys, 'argv', ['ocdskit', 'update-to-v1_1', d])
            main()

        assert actual.getvalue() == ''

        with open(os.path.join(d, 'release-1.0.json')) as f:
            data = json.load(f)
            assert data['version'] == '1.1'
            assert len(data['releases'][0]['parties']) == 2
            assert 'contactPoint' not in data['releases'][0]['buyer']

import sys
from io import BytesIO, StringIO, TextIOWrapper
from tempfile import TemporaryDirectory
from unittest.mock import patch

import os

from ocdskit.cli.__main__ import main
from tests import read


release_1_0 = '''{
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
        "planning": {
          "budget": {
            "description": "Adquisición de Scanner",
            "amount": {
              "amount": null,
              "currency": "PYG"
            }
          },
          "url": "https://www.contrataciones.gov.py/datos/id/planificaciones/193399-adquisicion-scanner"
        },
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
        ],
        "contracts": [
          {
            "id": "193399-data-systems-sa-emisora-capital-abierto-2",
            "awardID": "193399-adquisicion-scanner",
            "dncpContractCode": "CO-23019-10-0806",
            "title": "Adquisición de Scanner",
            "status": "active",
            "value": {
              "amount": 105600000.0,
              "currency": "PYG"
            },
            "dateSigned": "2010-04-14T12:00:00Z",
            "suppliers": {
              "name": "DATA SYSTEMS SA EMISORA DE CAPITAL ABIERTO",
              "identifier": {
                "id": "80013889-9",
                "legalName": "DATA SYSTEMS SA EMISORA DE CAPITAL ABIERTO",
                "scheme": "Registro Único de Contribuyente emitido por el Ministerio de Hacienda del Gobierno de Paraguay"
              },
              "identifiers": {
                "key": "193399-data-systems-sa-emisora-capital-abierto-2"
              }
            },
            "period": {
              "endDate": "2010-06-13T12:00:00Z",
              "startDate": "2010-04-14T12:00:00Z"
            },
            "url": "https://www.contrataciones.gov.py/datos/id/contratos/193399-data-systems-sa-emisora-capital-abierto-2"
          }
        ]
      }
    }
  ]
}
'''

release_1_1 = '''{
  "uri": "https://www.contrataciones.gov.py/datos/record-package/193399.json",
  "records": [
    {
      "ocid": "ocds-03ad3f-193399",
      "compiledRelease": {
        "ocid": "ocds-03ad3f-193399",
        "id": "193399-adquisicion-scanner",
        "date": "2018-12-17T17:31:43Z",
        "language": "es",
        "tag": [
          "compiled"
        ],
        "initiationType": "tender",
        "parties": [
          {
            "name": "MASTER SOFT SRL",
            "identifier": {
              "legalName": "MASTER SOFT SRL",
              "id": "80007525-0",
              "scheme": "Registro \u00danico de Contribuyente emitido por el Ministerio de Hacienda del Gobierno de Paraguay"
            },
            "roles": [
              "supplier"
            ],
            "contactPoint": {
              "name": "LUIS MARIA OREGGIONI, GISELA SELMA WEIBERLEN DE OREGGIONI",
              "faxNumber": "",
              "telephone": "662831",
              "url": null,
              "email": "mastersoft@tigo.com.py"
            },
            "id": "4c7a1fff53a8cae7d19eff57383a413d",
            "address": {
              "streetAddress": "CHOFERES DEL CHACO N\u00ba1956",
              "countryName": "Paraguay",
              "postalCode": "",
              "locality": "ASUNCION",
              "region": "Asunci\u00f3n"
            }
          },
          {
            "name": "Direcci\u00f3n Nacional de Contrataciones P\u00fablicas (DNCP)",
            "roles": [
              "buyer",
              "procuringEntity"
            ],
            "contactPoint": {
              "name": "Abog. Cynthia Leite de Lezcano",
              "telephone": "415-4000",
              "email": "uoc@contrataciones.gov.py"
            },
            "id": "ce9b810db700b1b9c8487e4b6e49eb30"
          }
        ],
        "contracts": [
          {
            "suppliers": {
              "name": "DATA SYSTEMS SA EMISORA DE CAPITAL ABIERTO",
              "identifier": {
                "legalName": "DATA SYSTEMS SA EMISORA DE CAPITAL ABIERTO",
                "id": "80013889-9",
                "scheme": "Registro \u00danico de Contribuyente emitido por el Ministerio de Hacienda del Gobierno de Paraguay"
              },
              "identifiers": {
                "key": "193399-data-systems-sa-emisora-capital-abierto-2"
              }
            },
            "url": "https://www.contrataciones.gov.py/datos/id/contratos/193399-data-systems-sa-emisora-capital-abierto-2",
            "title": "Adquisici\u00f3n de Scanner",
            "period": {
              "endDate": "2010-06-13T12:00:00Z",
              "startDate": "2010-04-14T12:00:00Z"
            },
            "dncpContractCode": "CO-23019-10-0806",
            "value": {
              "currency": "PYG",
              "amount": 105600000.0
            },
            "status": "active",
            "id": "193399-data-systems-sa-emisora-capital-abierto-2",
            "awardID": "193399-adquisicion-scanner",
            "dateSigned": "2010-04-14T12:00:00Z"
          }
        ],
        "buyer": {
          "name": "Direcci\u00f3n Nacional de Contrataciones P\u00fablicas (DNCP)",
          "id": "ce9b810db700b1b9c8487e4b6e49eb30"
        },
        "awards": [
          {
            "value": {
              "currency": "PYG",
              "amount": 135630400.0
            },
            "url": "https://www.contrataciones.gov.py/datos/id/adjudicaciones/193399-adquisicion-scanner",
            "title": "Adquisici\u00f3n de Scanner",
            "date": "2010-04-23T12:25:10Z",
            "status": "active",
            "id": "193399-adquisicion-scanner",
            "suppliers": [
              {
                "name": "MASTER SOFT SRL",
                "id": "4c7a1fff53a8cae7d19eff57383a413d"
              }
            ]
          }
        ],
        "tender": {
          "url": "https://www.contrataciones.gov.py/datos/id/convocatorias/193399-adquisicion-scanner",
          "title": "Adquisici\u00f3n de Scanner",
          "procuringEntity": {
            "name": "Direcci\u00f3n Nacional de Contrataciones P\u00fablicas (DNCP)",
            "id": "ce9b810db700b1b9c8487e4b6e49eb30"
          },
          "value": {
            "currency": "PYG",
            "amount": null
          },
          "status": "complete",
          "tenderPeriod": {
            "endDate": null,
            "startDate": "2010-03-15T09:00:00Z"
          },
          "id": "193399-adquisicion-scanner",
          "submissionMethod": [
            "electronicAuction"
          ]
        },
        "planning": {
          "url": "https://www.contrataciones.gov.py/datos/id/planificaciones/193399-adquisicion-scanner",
          "budget": {
            "description": "Adquisici\u00f3n de Scanner",
            "amount": {
              "currency": "PYG",
              "amount": null
            }
          }
        }
      },
      "releases": [
        {
          "date": "2013-03-05T08:24:59Z",
          "url": "https://www.contrataciones.gov.py/datos/id/planning/193399-adquisicion-scanner.json",
          "tag": [
            "planning"
          ]
        }
      ]
    }
  ],
  "publishedDate": "2018-12-17T17:31:43Z",
  "version": "1.1"
}
'''


def test_command(monkeypatch):

    with TemporaryDirectory() as d:
        with open(os.path.join(d, 'release-1.0.json'), 'w') as f:
            f.write(release_1_0)

        with patch('sys.stdout', new_callable=StringIO) as actual:
            monkeypatch.setattr(sys, 'argv', ['ocdskit', 'update-to-v1_1', d])
            main()

        assert actual.getvalue() == ''

        with open(os.path.join(d, 'release-1.0.json')) as f:
            assert f.read() == release_1_1

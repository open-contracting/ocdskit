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
                  "scheme": "Registro Único de Contribuyente emitido por el Ministerio de Hacienda"
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
                  "scheme": "Registro Único de Contribuyente emitido por el Ministerio de Hacienda"
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

release_contracts = '''{
  "uri": "https://contrataciones.gov.py/datos/id/contratos/246807-11-setiembre-srl-4",
  "publishedDate": "2018-12-18T13:20:42Z",
  "publisher": {
    "name": "DNCP - Paraguay",
    "legalName": "Dirección Nacional de Contrataciones Públicas, Paraguay",
    "uri": "https://contrataciones.gov.py/datos"
  },
  "license": "https://creativecommons.org/licenses/by/4.0/",
  "publicationPolicy": "https://www.contrataciones.gov.py/datos/legal",
  "releases": [
    {
      "language": "es",
      "ocid": "ocds-03ad3f-246807",
      "id": "246807-11-setiembre-srl-4-contract",
      "date": "2018-12-18T13:20:42Z",
      "tag": [
        "contract"
      ],
      "initiationType": "tender",
      "contracts": [
        {
        "implementation": {
            "transactions": [
              {
                "id": "92885",
                "amount": {
                  "amount": 2372509,
                  "currency": "PYG"
                },
                "date": "2012-05-31T00:00:00Z",
                "providerOrganization": {
                  "id": "PY-PGN-12-8-1000000",
                  "legalName": "1000000-DIRECCION GENERAL DE ADMINISTRACION Y FINANZAS",
                  "scheme": "PY-PGN"
                },
                "receiverOrganization": {
                  "id": "PY-RUC-80017437-2",
                  "legalName": "NUCLEO S.A.",
                  "scheme":  "PY-PGN"
                }
              }
            ]
           },
          "id": "246807-11-setiembre-srl-4",
          "awardID": "246807-adqusicion-guantes-otros-insumos-medicos",
          "dncpContractCode": "CD-13003-13-70684",
          "title": "ADQUSICION DE GUANTES Y OTROS INSUMOS MEDICOS ",
          "status": "active",
          "value": {
            "amount": 17875000,
            "currency": "PYG"
          },
          "items": [
            {
              "description": "Placa Radiografica Medica",
              "id": "M99UFYWPOag%3D",
              "classification": {
                "schema": "Catálogo de productos, bienes y servicios de la Dirección Nacional de Contrataciones",
                "id": "42201810-001",
                "description": "Catálogo de productos, bienes y servicios de la Dirección Nacional de Contrataciones",
                "uri": "https://www.contrataciones.gov.py/datos/api/v2/doc/catalogo/nivel-5/42201810-001"
              },
              "quantity": 10,
              "unit": {
                "name": "Unidad",
                "value": {
                  "amount": 445000,
                  "currency": "PYG"
                }
              }
            },
            {
              "description": "Placa Radiografica Medica",
              "id": "7SmiEGR9Oes%3D",
              "classification": {
                "schema": "Catálogo de productos, bienes y servicios de la Dirección Nacional de Contrataciones",
                "id": "42201810-001",
                "description": "Catálogo de productos, bienes y servicios de la Dirección Nacional de Contrataciones",
                "uri": "https://www.contrataciones.gov.py/datos/api/v2/doc/catalogo/nivel-5/42201810-001"
              },
              "quantity": 10,
              "unit": {
                "name": "Unidad",
                "value": {
                  "amount": 850000,
                  "currency": "PYG"
                }
              }
            },
            {
              "description": "Liquido fijador para placas radiograficas",
              "id": "hPQ2FURf7RQ%3D",
              "classification": {
                "schema": "Catálogo de productos, bienes y servicios de la Dirección Nacional de Contrataciones",
                "id": "42203708-002",
                "description": "Catálogo de productos, bienes y servicios de la Dirección Nacional de Contrataciones",
                "uri": "https://www.contrataciones.gov.py/datos/api/v2/doc/catalogo/nivel-5/42203708-002"
              },
              "quantity": 20,
              "unit": {
                "name": "Unidad",
                "value": {
                  "amount": 110000,
                  "currency": "PYG"
                }
              }
            },
            {
              "description": "Liquido revelador para placas radiograficas",
              "id": "3LykMkkFXqU%3D",
              "classification": {
                "schema": "Catálogo de productos, bienes y servicios de la Dirección Nacional de Contrataciones",
                "id": "42203704-001",
                "description": "Catálogo de productos, bienes y servicios de la Dirección Nacional de Contrataciones",
                "uri": "https://www.contrataciones.gov.py/datos/api/v2/doc/catalogo/nivel-5/42203704-001"
              },
              "quantity": 20,
              "unit": {
                "name": "Unidad",
                "value": {
                  "amount": 110000,
                  "currency": "PYG"
                }
              }
            },
            {
              "description": "Pinza para laboratorio",
              "id": "2iT5c5pHD9g%3D",
              "classification": {
                "schema": "Catálogo de productos, bienes y servicios de la Dirección Nacional de Contrataciones",
                "id": "41122404-001",
                "description": "Catálogo de productos, bienes y servicios de la Dirección Nacional de Contrataciones",
                "uri": "https://www.contrataciones.gov.py/datos/api/v2/doc/catalogo/nivel-5/41122404-001"
              },
              "quantity": 5,
              "unit": {
                "name": "Unidad",
                "value": {
                  "amount": 105000,
                  "currency": "PYG"
                }
              }
            }
          ],
          "dateSigned": "2013-04-05T12:00:00Z",
          "suppliers": {
            "name": "11 DE SETIEMBRE SRL"
          },
          "period": {
            "endDate": "2013-04-15T12:00:00Z",
            "startDate": "2013-04-05T12:00:00Z"
          },
          "url": "https://www.contrataciones.gov.py/datos/id/contratos/246807-11-setiembre-srl-4"
        }
      ]
    }
  ]
}'''


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


def test_command_release_contracts(monkeypatch):

    with TemporaryDirectory() as d:
        with open(os.path.join(d, 'release-1.0.json'), 'w') as f:
            f.write(release_contracts)
        with patch('sys.stdout', new_callable=StringIO) as actual:
            monkeypatch.setattr(sys, 'argv', ['ocdskit', 'update-to-v1_1', d])
            main()
        assert actual.getvalue() == ''
        with open(os.path.join(d, 'release-1.0.json')) as f:
            data = json.load(f)
            assert data['version'] == '1.1'
            payee = data['releases'][0]['contracts'][0]['implementation']['transactions'][0]['payee']
            assert payee['id'] == 'PY-PGN-PY-RUC-80017437-2'

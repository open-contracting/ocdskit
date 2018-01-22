import json

import requests
import validators
from ocdskit.exceptions import CommandError
from .base import BaseCommand


class Command(BaseCommand):
    name = 'check_documents_urls'
    help = 'reads JSON data from standard input and check all documents urls, and prints url + status'

    def add_arguments(self):
        self.add_argument('--timeout', help='timeout (seconds) to get a document',
                          default='10')

    def handle(self):
        for i, line in enumerate(self.buffer()):
            try:
                data = json.loads(line)
            except json.decoder.JSONDecodeError as e:
                raise CommandError('item {}: JSON error: {}'.format(i, e))
            for release in data['releases']:
                if 'planning' in release:
                    self.check_document_url(release['planning'])
                    if 'milestones' in release['planning']:
                        for milestone in release['planning']['milestones']:
                            self.check_document_url(milestone)
                if 'tender' in release:
                    self.check_document_url(release['tender'])
                    if 'milestones' in release['tender']:
                        for milestone in release['tender']['milestones']:
                            self.check_document_url(milestone)
                if 'award' in release:
                    self.check_document_url(release['award'])
                if 'contracts' in release:
                    for contract in release['contracts']:
                        self.check_document_url(contract)
                        if 'milestones' in contract:
                            for milestone in contract['milestones']:
                                self.check_document_url(milestone)
                        if 'implementation' in contract:
                            self.check_document_url(contract['implementation'])
                            if 'milestones' in contract['implementation']:
                                for milestone in contract['implementation']['milestones']:
                                    self.check_document_url(milestone)

    def check_document_url(self, json_object):
        if 'documents' in json_object:
            documents = json_object['documents']
            for document in documents:
                try:
                    if 'url' in document:
                        if not validators.url(document['url']):
                            print("%s status: %s" % (document['url'], 'malformed url'))
                        else:
                            r = requests.get(document['url'], timeout=int(self.args.timeout))
                            print("%s status: %s" % (document['url'], r.status_code))
                except requests.exceptions.Timeout:
                    print("%s status: %s" % (document['url'], 'timeout'))

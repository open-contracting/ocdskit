import json

import ocdsmerge

from .base import BaseCommand
from ocdsreport.exceptions import CommandError


class Command(BaseCommand):
    name = 'merge'
    help = 'merge the releases of a release package'

    def add_arguments(self):
        self.add_argument('--uri', help='The "uri" to identify the release package')

    def handle(self, args, data):
        if isinstance(data, dict):
            data = [data]

        for release_package in data:
            if not args.uri or release_package['uri'] == args.uri:
                release = ocdsmerge.merge(release_package['releases'])
                print(json.dumps(release, indent=4, separators=(',', ': ')))
                break
        else:
            raise CommandError('{} not found'.format(args.uri))

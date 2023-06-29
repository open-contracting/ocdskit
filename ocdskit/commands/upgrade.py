from collections import OrderedDict  # for move_to_end()

from ocdskit import upgrade
from ocdskit.commands.base import OCDSCommand
from ocdskit.exceptions import CommandError


class Command(OCDSCommand):
    name = 'upgrade'
    help = 'upgrades packages, records and releases from an old version of OCDS to a new version'

    def add_arguments(self):
        self.add_argument('versions', help='the colon-separated old and new versions')

    def handle(self):
        versions = self.args.versions

        version_from, version_to = versions.split(':')
        if version_from < version_to:
            direction = 'up'
        else:
            direction = 'down'

        try:
            upgrade_method = getattr(upgrade, f"upgrade_{versions.replace('.', '').replace(':', '_')}")
        except AttributeError as e:
            message = f"{direction}grade from {versions.replace(':', ' to ')} is not supported"
            raise CommandError(message) from e

        for data in self.items(map_type=OrderedDict):
            data = upgrade_method(data)
            self.print(data)

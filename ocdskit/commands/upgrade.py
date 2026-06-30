from collections import OrderedDict  # for move_to_end()

from ocdskit import upgrade
from ocdskit.commands.base import OCDSCommand
from ocdskit.exceptions import CommandError


class Command(OCDSCommand):
    name = "upgrade"
    help = "upgrades packages, releases and records from an old version of OCDS to a new version"

    def add_arguments(self):
        self.add_argument("versions", help="the colon-separated old and new versions")
        self.add_argument(
            "--no-reorder",
            action="store_true",
            help="don't move identifying fields like 'ocid' to the top of objects",
        )

    def handle(self):
        versions = self.args.versions

        version_from, version_to = versions.split(":")
        direction = "up" if version_from < version_to else "down"

        try:
            upgrade_method = getattr(upgrade, f"upgrade_{versions.replace('.', '').replace(':', '_')}")
        except AttributeError as e:
            message = f"{direction}grade from {versions.replace(':', ' to ')} is not supported"
            raise CommandError(message) from e

        reorder = not self.args.no_reorder
        map_type = OrderedDict if reorder else dict

        for data in self.items(map_type=map_type):
            self.print(upgrade_method(data, reorder=reorder))

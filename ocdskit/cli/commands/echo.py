from ocdskit.cli.commands.base import OCDSCommand


class Command(OCDSCommand):
    name = 'echo'
    help = 'Repeats the input, applying --encoding, --ascii, --pretty and --root-path, and using the UTF-8 encoding'

    def handle(self):
        for data in self.items():
            self.print(data)

from ocdskit.cli.commands.base import OCDSCommand


class Command(OCDSCommand):
    name = 'split-release-packages'
    help = 'reads release packages from standard input, and prints many release packages for each'

    def add_arguments(self):
        self.add_argument('size', type=int, help='the number of releases per package')

    def handle(self):
        # See exploration of not reading each input into memory: https://github.com/open-contracting/ocdskit/issues/118
        for package in self.items():
            releases = package['releases']

            for i in range(0, len(releases), self.args.size):
                package.update(releases=releases[i:i + self.args.size])

                self.print(package)

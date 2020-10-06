from ocdskit.cli.commands.base import OCDSCommand


class Command(OCDSCommand):
    name = 'split-project-packages'
    help = 'reads project packages from standard input, and prints many record packages for each'

    def add_arguments(self):
        self.add_argument('size', type=int, help='the number of projects per package')

    def handle(self):
        # See exploration of not reading each input into memory: https://github.com/open-contracting/ocdskit/issues/118
        for package in self.items():
            projects = package['projects']

            for i in range(0, len(projects), self.args.size):
                package.update(projects=projects[i:i + self.args.size])

                self.print(package)

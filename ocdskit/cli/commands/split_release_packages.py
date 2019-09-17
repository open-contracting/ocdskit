from .base import OCDSCommand


class Command(OCDSCommand):
    name = 'split-release-packages'
    help = 'reads release packages from standard input, and prints many release packages for each'

    def add_arguments(self):
        self.add_argument('size', type=int, help='the number of releases per package')

    def handle(self):
        for package in self.items():
            releases = package['releases']

            for i in range(0, len(releases), self.args.size):
                package.update(releases=releases[i:i + self.args.size])

                self.print(package)

from .base import BaseCommand


class Command(BaseCommand):
    name = 'split-release-packages'
    help = 'reads release packages from standard input, and prints many release packages for each'

    def add_arguments(self):
        self.add_argument('size', type=int,
                          help='the number of releases per package')

    def handle(self):
        for line in self.buffer():
            package = self.json_loads(line)

            releases = package['releases']

            for i in range(0, len(releases), self.args.size):
                package.update(releases=releases[i:i + self.args.size])

                self.print(package)

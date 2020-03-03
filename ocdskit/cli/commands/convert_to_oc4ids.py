import logging

from ocdskit import oc4ids
from ocdskit.cli.commands.base import OCDSCommand

logger = logging.getLogger("ocdskit")


class Command(OCDSCommand):
    name = "convert-to-oc4ids"
    help = "reads release packages and individual releases from standard input and produces an oc4ids project"

    def add_arguments(self):
        self.add_argument("--project-id", help="Project ID of the created project", default=None)
        self.add_argument("--package", action="store_true", help="wrap the project in a package")
        self.add_argument("--transforms", help="comma-separated list of optional transforms", default="")
        self.add_argument("--all", help="run all optional transforms", action="store_true")

        self.add_package_arguments("project", "if --package is set, ")

    def handle(self):
        project_id = self.args.id
        config = {}

        if self.args.all:
            config["all"] = True
        else:
            for option in self.args.options.split(","):
                config[option.strip()] = True

        project = oc4ids.run_transforms(config, self.items(), project_id=project_id)

        if self.args.package:
            output = self.parse_package_arguments()
            output["projects"] = [project]
        else:
            output = project

        self.print(output)

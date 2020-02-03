import logging

from ocdskit.cli.commands.base import OCDSCommand
import ocdskit.oc4ids_transforms as transforms

logger = logging.getLogger("ocdskit")


class Command(OCDSCommand):
    name = "oc4ids_transform"
    help = "reads release packages and individual releases from standard input and produces an" "oc4ids project"

    def add_arguments(self):
        self.add_argument("--id", help="Project ID of the created project", default=None)
        self.add_argument("--package", action="store_true", help="wrap the project in a package")
        self.add_argument("--options", help="comma seperated list of optional tranforms", default="")

        self.add_package_arguments("project", "if --package is set, ")

    def handle(self):
        project_id = self.args.id
        config = {}

        for option in self.args.options.split(","):
            config[option.strip()] = True

        project = transforms.run_transforms(config, self.items(), project_id=project_id)

        if self.args.package:
            output = self.parse_package_arguments()
            output["projects"] = [project]
        else:
            output = project

        self.print(output)

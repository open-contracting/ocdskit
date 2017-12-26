# Developing OCDS Kit

## Adding a command

1. Create a file matching the command's name in `ocdskit/cli/commands`, replacing hyphens with underscores.
1. Add the command's module to `COMMAND_MODULES` in `ocdskit/__main__.py`, in alphabetical order.
1. Fill in the command's file (see `ocdskit/cli/commands/compile.py` for a brief file).
1. Add tests for the command.

## Release process

1. Check the version number and set the date in `CHANGELOG.md`
1. Check the version number in `setup.py`
1. Tag the release: ``git tag -a x.y.z; git push --tags``
1. Release on PyPI: ``python setup.py sdist upload``
1. Iterate the version number in `CHANGELOG.md` and `setup.py`.

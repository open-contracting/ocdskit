Contributing
============

Adding a command
----------------

#. Create a file matching the command's name in ``ocdskit/cli/commands``, replacing hyphens with underscores.
#. Add the command's module to ``COMMAND_MODULES`` in ``ocdskit/__main__.py``, in alphabetical order.
#. Fill in the command's file (see ``ocdskit/cli/commands/compile.py`` for a brief file).
#. Add tests for the command.

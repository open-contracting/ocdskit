class OCDSKitError(Exception):
    """Base class for exceptions from within this package"""


class CommandError(OCDSKitError):
    """Errors from within this package's CLI"""


class InconsistentVersionError(OCDSKitError):
    """Raised if the versions are inconsistent across packages to compile"""

    def __init__(self, message, earlier_version=None, current_version=None):
        self.earlier_version = earlier_version
        self.current_version = current_version
        super().__init__(message)


class MissingColumnError(OCDSKitError):
    """Raised if the column to order by is missing"""


class UnknownFormatError(OCDSKitError):
    """Raised if the format of a file can't be determined"""

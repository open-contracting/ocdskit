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
    """Raised if the column by which to order is missing"""


class UnknownFormatError(OCDSKitError):
    """Raised if the format of a file can't be determined"""


class MissingOcidKeyError(OCDSKitError, KeyError):
    """Raised if a release to be merged is missing an ``ocid`` key"""


class OCDSKitWarning(UserWarning):
    """Base class for warnings from within this package"""


class MissingRecordsWarning(OCDSKitWarning):
    """Used when the "records" field is missing from a record package when combining packages"""

    def __str__(self):
        return 'item {0} has no "records" field (check that it is a record package)'.format(*self.args)


class MissingReleasesWarning(OCDSKitWarning):
    """Used when the "releases" field is missing from a release package when combining packages"""

    def __str__(self):
        return 'item {0} has no "releases" field (check that it is a release package)'.format(*self.args)

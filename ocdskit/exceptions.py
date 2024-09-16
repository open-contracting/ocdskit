class OCDSKitError(Exception):
    """Base class for exceptions from within this package."""


class CommandError(OCDSKitError):
    """Errors from within this package's CLI."""


class InconsistentVersionError(OCDSKitError):
    """Raised if the versions are inconsistent across packages to compile."""

    def __init__(self, message, earlier_version=None, current_version=None):
        self.earlier_version = earlier_version
        self.current_version = current_version
        super().__init__(message)


class MissingColumnError(OCDSKitError):
    """Raised if the column by which to order is missing."""


class UnknownFormatError(OCDSKitError):
    """Raised if the format of a file can't be determined."""


class UnknownVersionError(OCDSKitError):
    """Raised if the OCDS version is not recognized."""


class MissingOcidKeyError(OCDSKitError, KeyError):
    """Raised if a release to be merged is missing an ``ocid`` field."""


class OCDSKitWarning(UserWarning):
    """Base class for warnings from within this package."""


class MissingRecordsWarning(OCDSKitWarning):
    """Used when the "records" field is missing from a record package when combining packages."""


class MissingReleasesWarning(OCDSKitWarning):
    """Used when the "releases" field is missing from a release package when combining packages."""


class MergeErrorWarning(OCDSKitWarning):
    """Used when downgrading an OCDS Merge exception to a warning."""

class OCDSKitError(Exception):
    """Base class for exceptions from within this package"""


class CommandError(OCDSKitError):
    """Errors from within this package's CLI"""

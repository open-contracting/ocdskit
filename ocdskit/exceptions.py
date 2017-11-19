class ReportError(Exception):
    """Base class for exceptions from within this package"""


class CommandError(ReportError):
    """Errors from within this package's CLI"""

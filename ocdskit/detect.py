import logging

from ocdskit.util import detect

logger = logging.getLogger('ocdskit')


def detect_format(path, root_path=''):
    """
    Returns the format of OCDS data, and whether the OCDS data is concatenated or in an array.
    
    If the OCDS data is concatenated or in an array, assumes that all items have the same format as the first item.

    :param str path: the path to a file
    :param str root_path: the path to the OCDS data within the file
    :returns: a tuple of the format, whether data is concatenated, and whether data is in an array
    :rtype: tuple
    :raises UnknownFormatError: if the format cannot be detected
    """
    return detect(path, root_path)

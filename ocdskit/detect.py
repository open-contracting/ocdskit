import logging

from ocdskit.util import detect

logger = logging.getLogger('ocdskit')


def detect_format(path, root_path=''):
    """
    Returns the file format with additional info whether the items are in array and/or concatenated.

    :param str path: path to tested file
    :param str root_path: ``json path`` within the file, where the tested items will be searched for
    :return: a tuple (detected_format, is_concatenated, is_array)
    :raises UnknownFormatError: if the format cannot be detected
    """
    return detect(path, root_path)

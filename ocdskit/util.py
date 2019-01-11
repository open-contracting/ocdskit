def get_ocds_minor_version(package):
    """
    Returns the OCDS minor version of the release package or record package.
    """
    if 'version' in package:
        return package['version']
    else:
        return '1.0'

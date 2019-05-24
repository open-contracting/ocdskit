import os.path


def path(filename):
    return os.path.join('tests', 'fixtures', filename)


def read(filename, mode='rt', encoding=None):
    with open(path(filename), mode, encoding=encoding) as f:
        return f.read()

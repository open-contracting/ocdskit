import os.path


def read(filename, mode='rt', encoding=None):
    with open(os.path.join('tests', 'fixtures', filename), mode, encoding=encoding) as f:
        return f.read()

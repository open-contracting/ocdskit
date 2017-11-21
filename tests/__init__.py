import os.path


def read(filename, mode='r'):
    with open(os.path.join('tests', 'fixtures', filename), mode) as f:
        return f.read()

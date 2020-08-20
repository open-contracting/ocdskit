from setuptools import find_packages, setup

with open('README.rst') as f:
    long_description = f.read()

setup(
    name='ocdskit',
    version='0.2.12',
    author='Open Contracting Partnership',
    author_email='data@open-contracting.org',
    url='https://github.com/open-contracting/ocdskit',
    description='A suite of command-line tools for working with OCDS data',
    license='BSD',
    packages=find_packages(exclude=['tests', 'tests.*']),
    long_description=long_description,
    install_requires=[
        'ijson>=2.5',
        'jsonpointer',
        'jsonref',
        'jsonschema',
        'ocdsmerge>=0.6',
        'ocdsextensionregistry>=0.0.14',
        'requests',
        'rfc3987',
        'sqlalchemy',
        'strict-rfc3339',
    ],
    extras_require={
        'perf': [
            'orjson>=3',
        ],
        'test': [
            'coveralls',
            'pytest',
            'pytest-cov',
            'pytest-vcr',
        ],
        'docs': [
            'Sphinx',
            'sphinx-autobuild',
            'sphinx_rtd_theme',
        ],
    },
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    entry_points={
        'console_scripts': [
            'ocdskit = ocdskit.cli.__main__:main',
        ],
    },
)

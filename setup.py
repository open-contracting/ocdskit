from setuptools import setup, find_packages

with open('README.rst') as f:
    long_description = f.read()

setup(
    name='ocdskit',
    version='0.0.5',
    author='Open Contracting Partnership',
    author_email='data@open-contracting.org',
    url='https://github.com/open-contracting/ocdskit',
    description='A suite of command-line tools for working with OCDS data',
    license='BSD',
    packages=find_packages(),
    long_description=long_description,
    install_requires=[
        'jsonref',
        'jsonschema',
        'ocdsmerge>=0.5.1',
        'python-dateutil',
        'pytz',
        'requests',
        'rfc3987',
        'sqlalchemy',
        'strict-rfc3339',
    ],
    extras_require={
        'test': [
            'coveralls',
            'pytest',
            'pytest-cov',
        ],
    },
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3.6',
    ],
    entry_points={
        'console_scripts': [
            'ocdskit = ocdskit.cli.__main__:main',
        ],
    },
)

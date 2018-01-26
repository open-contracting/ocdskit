from setuptools import setup, find_packages

setup(
    name='ocdskit',
    version='0.0.2',
    author='James McKinney',
    author_email='james@slashpoundbang.com',
    url='https://github.com/open-contracting/ocdskit',
    description='A suite of command-line tools for working with OCDS data',
    platforms=['any'],
    license='BSD',
    packages=find_packages(),
    long_description=open('README.rst').read(),
    entry_points='''[console_scripts]
ocdskit = ocdskit.cli.__main__:main''',
    install_requires=[
        'jsonref',
        'jsonschema',
        'ocdsmerge',
        'python-dateutil',
        'pytz',
        'requests',
        'rfc3987',
        'sqlalchemy',
        'strict-rfc3339',
    ],
    extras_require={
        'test': [
            'pytest<3',
            'pytest-capturelog',
            'pytest-cov',
        ],
    },
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3.6',
    ],
)

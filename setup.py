from setuptools import find_packages, setup

with open('README.rst') as f:
    long_description = f.read()

setup(
    name='ocdskit',
    version='1.1.1',
    author='Open Contracting Partnership',
    author_email='data@open-contracting.org',
    url='https://github.com/open-contracting/ocdskit',
    description='A suite of command-line tools for working with OCDS data',
    license='BSD',
    packages=find_packages(exclude=['tests', 'tests.*']),
    long_description=long_description,
    long_description_content_type='text/x-rst',
    install_requires=[
        'ijson>=2.5',
        'jsonref',
        'ocdsmerge>=0.6',
        'ocdsextensionregistry>=0.1.2',
        # https://github.com/python-attrs/cattrs/issues/253
        'cattrs!=22.1.0;platform_python_implementation=="PyPy"',
    ],
    extras_require={
        'perf': [
            'orjson>=3',
        ],
        'test': [
            'coveralls',
            'jsonpointer',
            'pytest',
            'pytest-cov',
            'pytest-vcr',
        ],
        'docs': [
            'furo',
            'sphinx',
            'sphinx-autobuild',
        ],
    },
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
    entry_points={
        'console_scripts': [
            'ocdskit = ocdskit.cli.__main__:main',
        ],
    },
)

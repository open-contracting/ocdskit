from setuptools import setup, find_packages

setup(
    name='ocdsreport',
    version='0.0.1',
    author='James McKinney',
    author_email='james@slashpoundbang.com',
    url='https://github.com/open-contracting/mel-reporting-support',
    description='Scripts for automatically measuring specific indicators',
    platforms=['any'],
    license='BSD',
    packages=find_packages(),
    entry_points='''[console_scripts]
ocdsreport = ocdsreport.cli.__main__:main''',
    install_requires=[
        'jsonschema==2.6.0',
        'ocdsmerge==0.3',
        'python-dateutil==2.6.1',
        'pytz==2017.2',
        'requests==2.18.4', 'sqlalchemy',
    ],
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
)

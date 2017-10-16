# ocds_validator

Validate a directory with releases-packages (Only version 1.0 supported) and generate a bd with the results. Also makes
an analysis about the fields and publication levels.

## Installation

Clone this repository. Create a python virtual environment and enter it

```shell
virtualenv .ve -p python3

source .ve/bin/activate
```

Install the requirements

```shell
pip install -r requirements.txt
```

## Usage

To see the options.

```shell
python ocds_validation.py -h
```
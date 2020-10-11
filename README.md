# req-update

[![PyPI](https://img.shields.io/pypi/v/req-update)](https://pypi.org/project/req-update/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/req-update)
![PyPI - License](https://img.shields.io/pypi/l/req-update)

[![Circle CI](https://circleci.com/gh/albertyw/req-update.svg?style=shield)](https://circleci.com/gh/albertyw/req-update)
[![Dependency Status](https://pyup.io/repos/github/albertyw/req-update/shield.svg)](https://pyup.io/repos/github/albertyw/req-update/)
[![Code Climate](https://codeclimate.com/github/albertyw/req-update/badges/gpa.svg)](https://codeclimate.com/github/albertyw/req-update)
[![Test Coverage](https://codeclimate.com/github/albertyw/req-update/badges/coverage.svg)](https://codeclimate.com/github/albertyw/req-update/coverage)

`req-update` is a CLI tool to automatically update dependencies listed in `requirements.txt`.

## Usage

`req-update` requires no command line arguments.  Running `req-update` will
make it create a branch `dep-update`, check outdated packages (compared against
your current installed packages), and commit a series of single-package update
commits.

```
$ python req_update/req_update.py -h
usage: req_update.py [-h] [-d] [-v] [--version]

Update python dependencies for your project with git integration https://github.com/albertyw/req-update

optional arguments:
  -h, --help     show this help message and exit
  -d, --dryrun   Dry run
  -v, --verbose  Verbose output
  --version      show program's version number and exit
```

## Features

 - Integrates with git, creating a branch with one commit per updated dependency
 - No third party dependencies beyond python 3 standard library
 - Automatic detection of python requirements.txt; no CLI arguments required

## Comparisons

 - `req-upgrader` - `req-update` integrates with git

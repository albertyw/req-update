# req-update

[![PyPI](https://img.shields.io/pypi/v/req-update)](https://pypi.org/project/req-update/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/req-update)
![PyPI - License](https://img.shields.io/pypi/l/req-update)

[![Circle CI](https://circleci.com/gh/albertyw/req-update.svg?style=shield)](https://circleci.com/gh/albertyw/req-update)
[![Dependency Status](https://pyup.io/repos/github/albertyw/req-update/shield.svg)](https://pyup.io/repos/github/albertyw/req-update/)

`req-update` is a CLI tool to automatically update dependencies listed in `requirements.txt`.

## Features

 - Integrates with git, creating a branch with one commit per updated dependency
 - No third party dependencies beyond python 3 standard library
 - Automatic detection of python requirements.txt; no CLI arguments required

## Comparisons

 - `req-upgrader` - `req-update` integrates with git

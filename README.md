# pip-update

`pip-update` is a CLI tool to automatically update dependencies listed in `requirements.txt`.

## Features

 - Integrates with git, creating a branch with one commit per updated dependency
 - No third party dependencies beyond python 3 standard library
 - Automatic detection of python requirements.txt; no CLI arguments required

## Comparisons

 - `pip-upgrader` - `pip-update` integrates with git

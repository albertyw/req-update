# req-update

[![Circle CI](https://circleci.com/gh/albertyw/req-update.svg?style=shield)](https://circleci.com/gh/albertyw/req-update)

`req-update` is a CLI tool to automatically update dependencies listed in `requirements.txt`.

## Features

 - Integrates with git, creating a branch with one commit per updated dependency
 - No third party dependencies beyond python 3 standard library
 - Automatic detection of python requirements.txt; no CLI arguments required

## Comparisons

 - `req-upgrader` - `req-update` integrates with git

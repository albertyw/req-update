# pip-update

[![Codeship Status for albertyw/pip-update](https://app.codeship.com/projects/e3bbaae0-e4f2-0138-08ce-1e914e8879b6/status?branch=master)](https://app.codeship.com/projects/410831)

`pip-update` is a CLI tool to automatically update dependencies listed in `requirements.txt`.

## Features

 - Integrates with git, creating a branch with one commit per updated dependency
 - No third party dependencies beyond python 3 standard library
 - Automatic detection of python requirements.txt; no CLI arguments required

## Comparisons

 - `pip-upgrader` - `pip-update` integrates with git

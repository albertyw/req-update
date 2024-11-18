CHANGELOG
=========

2.7.4 (2024-11-17)
------------------

 - Drop support for python 3.7 and 3.8
 - Improve logging
 - Cache network requests for speed
 - Improve ability for docker/drone update to find newer versions
 - Update dependencies


2.7.3 (2024-11-10)
------------------

 - Support python 3.13
 - Update dependencies


2.7.2 (2024-08-04)
------------------

 - Fix bug with checking if git submodule has been updated
 - Update dependencies
 - Remove deprecated pyup


2.7.1 (2024-06-23)
------------------

 - Allow python upgrade to find files anywhere in repository
 - Update dependencies


2.7.0 (2024-06-01)
------------------

 - Support updating github actions
 - Vertically align comments for python updates
 - Update dependencies


2.6.0 (2024-05-26)
------------------

 - Change check_repository_cleanliness to return a bool rather than raise an exception
 - Add a ignore-cleanliness CLI flag
 - Fix update warnings in dry-mode
 - Update dependencies


2.5.1 (2024-02-20)
------------------

 - Fix docker writing updates to the wrong path
 - Fix erroring out on docker hub errors
 - Update and clean up dependencies


2.5.0 (2024-02-05)
------------------

 - Support updating dependencies in pyproject.toml
 - Cleanup testing and types
 - Update dependencies


2.4.3 (2023-10-14)
------------------

 - Fix version comparison for docker images
 - Remove setup.py
 - Update dependencies


2.4.2 (2023-10-02)
------------------

 - Fix git pushing updates for docker and drone
 - Update dependencies
 - Explicitly support python 3.12


2.4.1 (2023-10-01)
------------------

 - Support updating all Dockerfile and drone.yml files in a repository


2.4.0 (2023-09-18)
------------------

 - Support updating drone configs
 - Refactors


2.3.3 (2023-09-17)
------------------

 - Fix update configuration bug
 - Refactors


2.3.2 (2023-09-16)
------------------

 - Fix bug where update languages would be incorrect in git commit messages
 - Update dependencies


2.3.1 (2023-09-03)
------------------

 - Improve handling versions of docker images
 - Ensure dryrun does not modify files
 - Improve logging
 - Update dependencies


2.3.0 (2023-08-28)
------------------

 - Support updating Dockerfile base images
 - Speed up tests
 - Update dependencies


2.2.3 (2023-06-03)
------------------

 - Fix python obeying dryrun configuration
 - Update dependencies


2.2.2 (2023-03-13)
------------------

 - Ensure spacing between version and comment when a version number increases in number of characters
 - Update dependencies
 - CI optimizations


2.2.1 (2022-10-29)
------------------

 - Make sure python package update is case insensitive
 - Improve python type annotations
 - Update dependencies


2.2.0 (2022-10-01)
------------------

 - Add `--language` flag to selectively update a single language's dependencies
 - Update dependencies


2.1.0 (2022-08-27)
------------------

 - Add support for updating git submodules
 - Add support for execute_shell in a given cwd
 - Refactors, cleanup, and testing
 - Update dependencies

2.0.5 (2022-08-20)
------------------

 - Do not check repository cleanliness when in dryrun mode
 - Add an `Updater` skeleton class
 - Refactor imports and make mypy stricter
 - Add tests for CLI usage
 - Update test dependencies
 - Various cleanup


2.0.4 (2022-07-31)
------------------

 - Have node updates warn when making major version changes
 - Update dependencies


2.0.3 (2022-07-17)
------------------

 - Gracefully deal with node dependency version conflicts
 - Update dependencies
 - Test against Python 3.11


2.0.2 (2022-03-21)
------------------

 - Fix bug with package.json with no dependencies
 - Add test for python packaging
 - Update dependencies


2.0.1 (2022-02-12)
------------------

 - Fix compatibility with python 3.7 through python 3.9


2.0.0 (2022-02-10)
------------------

 - **Breaking** - Removed the `--install` flag.  Running req-update will always install newly updated packages in all languages.


1.8.0 (2022-02-05)
------------------

 - Support updating go dependencies
 - Switch to black python formatter
 - Dependency updates


1.7.0 (2022-01-21)
------------------

 - Support updating pinned node dependencies
 - Add color for warning logs
 - Clarify logging text
 - Support the `NO_COLOR` environment variable


1.6.5 (2022-01-08)
------------------

 - Add color to warning logs
 - Remove explicit support for EOL python 3.5 and 3.6
 - Update error outputs
 - Update dependencies


1.6.4 (2022-01-02)
------------------

 - Limit python dependency update to only when requirements.txt is present
 - Bring test coverage back to 100%
 - Update dependencies


1.6.3 (2021-12-20)
------------------

 - Fix a bug where install flag wouldn't work


1.6.2 (2021-12-05)
------------------

 - Fix bug with committing node updates on the original branch if there were no python updates
 - README updates
 - Surface if dependency updates were made


1.6.1 (2021-11-26)
------------------

 - Fix bug with checking if node dependency update changed files


1.6.0 (2021-11-25)
------------------

 - Support updating node dependencies
 - Refactors


1.5.3 (2021-11-21)
------------------

 - Refactors


1.5.2 (2021-11-07)
------------------

 - Fix support for special python package version names
 - Support python 3.10
 - Update dependencies


1.5.1 (2021-06-09)
------------------

 - Work correctly with already existing dep-update branches
 - Update dependencies


1.5.0 (2021-04-04)
------------------

 - Add `--install` flag


1.4.1 (2021-03-16)
------------------

 - Clean up error messages
 - Update dependencies
 - Build optimizations


1.4.0 (2021-02-21)
------------------

 - Add a new `--push` option to git push each commit to the default remote
 - Switch CI platform from CircleCI to Drone
 - Update dependencies


1.3.4 (2021-01-18)
------------------

 - Show a warning when a dependency update changes major versions
 - Support python 3.9


1.3.3 (2020-12-25)
------------------

 - Ignore untracked files when checking repository cleanliness


1.3.2 (2020-12-05)
------------------

 - Correctly with with packages with dashes and/or underscores in name
 - Fix bug with no-op version updates


1.3.1 (2020-11-12)
------------------

 - Fix logic for chcking if the dep-update branch already exists


1.3.0 (2020-11-08)
------------------

 - Align comments on dependency lines when updating
 - Rollback dep-update branch if no dependencies were updated
 - Require that dependencies in requirements.txt files start at beginning of line
 - Cleanup


1.2.0 (2020-11-04)
------------------

 - Allow req-update to reusing an existing dep-update branch
 - Check pip version on startup and error when version is not high enough
 - Various fixes


1.1.0 (2020-10-25)
------------------

 - Make dryrun mode work correctly
 - Make verbose mode spit out all commands
 - Make CLI packaging work correctly


1.0.0 (2020-10-10)
------------------

 - Initial working release


0.0.1 (2020-10-01)
------------------
 - Initialize repository
 - PyPI placeholder

CHANGELOG
=========

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

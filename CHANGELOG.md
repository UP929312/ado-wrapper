# Changelog

## vUpcoming

### Added

- Runs now support stages to include and variables (as opposed to template parameters)

### Changed

- Search hit's have been renamed to CodeSearchHit to accomodate future support for WorkItemHit and WikiSearchHit.
- `Run`s template_variables have been renamed to template_parameters (for the inclusion of actual template variables)
- `Run`s source_branch has been renamed to `branch_name`.

---

## v1.12.0

### Added

- Added `Run`s, `UserPermission`s, `MergePermission`s and more to examples.md and all their methods.
- Basic Test for Searches.

### Changed

- All exceptions now come from generic AdoWrapperException (for easier catching of generic exception)
- Get repo contents now also works with filters that contain the dot, e.g. [".json"] now works (instead of ["json"])
- code_snippet of `Search`'s `Hit` is now optional (str | None).

---

## v1.11.0

### Changed

- All under-the-hood state managed resource functions have been made private, meaning they won't appear in autocompletes and such.
  - This was so it was easier to find the real function you wanted, and is a lot clearer what's part of the public API or not.
- Branches can now fetch repos by name *or* id now.

### Fixes

- Runs now properly extract their repo id now, previously it would always be `None`

---

## v1.10.0

### Added

- `Runs`, these are similar to `Builds`, but are more modern, and support template variables
  - These allow running pipelines with more data, e.g. dropdowns, radio button inputs, etc.
  - They can also run any number in parallel, for user convenience
- `pyyaml` as a dependency, to automatically parse .yaml/.yml files for you when downloading them
- The ability to delete `Branches` (although not state managed due to the multi-component element of repo_id + branch_id)

### Changed

- Errors have been moved out of utils into their own file for easier imports (ado_wrapper.errors)
- New resources are now automatically added to state files when needed, no longer crashing

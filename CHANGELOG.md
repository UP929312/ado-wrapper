# Changelog

## v1.14.0

### Added

- When creating/fetching `Run`s, you can now see the `Run`s `Build Definition` id.
- More tests for `Search`es.
- `Run.get_run_stage_results` to get a list of each job's status/result

### Changed

- Ran Flake8 over the codebase, many non-code but formatting changes
- `Search` is now called `CodeSearch` (to allow for other search types in the future)

---

## v1.13.0

### Added

- `Run`s now support stages to include and variables (as opposed to template parameters)
- `Run`s now tests `run_all_and_capture_results_simultaneously`.

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

---

## v1.9.0

### Added

- `AuditLog`s, the ability to search and filter by Audit Logs.
- `MergeBranchPolicy` are now importable directly from root.

---

## v1.8.0

### Added

- `Branch`es now have `creator` attribute, to identify out who created the branch.
- `UserPermission`s `set_by_group_descriptor` has been added, to set a group's perms on a repo.

### Changed

- `MergePolicies` now work for repos with previously no policies set on them
- When trying to set default reviewers, it now raises a `ConfigurationError` on exception.
- When trying to set branch policies, it'll now warn for incorrect perms, and raise a `ConfigurationError` exception.
- When trying to set individual user perms on a repo, an `InvalidPermissionsError` permission is raised if the PAT token doesn't have perms.
- `UserPermission`s `set_by_subject_email` has been renamed to `set_by_user_email`.

---

## v1.7.0

### Added

- Added `AgentPool`s (cannot create or delete yet)
- The ability to fetch repos by default reviewers, using `Repo.get_all_repos_with_required_reviewer()`
- The ability to fetch latest build by definition using `BuildDefinition.get_latest_build_by_definition()`

### Changed

- `Group`s `group_id` has been remapped to `domain` to align better with the official API.

---

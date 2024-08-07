# Changelog

## v1.19.1

### Changed

- `get_default_reviewers_by_repo_id` has been renamed to `get_default_reviewer_policy_by_repo_id` (and re-implemented)
- Added `MergeTypeRestrictionPolicy` to the __all__ so it can be imported easily

---

## v1.19.0

### Added

- `Build.get_all()` now supports a limit, as well as a filter for build status (e.g. completed, failed, etc)
- `MergeTypeRestrictionPolicy`s can now be set for repos, disallowing non-squashes, fast-forwards, etc.
- Added `MergePolicies.get_all_repo_policies()` to fetch all the policies relating to a repo, e.g. required reviewers, allowed merge types, merge requirements, etc.

### Changed

- The codebase is now covered by `Bandit`, a code analysis and security tool.
- Slightly more of the codebase is tested (which should mean slightly less library errors)

---

## v1.18.0

### Added

- Build's now store the agent pool id, under `pool_id` (although it's sometimes `None`)
- Added `BuildTimeline`s, which contain a large amount of data of a build, each checkpoint, stage, step, phase, job, etc.
- Added the Ability to get a `BuildTimeline`s retries automatically, by passing in fetch_retries=True (although this is an expensive operation)
- Added `skipped` as another option to the `RunResult` literal (to align it more with the A.P.I.)

### Changed

- How a lot of extracting and converting from json is for instance's `get_by_id` (and similar functions) to better respond to empty strings (now raises `UnknownError`)
- Added __all__ to better set exports for modules.
- Renamed `Artifacts` test class from `Build` to `BuildArtifact`
- Removed an eroneous print statement in `BuildArtifact`s

---

## v1.17.0

### Added

- `Build.get_build_log_content()` to get the output from a build log terminal.
- `Run` has also got the same function (just aliased)
- Build Artifacts, and the ability to get them all, get individuals, and get the individual file contents.
- Trying to make resources with the same identifier (e.g. repos with the same name) now gives a `ResourceAlreadyExists` error.

### Changed

- The predefined StateManager's classes typing has been massively improved to remove a lot of type: ignores
- All cases of from __future__ import annotations have been removed. All imported types are now wrapped in "strings"
- `PullRequestCommentThread`'s `create` now has the proper return type
- Some resources raise Configuration Error rather than use asserts (`AuditLog.get_all()`, `CodeSearch.get_by_search_string`, `ServiceEndpoint.create()`)
- Removed a lot of NotImplementedError functions, these now won't show up and then instantly error.

---

## v1.16.0

### Added

- `typing_info.py`, which allows users to import types for type hinting in their scripts.
- Tests for Permissions
- `Organisation`s, specifically the ability to get an object by name (and hence extract `organisation_id`)
- The client now has `.ado_org_id` string, which is used when fetching personal access tokens.
- The ability to fetch Personal Access Tokens (to see when they'll expire, and what perms they have)

### Changed

- Changed the return type of CodeSearch's `get_by_search_string` from Any to `list[CodeSearch]`
- Removed the "namespace_id" from the permissions as it was always it's parents namespace_id, use group_namespace_id instead
- Fixed TestRun/test_get_by_id from not removing an old run.
- The StateManager is less fussy about trying to remove resources from a state without that resource's key.
- Commit's `ChangeType` has been renamed to `CommitChangeType` for the same reason
- Permission's `ActionType` has been renamed to `PermissionActionType` so when importing for typing will be more specific
- Repo's `ActionType` & `PermissionType` have been renamed to `RepoPermsActionType` & `RepoPermissionType` respectively
- Internally, `ado_client.ado_org` has been remapped to `ado_client.ado_org_name`. For backwards compability reasons, `ado_client.ado_org` still exists but will soon be removed.
- `ado_client.ado_project` has been remapped to `ado_client.ado_project_name` (to better reflect what it is) and allow the project object to replace it in the future. For backwards compability reasons, `ado_client.ado_project` still exists but will soon be removed.

---

## v1.15.0

### Added

- The ability to fetch `Assigned to my teams` PullRequest list using `PullRequest.get_my_pull_requests()`
- Can be altered permantly using `PullRequest.set_my_pull_requests_included_teams()`
- The ability to get the permission set by the provider PAT, e.g. Git Repo -> Contribute. using `Permission.get_by_project()`
- Started work on a feature to decorate functions with `@required_perms()` which will pre-emptively warn the user for which perm they need.

### Changed

- Unmarking a PR as draft now works properly (previously it would try to re-mark as draft)
- Slightly improved the error message when the API raises a 401 (raises an InvalidPermissionsError)

---

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

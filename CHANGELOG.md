# Changelog

## v1.30.0

### Added

- `Task.get_log_content()` which mirrors `Run.get_run_log_content()`, but almost acting as an alias
- The ability to get the amount of free and purchased parallel jobs and hosted agents for a project, using `Project.get_build_queue_settings()`
- The ability to get the retention for builds and releases for a project, using `Project.get_retention_policy_settings()`

---

## v1.29.0

### Added

- The requirement to elevate privileges through a new context manager `with ado_client.elevated_privileges():` for creation and deletion of projects.
- When using `BuildTimeline`s, the parent job and stages (where appropriate)'s id and name are automatically added to the item's attributes.

### Changed

- `Run.run_and_wait_until_completion()` and it's sibling functions will now capture the error if it fails to fetch, rather than killing all the runs.
- `ProjectVisibilityType, TemplateTypes, ProjectStatus, ProjectRepositorySettingType` are all added to typing_info.py
- `VoteOptions` is also added to typing_info.py.
- Remove `Run`'s `get_task_parents` in favour of using `.parent_job_name` and `parent_stage_name` (as properties, less fetches).

---

## v1.28.0

### Added

- `BuildTimeline.get_tasks_by_name(ado_client, <build_id>, <task_name>)` which returns all tasks with that task name.
- The polling interval for runs via run_and_wait_until_complete and sibling functions is now configurable by passing in a new arg to the ado_client object (run_polling_interval_seconds)
- The polling rate for a run can be temporarily changed using the new context manager, ado_client.temporary_polling_interval(<interval_in_seconds>)
- ado_client.assume_project(<project_name>) which can be used to assume a different ADO project, changing where function calls are made from.

### Changed

- `BuildTimeline`s now hide a lot more of it's attributes in strs/reprs.
- `examples.md` now show dictionary types, and unpacks tuples for you.
- `BuildTimeline` now has a new alias, `get_by_build_id`.
- Slightly optimised `BuildTime.get_all_by_types()`

---

## v1.27.0

### Added

- AgentPools.create are now creatable and no longer raises NotImplementedError, as does delete_by_id.
- Added all the gitignore templates to Commits, and also to repo creation as a new argument.
- MergePolicyDefaultReviewer now converts from origin_ids to local_ids, which internally means it'll work on side projects/orgs.
- When creating a run with run variables, it'll now warn you if the projects repo settings prevents runtime vars.
- Teams can not be created and deleted rather than raising NotImplementedError (and are state manageable).

### Changed

- AgentPool.get_by_name now works properly, and doesn't filter by id anymore.
- Commit.create now defaults to "Add" change_type, and a default commit message.
- More assert statements have been replaced with full error handling and messages.

---

## v1.26.0

### Added

- Can now create an empty branch, so it will no longer point you to Commit.create instead.
- Creating a build_definition without passing in agent_pool_id will use the Azure AgentPools
- Creating a release without passing in agent_pool_id will use the Azure AgentPools
- Groups are now creatable, and deletable and won't raise NotImplementedError
- AdoUsers now have a few more utility functions, like getting by id, or search string.
- VariableGroups can now be fetched by value, using `get_variable_group_contents`, but this takes 20-60 seconds to run.
- Runs now have a function which is ran with the current run everytime the run is polled (which can be used for logging or dispatching)

### Changed

- Improved functions which call the Hierarchy endpoints to use a new builder, making that code better
- Optimised client startup time (don't fetch org anymore, or perms, but now fetch project pipeline settings)
- When calling Build.get_build_log_content with invalid stages, it now tells you the possible options
- Build's `get_root_stage_names` is now also in Runs.

---

## v1.25.0

### Added

- `remove_ansi_codes`, a utils function to removr all ansi colour codes from a string, uses `ANSI_RE_PATTERN`.
- Project's now have `visibility` and `creation_status` when fetching by id or name.
- Improved StateManger.load_all_resources_with_prefix_into_state to include more resources, and work over all better
- Added the ability to allow a variable group to be used for a build build_definition
- Added the ability to create a build definition with Hierarchy, which allows additional functionality.
- Added HierarchyCreatedBuildDefinition to corrospond with the informaton above
- Projects are now creatable, and deletable.
- You can also get and set a project's pipeline settings
- Also able to get and set a project's repository settings

### Changed

- `Removed` all plan logic, this was never fully implemented and was making things more complicated.
- Fixed `StateManagedResource._create`'s refetch argument.
- BuildDefinition.get_all_stages() now has better errors for creation without Hierarchy mode.
- Build.create no longer takes the `permit_use_of_var_groups` argument.
- Build's `approve_environment_for_pipeline` now has better error messages.
- `ansi_re_pattern` and `datetime_re_pattern` have been renamed to `ANSI_RE_PATTERN` and `DATETIME_RE_PATTERN` respectively.
- If search is not enabled for a project, it'll now error when trying to do a new search.

---

## v1.24.0

### Added

- `Build`'s get_environment_approvals now doesn't supply pipelines with dependencies anymore (to prevent an issue).
- Ability to get `Build.get_root_stage_names()` to get all stages with no dependencies, at root level.

### Changed

- `Run.create()` with stages_to_run now no longer mutates the list it takes, instead shadowing it and discarding at the end.
- Improved error message in `Run.get_task_parents`.

---

## v1.23.0

### Added

- `PullRequest.create()` now accepts a target branch, this defaults to main, but can be overriden to any branch, including master.
- Better documentation around which Build methods return stages/jobs/task `display_name` versus returning their `internal_name`

### Changed

- `BuildTimeline`s "identifier" has been renamed to `internal_name`.
- Repo's utility function "create_pull_request" now accepts a target branch name, and is_draft for setting it to draft.

---

## v1.22.0

### Added

- `BuildDefinition.get_environment_approvals()`, which allows you to get a mapping of stage_name -> approval_id.
- Using the above with `approve_environment_for_pipeline` should allow you to approve environment stages, takes a stage_name

### Changed

- Builds and BuildDefinitions have be split into their own files, it was getting to cluttered with all the new build features. This shouldn't change anything, since you can import both of them from the root directory (e.g. from ado_wrapper import Build, BuildDefinition) like before.
- `BuildDefinition`s __str__ method is now autogenerated by dataclasses.
- Docs are now running a newer version, so should be more up to date.

---

## v1.21.1

### Added

- `BuildDefinition.get_all_stages()`'s stages_to_run now converts display names to internal names if provided.

---

## v1.21.0

### Added

- `BuildDefinition.get_all_stages()` now takes template_parameters, whereas before it would simply use the defaults for that pipeline.
- A warning when trying to use an invalid access token.

### Changed

- Fetching a list of `PersonalAccessTokens` using `PersonalAccessToken.get_access_tokens()` now works for days in the month < 10 (e.g. 1st->9th)
- Finally removed the deprecated `AdoClient.ado_org` and `AdoClient.ado_project`, use `ado_org_name` and `ado_project_name` instead.
- Fixed some tests regarding a renamed team (should create test environment for this reason, maybe one day)

---

## v1.20.0

### Added

- The `ado_wrapper.utils` import now contains multiple ansi colour codes for use with build logs.
- The ability to do `BuildTimeline.get_all_by_types()`, which returns multiple types (e.g. stages, jobs)
- The ability to do `Build.get_stages_jobs_tasks()`, which returns a nested dictionary of all the stages, jobs and tasks for a certain build.
- `Run.get_task_parents()`, which returns the ids and names of any pipeline run's task's parents (e.g. stage & job)

### Changed

- Run's created off branches should now work again.
- `Build.get_build_log_content()` now requires stage, job and task, since previously you could have the same job and task (but different stage)
- The internal `_get_all_logs_ids` is now much more nicely coded, and doesn't rely on parsing HTML.
- `BuildDefinitionStage` has been renamed from `BuildDefinitionStep`, it has always reflected stages.

---

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

## v1.6.0

### Added

-

### Changed

-

---

## v1.5.0

### Added

-

### Changed

-

---

## v1.4.0

### Added

-

### Changed

-

---

## v1.3.0

### Added

-

### Changed

-

---

## v1.3.0

### Added

-

### Changed

-

---

## v1.2.0

### Added

-

### Changed

-

---

## v1.1.3

- <https://github.com/UP929312/ado-wrapper/commits/master/?before=0e09dd48ea51735b10d91b800e8381af9dd14c14+70>

### Changed

- `MergePolicy.get_branch_policy()` now returns None if no branch policy is set.

---

## v1.1.2

### Added

- StateManageResources "create" now has a refetch, for resources that don't return proper values when creating and need a `.get_by_id`

### Changed

- Trying to fetch contents from an empty repo now raises a proper error message.
- Fixed a bug with allowing merging with policies (ignored for now)

---

## v1.1.0

### Added

- Added `Environments`.

### Changed

- Fixed the AnnotatedTags test name from Test -> TestAnnotatedTags.

---

## v1.0.0

### Added

- `AnnotatedTag`s, which are repo's Tags for versioning.
- Better error handling for > 300 error codes when creating resources.

### Changed

- Removed `description` from the repr for `PullRequest`s.
- `PullRequest.get_all_by_repo_id()` now uses the super() method.
- Remove `Group`s override for __str__
- Removed `requested_by`, `build_repo`, `parameters`, `start_time`, `end_time` from Build's repr.
- Removed `is_main`, `is_protected`, `is_deleted` from branches attributes, they were buggy/not always present so removed.

---

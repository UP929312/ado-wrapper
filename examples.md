

# Examples

All these examples assume an already created AdoClient, perhaps similar to this:

```py
from ado_wrapper import AdoClient

with open("credentials.txt", "r") as file:
    email, ado_access_token, ado_org, ado_project = file.read().split("\n")

ado_client = AdoClient(email, ado_access_token, ado_org, ado_project)
```

-----
# AdoUser
<details>

```py
# Create
ado_user = AdoUser.create(ado_client, <member_name>, <member_email>)

# Delete
ado_user.delete(ado_client)

# Delete By Id
ado_user.delete_by_id(ado_client, <member_id>)

# Get All
ado_users = AdoUser.get_all(ado_client)

# Get By Email
ado_user = AdoUser.get_by_email(ado_client, <member_email>)

# Get By Id
ado_user = AdoUser.get_by_id(ado_client, <descriptor_id>)

# Get By Name
ado_user = AdoUser.get_by_name(ado_client, <member_name>)

# Update
ado_user.update(ado_client, <update_action>, <url>, <attribute_name>, <attribute_value>, <params>)


```
</details>

-----
# AnnotatedTag
<details>

```py
# Create
annotated_tag = AnnotatedTag.create(ado_client, <repo_id>, <name>, <message>, <object_id>)

# Delete
annotated_tag.delete(ado_client)

# Delete By Id
annotated_tag.delete_by_id(ado_client, <object_id>)

# Get All By Repo
annotated_tags = AnnotatedTag.get_all_by_repo(ado_client, <repo_name>)

# Get By Id
annotated_tag = AnnotatedTag.get_by_id(ado_client, <repo_id>, <branch_id>)

# Get By Name
annotated_tag = AnnotatedTag.get_by_name(ado_client, <repo_id>, <tag_name>)

# Update
annotated_tag.update(ado_client, <update_action>, <url>, <attribute_name>, <attribute_value>, <params>)


```
</details>

-----
# Branch
<details>

```py
# Create
branch = Branch.create(ado_client, <repo_id>, <branch_name>, <source_branch>)

# Delete
branch.delete(ado_client)

# Delete By Id
branch.delete_by_id(ado_client, <repo_id>, <branch_id>)

# Get All By Repo
branchs = Branch.get_all_by_repo(ado_client, <repo_id>)

# Get By Id
branch = Branch.get_by_id(ado_client, <repo_id>, <branch_id>)

# Get By Name
branch = Branch.get_by_name(ado_client, <repo_id>, <branch_name>)

# Get Main Branch
branch = Branch.get_main_branch(ado_client, <repo_id>)

# Update
branch.update(ado_client, <update_action>, <url>, <attribute_name>, <attribute_value>, <params>)


```
</details>

-----
# Build
<details>

```py
# Allow On Environment
<class ado_wrapper.resources.environment._pipeline_authorisation> = Build.allow_on_environment(ado_client, <definition_id>, <environment_id>)

# Create
build = Build.create(ado_client, <definition_id>, <source_branch>, <permit_use_of_var_groups>)

# Create And Wait Until Completion
build = Build.create_and_wait_until_completion(ado_client, <definition_id>, <branch_name>, <max_timeout_seconds>)

# Delete
build.delete(ado_client)

# Delete All Leases
build.delete_all_leases(ado_client, <build_id>)

# Delete By Id
build.delete_by_id(ado_client, <build_id>)

# Get All
builds = Build.get_all(ado_client)

# Get All By Definition
builds = Build.get_all_by_definition(ado_client, <definition_id>)

# Get By Id
build = Build.get_by_id(ado_client, <build_id>)

# Get Latest
build = Build.get_latest(ado_client, <definition_id>)

# Priority
build = Build.priority(ado_client, <definition_id>)

# Queue Time
build = Build.queue_time(ado_client, <definition_id>)

# Reason
build = Build.reason(ado_client, <definition_id>)

# Update
build.update(ado_client, <attribute_name>, <attribute_value>)


```
</details>

-----
# BuildDefinition
<details>

```py
# Create
build_definition = BuildDefinition.create(ado_client, <name>, <repo_id>, <repo_name>, <path_to_pipeline>, <description>, <agent_pool_id>, <variable_groups>, <branch_name>)

# Delete
build_definition.delete(ado_client)

# Delete By Id
build_definition.delete_by_id(ado_client, <resource_id>)

# Get All
build_definitions = BuildDefinition.get_all(ado_client)

# Get All Builds By Definition
builds = BuildDefinition.get_all_builds_by_definition(ado_client)

# Get All By Name
build_definitions = BuildDefinition.get_all_by_name(ado_client, <name>)

# Get All By Repo Id
build_definitions = BuildDefinition.get_all_by_repo_id(ado_client, <repo_id>)

# Get By Id
build_definition = BuildDefinition.get_by_id(ado_client, <build_definition_id>)

# Process
build_definition = BuildDefinition.process(ado_client, <build_definition_id>)

# Revision
build_definition = BuildDefinition.revision(ado_client, <build_definition_id>)

# Update
build_definition.update(ado_client, <attribute_name>, <attribute_value>)


```
</details>

-----
# BuildRepository
<details>

```py
# Checkout Submodules
build_repository.checkout_submodules(ado_client, <attribute_name>, <attribute_value>)

# Clean
build_repository.clean(ado_client, <attribute_name>, <attribute_value>)

# Name
build_repository.name(ado_client, <attribute_name>, <attribute_value>)

# Type
build_repository.type(ado_client, <attribute_name>, <attribute_value>)


```
</details>

-----
# Commit
<details>

```py
# Add Initial Readme
commit = Commit.add_initial_readme(ado_client, <repo_id>)

# Create
commit = Commit.create(ado_client, <repo_id>, <from_branch_name>, <to_branch_name>, <updates>, <change_type>, <commit_message>)

# Delete
commit.delete(ado_client)

# Delete By Id
commit.delete_by_id(ado_client, <commit_id>)

# Get All By Repo
commits = Commit.get_all_by_repo(ado_client, <repo_id>, <branch_name>)

# Get By Id
commit = Commit.get_by_id(ado_client, <repo_id>, <commit_id>)

# Get Latest By Repo
commit = Commit.get_latest_by_repo(ado_client, <repo_id>, <branch_name>)

# Update
commit.update(ado_client, <update_action>, <url>, <attribute_name>, <attribute_value>, <params>)


```
</details>

-----
# Environment
<details>

```py
# Add Pipeline Permission
pipeline_authorisation = Environment.add_pipeline_permission(ado_client, <pipeline_id>)

# Create
environment = Environment.create(ado_client, <name>, <description>)

# Delete
environment.delete(ado_client)

# Delete By Id
environment.delete_by_id(ado_client, <environment_id>)

# Get All
environments = Environment.get_all(ado_client)

# Get By Id
environment = Environment.get_by_id(ado_client, <environment_id>)

# Get By Name
environment = Environment.get_by_name(ado_client, <name>)

# Get Pipeline Permissions
pipeline_authorisations = Environment.get_pipeline_permissions(ado_client)

# Remove Pipeline Permissions
environment.remove_pipeline_permissions(ado_client, <pipeline_id>)

# Update
environment.update(ado_client, <attribute_name>, <attribute_value>)


```
</details>

-----
# Group
<details>

```py
# Create
group = Group.create(ado_client, <name>)

# Delete
group.delete(ado_client)

# Delete By Id
group.delete_by_id(ado_client, <group_id>)

# Get All
groups = Group.get_all(ado_client)

# Get By Id
group = Group.get_by_id(ado_client, <group_descriptor>)

# Get By Name
group = Group.get_by_name(ado_client, <group_name>)

# Update
group.update(ado_client, <update_action>, <url>, <attribute_name>, <attribute_value>, <params>)


```
</details>

-----
# Member
<details>

```py
# Create
member = Member.create(ado_client, <member_name>, <member_email>)

# Delete
member.delete(ado_client)

# Delete By Id
member.delete_by_id(ado_client, <member_id>)

# Get By Id
member = Member.get_by_id(ado_client, <member_id>)

# Update
member.update(ado_client, <update_action>, <url>, <attribute_name>, <attribute_value>, <params>)


```
</details>

-----
# MergeBranchPolicy
<details>

```py
# Delete
merge_branch_policy.delete(ado_client)

# Delete By Id
merge_branch_policy.delete_by_id(ado_client, <url>, <resource_id>)

# Get Branch Policy
merge_branch_policy = MergeBranchPolicy.get_branch_policy(ado_client, <repo_id>, <branch_name>)

# Set Branch Policy
merge_branch_policy.set_branch_policy(ado_client, <repo_id>, <minimum_approver_count>, <creator_vote_counts>, <prohibit_last_pushers_vote>, <allow_completion_with_rejects>, <when_new_changes_are_pushed>, <branch_name>)

# Update
merge_branch_policy.update(ado_client, <update_action>, <url>, <attribute_name>, <attribute_value>, <params>)


```
</details>

-----
# MergePolicies
<details>

```py
# Add Default Reviewer
merge_policies.add_default_reviewer(ado_client, <repo_id>, <reviewer_id>, <is_required>, <branch_name>)

# Delete
merge_policies.delete(ado_client)

# Delete By Id
merge_policies.delete_by_id(ado_client, <url>, <resource_id>)

# Get All Branch Policies By Repo Id
merge_branch_policys = MergePolicies.get_all_branch_policies_by_repo_id(ado_client, <repo_id>, <branch_name>)

# Get All By Repo Id
merge_policy_default_reviewers = MergePolicies.get_all_by_repo_id(ado_client, <repo_id>, <branch_name>)

# Get Branch Policy
merge_branch_policy = MergePolicies.get_branch_policy(ado_client, <repo_id>, <branch_name>)

# Get Default Reviewers
reviewers = MergePolicies.get_default_reviewers(ado_client, <repo_id>, <branch_name>)

# Get Default Reviewers By Repo Id
merge_policy_default_reviewers = MergePolicies.get_default_reviewers_by_repo_id(ado_client, <repo_id>, <branch_name>)

# Remove Default Reviewer
merge_policies.remove_default_reviewer(ado_client, <repo_id>, <reviewer_id>, <branch_name>)

# Set Branch Policy
merge_policies.set_branch_policy(ado_client, <repo_id>, <minimum_approver_count>, <creator_vote_counts>, <prohibit_last_pushers_vote>, <allow_completion_with_rejects>, <when_new_changes_are_pushed>, <branch_name>)

# Update
merge_policies.update(ado_client, <update_action>, <url>, <attribute_name>, <attribute_value>, <params>)


```
</details>

-----
# MergePolicyDefaultReviewer
<details>

```py
# Add Default Reviewer
merge_policy_default_reviewer.add_default_reviewer(ado_client, <repo_id>, <reviewer_id>, <is_required>, <branch_name>)

# Delete
merge_policy_default_reviewer.delete(ado_client)

# Delete By Id
merge_policy_default_reviewer.delete_by_id(ado_client, <url>, <resource_id>)

# Get Default Reviewers
reviewers = MergePolicyDefaultReviewer.get_default_reviewers(ado_client, <repo_id>, <branch_name>)

# Remove Default Reviewer
merge_policy_default_reviewer.remove_default_reviewer(ado_client, <repo_id>, <reviewer_id>, <branch_name>)

# Update
merge_policy_default_reviewer.update(ado_client, <update_action>, <url>, <attribute_name>, <attribute_value>, <params>)


```
</details>

-----
# PipelineAuthorisation
<details>

```py
# Create
pipeline_authorisation = PipelineAuthorisation.create(ado_client, <environment_id>, <pipeline_id>, <authorized>)

# Delete By Id
pipeline_authorisation.delete_by_id(ado_client, <environment_id>, <pipeline_authorisation_id>)

# Get All For Environment
pipeline_authorisations = PipelineAuthorisation.get_all_for_environment(ado_client, <environment_id>)

# Update
pipeline_authorisation.update(ado_client, <authorized>)


```
</details>

-----
# Project
<details>

```py
# Create
project = Project.create(ado_client, <project_name>, <project_description>)

# Delete
project.delete(ado_client)

# Delete By Id
project.delete_by_id(ado_client, <project_id>)

# Get All
projects = Project.get_all(ado_client)

# Get By Id
project = Project.get_by_id(ado_client, <project_id>)

# Get By Name
project = Project.get_by_name(ado_client, <project_name>)

# Last Update Time
project = Project.last_update_time(ado_client, <project_name>)

# Update
project.update(ado_client, <update_action>, <url>, <attribute_name>, <attribute_value>, <params>)


```
</details>

-----
# PullRequest
<details>

```py
# Add Reviewer
pull_request.add_reviewer(ado_client, <reviewer_id>)

# Add Reviewer Static
pull_request.add_reviewer_static(ado_client, <repo_id>, <pull_request_id>, <reviewer_id>)

# Close
pull_request.close(ado_client)

# Close Date
pull_request.close_date(ado_client)

# Create
pull_request = PullRequest.create(ado_client, <repo_id>, <from_branch_name>, <pull_request_title>, <pull_request_description>, <is_draft>)

# Delete
pull_request.delete(ado_client)

# Delete By Id
pull_request.delete_by_id(ado_client, <pull_request_id>)

# Get All
pull_requests = PullRequest.get_all(ado_client, <status>)

# Get All By Author
pull_requests = PullRequest.get_all_by_author(ado_client, <author_email>, <status>)

# Get All By Repo Id
pull_requests = PullRequest.get_all_by_repo_id(ado_client, <repo_id>, <status>)

# Get By Id
pull_request = PullRequest.get_by_id(ado_client, <pull_request_id>)

# Get Comment Threads
pull_request_comment_threads = PullRequest.get_comment_threads(ado_client, <ignore_system_messages>)

# Get Comments
pull_request_comments = PullRequest.get_comments(ado_client, <ignore_system_messages>)

# Get My Pull Requests
pull_requests = PullRequest.get_my_pull_requests(ado_client)

# Get Reviewers
members = PullRequest.get_reviewers(ado_client)

# Is Draft
members = PullRequest.is_draft(ado_client)

# Mark As Draft
pull_request.mark_as_draft(ado_client)

# Merge Status
pull_request.merge_status(ado_client)

# Post Comment
pull_request_comment = PullRequest.post_comment(ado_client, <content>)

# Unmark As Draft
pull_request.unmark_as_draft(ado_client)

# Update
pull_request.update(ado_client, <attribute_name>, <attribute_value>)


```
</details>

-----
# Release
<details>

```py
# Create
release = Release.create(ado_client, <definition_id>, <description>)

# Delete
release.delete(ado_client)

# Delete By Id
release.delete_by_id(ado_client, <release_id>)

# Get All
releases = Release.get_all(ado_client, <definition_id>)

# Get By Id
release = Release.get_by_id(ado_client, <release_id>)

# Keep Forever
release = Release.keep_forever(ado_client, <release_id>)

# Update
release.update(ado_client, <update_action>, <url>, <attribute_name>, <attribute_value>, <params>)


```
</details>

-----
# ReleaseDefinition
<details>

```py
# Agent Pool Id
release_definition.agent_pool_id(ado_client, <update_action>, <url>, <attribute_name>, <attribute_value>, <params>)

# Create
release_definition = ReleaseDefinition.create(ado_client, <name>, <variable_group_ids>, <agent_pool_id>)

# Delete
release_definition.delete(ado_client)

# Delete By Id
release_definition.delete_by_id(ado_client, <release_definition_id>)

# Get All
release_definitions = ReleaseDefinition.get_all(ado_client)

# Get All Releases For Definition
releases = ReleaseDefinition.get_all_releases_for_definition(ado_client, <definition_id>)

# Get By Id
release_definition = ReleaseDefinition.get_by_id(ado_client, <release_definition_id>)

# Is Disabled
release_definition = ReleaseDefinition.is_disabled(ado_client, <release_definition_id>)

# Revision
release_definition = ReleaseDefinition.revision(ado_client, <release_definition_id>)

# Update
release_definition.update(ado_client, <attribute_name>, <attribute_value>)


```
</details>

-----
# Repo
<details>

```py
# Create
repo = Repo.create(ado_client, <name>, <include_readme>)

# Create Pull Request
pull_request = Repo.create_pull_request(ado_client, <branch_name>, <pull_request_title>, <pull_request_description>)

# Default Branch
pull_request = Repo.default_branch(ado_client, <branch_name>, <pull_request_title>, <pull_request_description>)

# Delete
repo.delete(ado_client)

# Delete By Id
repo.delete_by_id(ado_client, <repo_id>)

# Get All
repos = Repo.get_all(ado_client)

# Get All Pull Requests
pull_requests = Repo.get_all_pull_requests(ado_client, <repo_id>, <status>)

# Get Branch Merge Policy
merge_branch_policy = Repo.get_branch_merge_policy(ado_client, <repo_id>, <branch_name>)

# Get By Id
repo = Repo.get_by_id(ado_client, <repo_id>)

# Get By Name
repo = Repo.get_by_name(ado_client, <repo_name>)

# Get Content Static
dictionary = Repo.get_content_static(ado_client, <repo_id>, <file_types>, <branch_name>)

# Get Contents
dictionary = Repo.get_contents(ado_client, <file_types>, <branch_name>)

# Get File
string_var = Repo.get_file(ado_client, <file_path>, <branch_name>)

# Is Disabled
string_var = Repo.is_disabled(ado_client, <file_path>, <branch_name>)

# Set Branch Merge Policy
merge_policies = Repo.set_branch_merge_policy(ado_client, <repo_id>, <minimum_approver_count>, <creator_vote_counts>, <prohibit_last_pushers_vote>, <allow_completion_with_rejects>, <when_new_changes_are_pushed>, <branch_name>)

# Update
repo.update(ado_client, <attribute_name>, <attribute_value>)


```
</details>

-----
# Reviewer
<details>

```py
# Create
member = Reviewer.create(ado_client, <member_name>, <member_email>)

# Delete
reviewer.delete(ado_client)

# Delete By Id
reviewer.delete_by_id(ado_client, <member_id>)

# Get By Id
member = Reviewer.get_by_id(ado_client, <member_id>)

# Update
reviewer.update(ado_client, <update_action>, <url>, <attribute_name>, <attribute_value>, <params>)


```
</details>

-----
# ServiceEndpoint
<details>

```py
# Create
service_endpoint = ServiceEndpoint.create(ado_client, <name>, <service_endpoint_type>, <url>, <username>, <password>, <access_token>)

# Delete
service_endpoint.delete(ado_client)

# Delete By Id
service_endpoint.delete_by_id(ado_client, <service_endpoint_id>)

# Get All
service_endpoints = ServiceEndpoint.get_all(ado_client)

# Get By Id
service_endpoint = ServiceEndpoint.get_by_id(ado_client, <repo_id>)

# Get By Name
service_endpoint = ServiceEndpoint.get_by_name(ado_client, <name>)

# Update
service_endpoint.update(ado_client, <attribute_name>, <attribute_value>)

# Update Pipeline Perms
dictionary = ServiceEndpoint.update_pipeline_perms(ado_client, <pipeline_id>)


```
</details>

-----
# Team
<details>

```py
# Create
team = Team.create(ado_client, <name>, <description>)

# Delete
team.delete(ado_client)

# Delete By Id
team.delete_by_id(ado_client, <team_id>)

# Get All
teams = Team.get_all(ado_client)

# Get By Id
team = Team.get_by_id(ado_client, <team_id>)

# Get By Name
team = Team.get_by_name(ado_client, <team_name>)

# Get Members
team_members = Team.get_members(ado_client)

# Update
team.update(ado_client, <attribute_name>, <attribute_value>)


```
</details>

-----
# TeamMember
<details>

```py
# Create
member = TeamMember.create(ado_client, <member_name>, <member_email>)

# Delete
team_member.delete(ado_client)

# Delete By Id
team_member.delete_by_id(ado_client, <member_id>)

# Get By Id
member = TeamMember.get_by_id(ado_client, <member_id>)

# Update
team_member.update(ado_client, <update_action>, <url>, <attribute_name>, <attribute_value>, <params>)


```
</details>

-----
# VariableGroup
<details>

```py
# Create
variable_group = VariableGroup.create(ado_client, <variable_group_name>, <variable_group_description>, <variables>)

# Delete
variable_group.delete(ado_client)

# Delete By Id
variable_group.delete_by_id(ado_client, <variable_group_id>)

# Get All
variable_groups = VariableGroup.get_all(ado_client)

# Get By Id
variable_group = VariableGroup.get_by_id(ado_client, <variable_group_id>)

# Get By Name
variable_group = VariableGroup.get_by_name(ado_client, <name>)

# Modified On
variable_group = VariableGroup.modified_on(ado_client, <name>)

# Update
variable_group.update(ado_client, <attribute_name>, <attribute_value>)


```
</details>


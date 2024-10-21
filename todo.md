# To do

Releases need vigerous testing - kinda wip, ReleaseDef - Update

A push is when someone has multiple commits and they do a git push (to a branch), it can be multiple sub-commits
<https://learn.microsoft.com/en-us/rest/api/azure/devops/git/pushes/get?view=azure-devops-rest-7.1&tabs=HTTP#gitpush>

Rollback a commit? Tricky...
I guess I could fetch the repo by a certain commit, and find the difference for all the files, and then make a commit like that?

Maybe add the alternative way? I.E. if it's changed in real resources

Teams.get_members(recursive=True)  Not sure that Teams are the right thing, maybe Groups? Idk

We can maybe use run id to delete all by run id? "prevent_destroy", "ignore_changes"
MORE WORK ON LIFECYCLE!

This?
<https://www.reddit.com/r/ado_wrapper/comments/xj56gs/complete_pull_request_with_bypass_policy_via_api/>

Commits/Branches are the only things that don't have a generic `get_all` EDIT: Few more things now also don't.

<https://stackoverflow.com/questions/77522387/approving-pipeline-stage-azure-devops-via-api>
Auto approve via token ^

<https://learn.microsoft.com/en-us/azure/devops/pipelines/process/approvals?view=azure-devops&tabs=check-pass>
<https://stackoverflow.com/a/61519132>
Pipeline perms, currently our pipelines are approval-able by almost anyone, we should be able to set the perms

AdoUser - Get all, doesn't work with pagination, implement pagination

Hmmmmm, it appears that when creating a variable group, it doesn't return the created by or modified by with enough data.
This is different from the get_by_id, because the get_by_id gets the creator, but the creation return doesn't the data, grr...

More tests around:
Service connections perms on pipelines (done, not tested)
TestStateManager needs some work
build_defs/allow_on_environment Needs testing - Maybe better to use Build.approve_environment?
AgentPools create/delete and testing  
AuditLogs Tests - Only have perms in UK, dang... New systems???  
Test state_manager.py more?  
Test __main__.py  

Add all the required perms with @required_perms - On hold, perms seem to be user based, not token based

Can Jobs have logs, not just the tasks? Maybe the stage can have logs?

Build, Fetch: &maxTime={maxTime}&minTime={minTime}"

Docs have functions which raise NotImplemented, inspect and remove if they do?

Pat token stuffs, commit rollback, artifact stuffs

Somehow detect expired tokens? simple_ado???
simple_ado.exceptions.ADOHTTPException: ADO returned a non-200 status code, configuration=<simple_ado.http_client.ADOHTTPClient object at 0x1025de310>, status_code=401, text=Access Denied: The Personal Access Token used has expired.

UNSURE HOW TO DO ABOVE
But because we can fetch access_tokens, maybe we can instead check if the current one's expired? Somehow?

When creating yaml, if you don't provide stages, it creates one called "__default"
`ado_wrapper.errors.ConfigurationError: Wrong stage name or job name combination (case sensitive), received Jobs/EchoEnvironmentVariables/Echo Modified Keys and ValuesOptions were __default/EchoEnvironmentVariables/Initialize job, __default/EchoEnvironmentVariables/Echo Modified Keys and Values`

For each test file, have a zzz_cleanup() function which empties state?
Maybe each test could inherit from a parent class which has this?

When creating variable groups, deciding if they're secret or not?

Never test get_environment_approvals

rather than "requires initialisation", maybe make .ado_project_id a property and put it there?
Perhaps have some system relating to intents? Which pre-loads a bunch of stuff (e.g, pat_author)

Retry system, if any of the requests raise ConnectionError, retry somehow?
Have it call a generic _request(type) func, which has the retry logic

Could we make ado_client.session a property? Which just passes on the session, but also does logging?
Maybe we can do some clever stuff with the StateManagedResource which trackes which functions takes how long?
Might help tests, detecting calls, etc

Actual logging...

from enum import Flag

ProjectRepositorySettings settings - MEHHH, Project creation sucks
PullRequest.delete_by_id is untested.
PullRequest.add_reviewer
PullRequest.get_reviewers
PullRequest.get_my_pull_requests
PullRequest.set_my_pull_requests_included_teams?

Project -> get_build_queue_settings, get_retention_policy_settings

PullRequest -> Variable Groups

Add more changelog messages for the older versions

Tests for build timelines
Test utils

add .link for most resources, somehow dynamically? Maybe init=False attribute?

Work more on maintain

-----  

Commands:  

python3.11 -m ado_wrapper --delete-everything --creds_file "credentials.txt"  
python3.11 -m ado_wrapper --delete-everything --creds_file "credentials.txt" --state-file "tests/test_state.state"  

coverage run -m pytest tests/
coverage html && open htmlcov/index.html  

coverage run -m pytest && coverage html && open htmlcov/index.html  

python3.11 -m pip install ado_wrapper --upgrade  

python3.11 -m pytest tests/ -vvvv -s  
black . --line-length 140  

mypy . --strict && flake8 --ignore=E501,E126,E121,W503,W504,PBP --exclude=script.py && ruff check && pylint .
bandit -c pyproject.toml -r .  

[ADO_WRAPPER] Deleted Environment 134 from ADO
[ADO_WRAPPER] Deleted PullRequest 212 from ADO
[ADO_WRAPPER] Deleted PullRequest 213 from ADO
[ADO_WRAPPER] Deleted PullRequest 214 from ADO
[ADO_WRAPPER] Deleted PullRequest 215 from ADO
[ADO_WRAPPER] Deleted PullRequest 216 from ADO
[ADO_WRAPPER] Deleted PullRequest 217 from ADO
[ADO_WRAPPER] Deleted PullRequest 218 from ADO
[ADO_WRAPPER] Deleted PullRequest 219 from ADO
[ADO_WRAPPER] Deleted PullRequest 220 from ADO
[ADO_WRAPPER] Deleted Repo 16db8bc8-4956-4748-b845-d1f41ded2640 from ADO
[ADO_WRAPPER] Deleted Repo 145ad80c-fc37-4836-8a2f-6550225731d0 from ADO
[ADO_WRAPPER] Deleted Repo 973028f8-bdb0-4c2d-8da0-16cde2124b5f from ADO
[ADO_WRAPPER] Deleted Repo 9e8e4d94-3ce4-4b01-91f4-13ec7334525d from ADO
[ADO_WRAPPER] Deleted Repo cc1f32ee-4bea-47d9-a732-bce35c0418fe from ADO
[ADO_WRAPPER] Deleted Repo 91d033d8-4c74-4412-948d-46ee349bb45c from ADO
[ADO_WRAPPER] Deleted Repo 752d3a4f-90ef-4bea-bc02-40aff50a52b7 from ADO
[ADO_WRAPPER] Deleted Repo 135eeaa9-2312-44c1-820c-3125cb06667c from ADO
[ADO_WRAPPER] Deleted Repo 14f462a1-b627-4e65-9aa3-2b16d2fda4ca from ADO
[ADO_WRAPPER] Deleted Repo c3d6b207-d8cd-4636-9243-839f398b71d2 from ADO
[ADO_WRAPPER] Deleted Repo ba1eb99b-e7b6-432a-be9f-2681111545e9 from ADO
[ADO_WRAPPER] Deleted Repo 35102edc-e01f-42cb-b596-736acb20652b from ADO
[ADO_WRAPPER] Deleted Repo 5c051c13-0b6d-4f5b-8345-84b04db4ae8e from ADO
[ADO_WRAPPER] Deleted Repo e3eb07d5-96a7-41f1-866d-dcdec20d5367 from ADO
[ADO_WRAPPER] Deleted Repo c8a19730-5918-4bdf-ac11-ba420a0c176e from ADO
[ADO_WRAPPER] Deleted Repo cc20bb94-6577-447a-842e-58390ef3213c from ADO
[ADO_WRAPPER] Deleted Repo 41609502-108d-490c-8969-852f9dc3c5ee from ADO
[ADO_WRAPPER] Deleted Repo 127d1bd9-0db0-40c0-a79e-81c17fe172f0 from ADO
[ADO_WRAPPER] Deleted Repo c9a99705-2a06-4b62-b5c7-f130f56e5cbf from ADO
[ADO_WRAPPER] Deleted Repo 2b75d893-5824-4373-a756-424ae2662103 from ADO
[ADO_WRAPPER] Deleted Repo b92151de-f5b1-4f7e-9cee-7122a47a1dc6 from ADO
[ADO_WRAPPER] Deleted Repo c920c8a2-4fe2-4ce4-a50a-46d9dd3cbc45 from ADO
[ADO_WRAPPER] Deleted Repo 126b0bc8-b61a-4167-87b7-bcd0b882e103 from ADO
[ADO_WRAPPER] Deleted Repo 8ecaca41-658e-406b-bc87-e3a146b2f220 from ADO
[ADO_WRAPPER] Deleted Repo 21211497-b284-47f7-aa79-19ec8d4f3385 from ADO
[ADO_WRAPPER] Deleted Repo d7dc9bc2-ea13-4005-b41e-b094a92936cb from ADO
[ADO_WRAPPER] Deleted Repo 20c90e05-97ea-4dac-ae4d-e9dee83f1e27 from ADO
[ADO_WRAPPER] Deleted Repo 5c51606d-4fb4-4233-ae6c-bf494090a61b from ADO
[ADO_WRAPPER] Deleted Repo 95e6b257-0276-4cfd-9c5c-09f33d0c5d47 from ADO
[ADO_WRAPPER] Deleted Repo 5ec58d7f-fa97-41cc-b7ec-7bef271757bd from ADO
[ADO_WRAPPER] Deleted Repo d4175843-3d11-4a0e-af4e-3a8b4c384a65 from ADO
[ADO_WRAPPER] Deleted Repo 0fb1dfa3-ee58-48fd-bc6c-58c98f08a3f8 from ADO
[ADO_WRAPPER] Deleted Repo 94c4116d-8430-45ac-9efe-cbf4158f81b9 from ADO
[ADO_WRAPPER] Deleted Repo 49edb3d7-a59a-4235-8206-b245b28eae92 from ADO
[ADO_WRAPPER] Deleted Repo f3dbbd61-7153-4e55-a98c-4ef2aca4fedb from ADO
[ADO_WRAPPER] Deleted Repo afb13e25-d138-44af-a76e-34b06ddc90fd from ADO
[ADO_WRAPPER] Deleted Repo cdbaa60e-0274-4deb-b57b-6c580c9f65ab from ADO
[ADO_WRAPPER] Deleted Repo 1754a241-12df-4184-bc15-9a857935b019 from ADO
[ADO_WRAPPER] Deleted Repo f1455a7d-1d74-423e-97c3-824fa7bcb0df from ADO
[ADO_WRAPPER] Deleted Repo a74cf8cb-4154-44fd-8aab-52de7250ea09 from ADO
[ADO_WRAPPER] Deleted Repo 8592595b-7bbd-47e2-901a-235a87440ef8 from ADO
[ADO_WRAPPER] Deleted Repo 5a3a951f-25e3-447c-b665-a8989f78ca0e from ADO
[ADO_WRAPPER] Deleted Repo 5271b362-968c-4b33-a9a8-aa17a8de7fda from ADO
[ADO_WRAPPER] Deleted Repo 5a021381-6fe4-4cac-ad77-77d66aa05ffa from ADO
[ADO_WRAPPER] Deleted Repo 9f79544b-12ff-4142-9700-2e91d1cd78bd from ADO
[ADO_WRAPPER] Deleted Repo a707cdd8-a3ae-4023-8abb-af3fc7db4e44 from ADO
[ADO_WRAPPER] Deleted Repo a126206f-e6cc-448e-867d-6ced7f768f56 from ADO
[ADO_WRAPPER] Deleted Repo 370fa51b-ffe6-4b81-be24-9a693ff59292 from ADO
[ADO_WRAPPER] Deleted Repo 03e5eab6-4139-4f78-939b-9256af82ac84 from ADO

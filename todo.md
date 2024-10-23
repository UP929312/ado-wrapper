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

Secure Files next to library groups

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

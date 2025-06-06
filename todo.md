# To do

For VG get contents, raise if not found.

Releases need vigerous testing - kinda wip, ReleaseDef - Update

Maybe add the alternative way? I.E. if it's changed in real resources

We can maybe use run id to delete all by run id? "prevent_destroy", "ignore_changes"
MORE WORK ON LIFECYCLE!

This?
<https://www.reddit.com/r/ado_wrapper/comments/xj56gs/complete_pull_request_with_bypass_policy_via_api/>
Just generally approving infra stages that require approval, if we can even do that.

<https://stackoverflow.com/questions/77522387/approving-pipeline-stage-azure-devops-via-api>
Auto approve via token ^

<https://learn.microsoft.com/en-us/azure/devops/pipelines/process/approvals?view=azure-devops&tabs=check-pass>
<https://stackoverflow.com/a/61519132>
Pipeline perms, currently our pipelines are approval-able by almost anyone, we should be able to set the perms

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

Docs have functions which raise NotImplemented, inspect and remove if they do? AST?

Pat token stuffs
Artifact stuffs - # Is is because I can only create an artifact to an inProgress build?

Somehow detect expired tokens? simple_ado???
simple_ado.exceptions.ADOHTTPException: ADO returned a non-200 status code, configuration=<simple_ado.http_client.ADOHTTPClient object at 0x1025de310>, status_code=401, text=Access Denied: The Personal Access Token used has expired.
UNSURE HOW TO DO ABOVE
But because we can fetch access_tokens, maybe we can instead check if the current one's expired? Somehow?
I CANT REMEMBER HOW I GOT THAT ERROR, SO ANNOYING SINCE IT EXACTLY TELLS ME ITS EXPIRED

When creating yaml, if you don't provide stages, it creates one called "__default"
`ado_wrapper.errors.ConfigurationError: Wrong stage name or job name combination (case sensitive), received Jobs/EchoEnvironmentVariables/Echo Modified Keys and ValuesOptions were __default/EchoEnvironmentVariables/Echo Modified Keys and Values`

For each test file, have a zzz_cleanup() function which empties state?
Maybe each test could inherit from a parent class which has this?

Retry system, if any of the requests raise ConnectionError, retry somehow?
Have it call a generic _request(type) func, which has the retry logic?
We can now made this better, since we have the logging function which overrides the request.

rather than "requires initialisation", maybe make .ado_project_id a property and put it there?
Perhaps have some system relating to intents? Which pre-loads a bunch of stuff (e.g, pat_author)
from enum import Flag

ProjectRepositorySettings settings - MEHHH, Project creation sucks
PullRequest.delete_by_id is untested.
PullRequest.add_reviewer
PullRequest.get_reviewers
PullRequest.get_my_pull_requests
PullRequest.set_my_pull_requests_included_teams?
Never test get_environment_approvals

Project -> get_build_queue_settings, get_retention_policy_settings
PullRequest -> Variable Groups

Tests for build timelines
Test utils

Work more on maintain - No resources are *that* editable tbh.

Rollback a commit? Tricky...
I guess I could fetch the repo by a certain commit, and find the difference for all the files, and then make a commit like that?

Get all runs, figure out which stage takes the longest, basically profile our runs

PullRequest.from_link()??? And other resources? That just fetches.

Artifact creation using pipelines like VariableGroup and SecureFiles? We could also create a temp repo which hosts the files
So we can "download them" onto the agent. What is the point? So we can make a temporary artifact? So we can make a permanent one?

Rework get_all_by_continuation_token to use _get_by_url(fetch_multiple=True)
Problem is, we only return resources, we never capture the headers and return them too, not sure how we can do that...

Teams.get_members(recursive=True)  Not sure that Teams are the right thing, maybe Groups? Idk


Commit.branch?

Work Itme edit, also create with parent?

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

mypy . --strict && flake8 --ignore=E501,E126,E121,W503,W504,PBP,E226 --exclude=script.py && ruff check && pylint .
bandit -c pyproject.toml -r .  

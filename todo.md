# To-do

Releases need vigerous testing - kinda wip, ReleaseDef - Update

A push is when someone has multiple commits and they do a git push (to a branch), it can be multiple sub-commits
<https://learn.microsoft.com/en-us/rest/api/azure/devops/git/pushes/get?view=azure-devops-rest-7.1&tabs=HTTP#gitpush>

Rollback a commit? Tricky...
I guess I could fetch the repo by a certain commit, and find the difference for all the files, and then make a commit like that?

Update the state file on startup, and have an option to disable it - DONE
Maybe add the alternative way? I.E. if it's changed in real resources

Script plan mode?

Teams.get_members(recursive=True)  Not sure that Teams are the right thing, maybe Groups? Idk

We can maybe use run id to delete all by run id? "prevent_destroy", "ignore_changes"
MORE WORK ON LIFECYCLE!

We need to do something differently with creating stuff, currently if you run the same script twice, it'll just error because the
object already exists, so the creator in SMR should check try, and if it fails, update the already existing one?

This?
<https://www.reddit.com/r/ado_wrapper/comments/xj56gs/complete_pull_request_with_bypass_policy_via_api/>

Commits/Branches are the only things that don't have a generic `get_all`

<https://stackoverflow.com/questions/77522387/approving-pipeline-stage-azure-devops-via-api>
Auto approve via token ^

<https://learn.microsoft.com/en-us/azure/devops/pipelines/process/approvals?view=azure-devops&tabs=check-pass>
<https://stackoverflow.com/a/61519132>
Pipeline perms, currently our pipelines are approval-able by almost anyone, we should be able to set the perms

AdoUser - Get all, doesn't work with pagination

Maybe rather than RepoContextManager, we have it work for all resources? Maybe takes any StateManaged Resource and deletes it after?
Make all resources be able to be context managers?
This would work great (I think), but the objects need to store the ado_client, because exiting requires it...

Hmmmmm, it appears that when creating a variable group, it doesn't return the created by or modified by with enough data.
This is different from the get_by_id, because the get_by_id gets the creator, but the creation return doesn't...

The problem we have with the whole "create twice" instead of update can be fixed.
The state stores the repo id, but it also stores the repo *name*, which is coincidentally also unique.
Most resources have names, or some definining values which has to be unique, e.g. name (in repos, variable groups, etc).
Tags are a problem, branches a bit too, build definitions too, the problem is that we want to be able to change things and
have the create update, rather than create, but if the data is different, how do we link them?  

More tests around:
Service connections perms on pipelines (done, not tested)
TestStateManager needs some work
build_defs/allow_on_environment Needs testing
Runs
Run's Get Stage Results
AgentPools create/delete and testing  
AuditLogs Tests - Only have perms in UK, dang  
Test state_manager.py more?  
Test __main__.py  
Test to test if template_parameters is being set when fetching/creating runs

Add all the required perms with @required_perms

<https://github.com/microsoft/azure-devops-python-api/blob/dev/azure-devops/azure/devops/v7_0/build/build_client.py#L1248>

Can Jobs have logs, not just the steps?

-----  

Commands:  
pylint .  
mypy . --strict  
flake8 --ignore=E501,E126,E121,W503,W504,PBP --exclude=script.py  
ruff check  
black . --line-length 140  
python3.11 -m pytest tests/ -vvvv -s  

python3.11 -m ado_wrapper --delete-everything --creds_file "credentials.txt"  
python3.11 -m ado_wrapper --delete-everything --creds_file "credentials.txt" --state-file "tests/test_state.state"  
python3.11 -m ado_wrapper --refresh-resources-on-startup --creds_file "credentials.txt"  
coverage run -m pytest  
coverage html && open htmlcov/index.html  

coverage run -m pytest && coverage html && open htmlcov/index.html  

python3.11 -m pip install ado_wrapper --upgrade  

pylint . && mypy . --strict && flake8 --ignore=E501,E126,E121,W503,W504,PBP --exclude=script.py && ruff check  

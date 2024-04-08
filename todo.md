# To-do

Resources that are entirely state managed:
Build -*
BuildDefinition -*
ReleaseDefinition
Release
Repo -*
ServiceEndpoints
VariableGroup -*

Soon:
Pull Request, Commit, ServiceEndpoints

-* = Supports edits/updates too

Add "Update" to more stuff

-----

When I am testing .from_request_payload, maybe use the plan object's data?

Also, Releases need vigerous testing - kinda wip, ReleaseDef - Update

TODO: Look into Pushes vs Commits <https://learn.microsoft.com/en-us/rest/api/azure/devops/git/pushes/get?view=azure-devops-rest-7.1&tabs=HTTP#gitpush>

Rollback a commit? Tricky...

Update the state file on startup, and have an option to disable it - DONE
Maybe add the alternative way? I.E. if it's changed in real resources

Script plan mode?

Teams.get_members(recursive=True)  Not sure that Teams are the right thing, maybe Groups? Idk

Member's from_request should be improved to be displayName, uniqueName, id

<https://docs.python.org/3/library/dataclasses.html#dataclasses.asdict>
This might allow us to remove "as_json"

For state, have metadata, and lifecycle policies, split each id into id -> {data, lifecyclepolicy, metadata: {created_timestamp, run_id}}
We can maybe use run id to delete all by run id? "prevent_destroy", "ignore_changes"

We need to do something differently with creating stuff, currently if you run the same script twice, it'll just error because the
object already exists, so the creator in SMR should check try, and if it fails, update the already existing one?

Look into tags for resources?
<https://learn.microsoft.com/en-us/rest/api/azure/devops/git/annotated-tags/get?view=azure-devops-rest-7.1&tabs=HTTP>

This?
<https://www.reddit.com/r/ado_wrapper/comments/xj56gs/complete_pull_request_with_bypass_policy_via_api/>

Re-run on "connection error"

Dataclass "init=False" part of a field, but this won't work for type hinting I guess, also, while things like
normally take 1 input (id), things like create can take more complicated stuff

State manager has get_by_id, but it's really get by url path? Look into this?

Service connections perms on pipelines

-----

Pylint command:
pylint *
mypy . --strict
black . --line-length 140
pytest tests/ -vvvv -s
python3.11 -m ado_wrapper --delete-everything --creds_file "credentials.txt"
python3.11 -m ado_wrapper --delete-everything --creds_file "credentials.txt" --state-file "tests/test_state.state"
python3.11 -m ado_wrapper --refresh-resources-on-startup --creds_file "credentials.txt"
coverage run -m pytest

python3.11 -m pip install ado_wrapper --upgrade

-----

For the plans, have a new folder, called "plan_resources", which has all the same resources, but a few differences:

1. Each object will hold a dictionary of key=tuple, with first item, request type, second item, regex pattern (for the url) to match against. The value of each key, value pair will be a fake requets object with it's json set to a dump of what it normally returns, with ids containing a new singleton.
2. When we want planned things, we should decorate functions, which when run, will take over requests.get or whatever to use our custom classes.
3. On startup, the plan will refresh all state, and if it tried to fetch stuff that's not in state, it'll also try in the real world
4. The ado_client should have a "is_planning" bool, which will dictate stuff.
5. When we are in planning mode, we should have an in memory state, which will start as a duplicate of the updated local state
6. This local state will get updated when we create or destroy things

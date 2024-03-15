# To-do

The whole state idea, for each class that creates stuff, add it to the state file
Have a CLI to clear state, maybe of certain resources
When you delete from ado, it should also delete from state
Maybe show a type when adding to state too, like "Add": abc
This lets us store and perhaps revert updates?

Resources that are entirely state managed:
BuildDefinition
Repo
VariableGroup

Soon:
Build, ReleaseDefinition, Release, Pull Request, Commit

-----

Also, Releases need vigerous testing

Perhaps when creating stuff, use a "while True" loop with user input, if they input "y", go to the next step?

Rollback a commit? Tricky...

Update the state file on startup, and have an option to disable it - DONE
Maybe add the alternative way? I.E. if it's changed in real resources, have "update" as part of the StateManged Standard?

Script plan mode?

Teams.get_members(recursive=True)

Pull requests aren't working, rip

Build.wait_until_completed(build_id)

Variable groups are broken in the dictionary/variables section

Add reviewers straight with {
  "sourceRefName": "refs/heads/npaulk/my_work",
  "targetRefName": "refs/heads/new_feature",
  "title": "A new feature",
  "description": "Adding a new feature",
  "reviewers": [
    {
      "id": "d6245f20-2af8-44f4-9451-8107cb2767db"
    }
  ]
}
To PRs

-----

Pylint command:
pylint *.py
mypy . --strict
black . --line-length 140
pytest tests/ -vvvv -s
python3.11 -m client --delete-everything

pytest tests/ -vvvv -s -m wip

# Todo

The whole state idea, for each class that creates stuff, add it to the state file
Have a CLI to clear state, maybe of certain resources
When you delete from ado, it should also delete from state
Maybe show a type when adding to state too, like "Add": abc
This lets us store and perhaps revert updates?

Also, Releases need vigerous testing

Perhaps when creating stuff, use a "while True" loop with user input, if they input "y", go to the next step?

Rollback a commit?

Test -> BuildDefinition.get_all_by_repo_id

Update the state file on startup, and have an option to disable it - DONE
Maybe add the alternative way? I.e. if it's changed in real resources, have "update" as part of the StateManged Standard?

Script plan mode?

Teams.get_members(recursive=True)

WHEN TESTING, make our own repos and stuff, we shouldn't use the existing ones, just make a repo, then delete after

Build.wait_until_completed(build_id)

Pylint command:
pylint *.py --disable=C0301,C0103,R0801,E0602,C0114,C0116,C0115,W3101,W0621,R0913,W0511,R0902,R1710,C0415,W0237,R0401
mypy . --strict
black . --line-length 140
pytest tests/ -vvvv -s
python3.11 -m client --delete-everything

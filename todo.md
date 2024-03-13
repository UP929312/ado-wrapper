# Todo

The whole state idea, for each class that creates stuff, add it to the state file
Have a CLI to clear state, maybe of certain resources
When you delete from ado, it should also delete from state
Maybe show a type when adding to state too, like "Add": abc
This lets us store and perhaps revert updates?

Also, Builds and Releases need vigerous testing

Perhaps when creating stuff, use a "while True" loop with user input, if they input "y", go to the next step?

Pylint command:
pylint *.py --disable=C0301,C0103,R0801,E0602,C0114,C0116,C0115,W3101,W0621,R0913,W0511,R0902,R1710,C0415,W0237
mypy . --strict
black . --line-length 140
pytest tests/
python3.11 -m client --delete-everything

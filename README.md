# Ado Wrapper

This is a Python Package which works as an interface to the Azure DevOps API

It is essentially a wrapper for the (horrible to work with) ADO API, and supports OOP principals.

Any resource can be fetched by calling the `<resource>.get_by_id()` function.

It also includes a solution for managing resources created by this script, which is extremely useful for testing the creation of random resources.
To delete all resources created by this, run the main module with the "--delete-everything" flag.

If you're reading this readme not from the code, here's a link to the [github repo](https://github.com/UP929312/ado-wrapper)


# Setup

To test/add to this locally, you'll need to create a few files:
For tests, add tests/test_data.txt, which contains:
ADO Organisation name
ADO Project name (e.g. MyProject)
ADO Secondary project name (e.g. can be empty for your testing, so just an empty line unless you're testing the client)
Email: e.g. first.last@company.com
Pat token (with good perms), https://dev.azure.com/<ORG>/_usersSettings/tokens
Existing User ID, print(AdoUser.get_by_email(ado_client, "first.last@company.com").origin_id)
Existing user descriptor, print(AdoUser.get_by_email(ado_client, "first.last@company.com").descriptor_id)


## Commands Used To Ensure Quality

pylint .  
mypy . --strict  
flake8 --ignore=E501,E126,E121,W503,W504,PBP --exclude=script.py  
bandit -c pyproject.toml -r .  
ruff check  
black . --line-length 140  
python3.11 -m pytest tests/ -vvvv -s  

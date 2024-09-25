# Ado Wrapper

This is a Python Package which works as an interface to the Azure DevOps API

It is essentially a wrapper for the (horrible to work with) ADO API, and supports OOP principals.

Any resource can be fetched by calling the `<resource>.get_by_id()` function.

It also includes a solution for managing resources created by this script, which is extremely useful for testing the creation of random resources.
To delete all resources created by this, run the main module with the "--delete-everything" flag.

If you're reading this readme not from the code, here's a link to the [github repo](https://github.com/UP929312/ado-wrapper)

## Commands Used To Ensure Quality

pylint .  
mypy . --strict  
flake8 --ignore=E501,E126,E121,W503,W504,PBP --exclude=script.py  
bandit -c pyproject.toml -r .  
ruff check  
black . --line-length 140  
python3.11 -m pytest tests/ -vvvv -s  

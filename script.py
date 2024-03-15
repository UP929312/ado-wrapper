from secret import email, ado_access_token, ado_org, ado_project  # , EXISTING_REPO_NAME
# from secret import email, alterative_ado_access_token, old_ado_org, old_ado_project
from client import AdoClient

# from resources.projects import Project
# from resources.repo import Repo

ado_client = AdoClient(email, ado_access_token, ado_org, ado_project)

# projects = Project.get_all(ado_client)
# print(projects)

# ado_client = AdoClient(email, alterative_ado_access_token, old_ado_org, old_ado_project)

# from repository import Repo
# Repo.create(ado_client, "ado-api-test-repo")

# repo = Repo.get_by_name(ado_client, "").repo_id

# from teams import Team

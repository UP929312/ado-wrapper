from secret import email, ado_access_token, ado_org, ado_project  # , EXISTING_REPO_NAME

# from secret import email, alterative_ado_access_token, old_ado_org, old_ado_project
from client import AdoClient

ado_client = AdoClient(email, ado_access_token, ado_org, ado_project)

# ado_client = AdoClient(email, alterative_ado_access_token, old_ado_org, old_ado_project)

# from repository import Repo
# Repo.create(ado_client, "ado-api-test-repo")

# repo = Repo.get_by_name(ado_client, "").repo_id
# print(repo)

# from teams import Team
# print(Team.get_by_name(ado_client, ""))

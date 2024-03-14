from secret import email, ado_access_token, ado_org, ado_project  # , EXISTING_REPO_NAME
# from secret import email, alterative_ado_access_token, old_ado_org, old_ado_project
from client import AdoClient

ado_client = AdoClient(email, ado_access_token, ado_org, ado_project)
# ado_client = AdoClient(email, alterative_ado_access_token, old_ado_org, old_ado_project)

from teams import Team
print(Team.get_by_name(ado_client, "Platform Team"))
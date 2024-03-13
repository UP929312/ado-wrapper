# client = AdoClient(email, ado_access_token, ado_org, ado_project)

# for repo in Repo.get_all(client):
#     print(repo)
#     for pr in repo.get_all_pull_requests(client, status="completed"):
#         if email in [x.email for x in pr.reviewers]:
#             print("   PR:", pr)
#             print("     Reviewers:", pr.get_reviewers(client))

from secret import email, ado_access_token, ado_org, ado_project  #, EXISTING_REPO_NAME
from client import AdoClient
ado_client = AdoClient(email, ado_access_token, ado_org, ado_project)

# from repository import Repo
# from commits import Commit
# from user import AdoUser
from teams import Team

team = Team.get_by_name(ado_client, "Common Components")
members = team.get_members(ado_client)
print(members)

# repo = Commit.get_all_by_repo(ado_client, EXISTING_REPO_NAME)
# print(repo)
# member = Member.get_by_email(ado_client, "ben.skerritt@vodafone.com")
# member = Member.get_by_id(ado_client, "4b800588-6f40-4382-95f4-a45c3411db22")
# member = AdoUser.get_by_id(ado_client, "aad.MDk2MTUyNTMtZWE1Mi03MzdmLWI4ZTQtNjNjYWI2NzRlYWM3")

# print(f"{member!r}")

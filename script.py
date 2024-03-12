from secret import email, ado_access_token, ado_org, ado_project
from main import AdoClient
from repository import Repo

client = AdoClient(email, ado_access_token, ado_org, ado_project)

for repo in Repo.get_all_repos(client):
    print(repo)
    for pr in repo.get_all_pull_requests(client, status="completed"):
        if email in [x.email for x in pr.reviewers]:
            print("   PR:", pr)
            print("     Reviewers:", pr.get_reviewers(client))

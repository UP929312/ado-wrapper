# pylint: disable-all

from datetime import datetime, timedelta
import re
import requests
import json

with open("credentials.txt", "r") as file:
    email, ado_access_token, ado_org, ado_project = file.read().split("\n")

from ado_wrapper import AdoClient, Project, VariableGroup, AdoUser, Member, Reviewer, Repo, Commit, PullRequest, Build, BuildDefinition, Branch, Release, ReleaseDefinition, Team, ServiceEndpoint

ado_client = AdoClient(email, ado_access_token, ado_org, ado_project)
ado_client.state_manager.load_all_resources_with_prefix_into_state("ado_wrapper-")

service_endpoint = ServiceEndpoint.get_by_id(ado_client, "41f5080f-a957-4d5b-8faa-061dba4e9ad6")
print(service_endpoint)

# for pr in PullRequest.get_all(ado_client, status="active"):
#     if datetime.now() - pr.creation_date > timedelta(days=185):
#         rint(pr)

# pr = PullRequest.get_by_id(ado_client, "11360")
# rint("\n".join([str(x) for x in pr.get_comment_threads(ado_client, ignore_system_messages=True)]))

# rint([x.name for x in Repo.get_all(ado_client)])

#  https://dev.azure.com/{ado_client.ado_org}/{id}/_apis/pipelines/pipelinePermissions/variablegroup/703
# PATCH
# a = {"pipelines": [{"id": 1, "authorized": True}]}
# recursive_teams = Team.get_all_teams_recursively(ado_client)
# for team in recursive_teams:
#     rint(f"{team!r}")

# rint(PullRequest.get_my_pull_requests(ado_client))

# pylint: disable-all

from datetime import datetime, timedelta
import re
import requests
import json

with open("credentials.txt", "r") as file:
    email, ado_access_token, ado_org, ado_project = file.read().split("\n")

from ado_wrapper import AdoClient
from ado_wrapper.resources import *

ado_client = AdoClient(email, ado_access_token, ado_org, ado_project, bypass_initialisation=True, action="plan")
# ado_client.state_manager.load_all_resources_with_prefix_into_state("ado_wrapper-")
# repo = Repo.create(ado_client, "ado_wrapper-plan-test", include_readme=False)

# from ado_wrapper.resources.repo import RepoPolicies

# a = RepoPolicies.get_by_id(ado_client, "1aa43e9c-ffca-4388-98b5-59b272a497b8")
# print(a)

# print(ado_client.state_manager.state)
# ado_client.state_manager.output_changes()  # type: ignore[attr-defined]

# for pr in PullRequest.get_all(ado_client, status="active"):
#     if datetime.now() - pr.creation_date > timedelta(days=185):
#         rint(pr)

# pr = PullRequest.get_by_id(ado_client, "11360")
# rint("\n".join([str(x) for x in pr.get_comment_threads(ado_client, ignore_system_messages=True)]))

# rint([x.name for x in Repo.get_all(ado_client)])

#  https://dev.azure.com/{ado_client.ado_org}/{id}/_apis/pipelines/pipelinePermissions/variablegroup/703
# PATCH
# a = {"pipelines": [{"id": 1, "authorized": True}]}
# rint(PullRequest.get_my_pull_requests(ado_client))

# pylint: disable-all

# from datetime import datetime, timedelta
# import requests

with open("credentials.txt", "r") as file:
    email, ado_access_token, ado_org, ado_project = file.read().split("\n")

from ado_wrapper import AdoClient
from ado_wrapper.resources import *

ado_client = AdoClient(email, ado_access_token, ado_org, ado_project, bypass_initialisation=False)  #, action="plan")

# environment = Environment.get_by_id(ado_client, "170")
# 1797, 1800

# ado_client.state_manager.load_all_resources_with_prefix_into_state("ado_wrapper-")
# repo = Repo.create(ado_client, "ado_wrapper-plan-test", include_readme=False)

# repo = Repo.create(ado_client, "perms-test-repo", include_readme=True)
# repo = Repo.get_by_name(ado_client, "")
# repo = Repo.get_by_name(ado_client, "perms-test-repo")
# assert repo is not None
# repo_branch_policies = MergePolicies.get_all_by_repo_id(ado_client, repo.repo_id)
# rint(repo_branch_policies)
# assert repo_branch_policies is not None
# rint("\n".join([repr(x) for x in repo_branch_policies]))

# rint(ado_client.state_manager.state)
# ado_client.state_manager.output_changes()  # type: ignore[attr-defined]

# for pr in PullRequest.get_all(ado_client, status="active"):
#     if datetime.now() - pr.creation_date > timedelta(days=365):
#         rint(pr)

#  https://dev.azure.com/{ado_client.ado_org}/{id}/_apis/pipelines/pipelinePermissions/variablegroup/703
# PATCH
# a = {"pipelines": [{"id": 1, "authorized": True}]}
# rint(PullRequest.get_my_pull_requests(ado_client))

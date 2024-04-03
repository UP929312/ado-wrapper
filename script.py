# pylint: disable-all

from datetime import datetime
import re
import requests
import json

from secret import email, ado_access_token, ado_org, ado_project

# from secret import email, alternative_ado_access_token, old_ado_org, old_ado_project

from client import AdoClient

from resources.projects import Project
from resources.variable_groups import VariableGroup
from resources.users import AdoUser, Member, Reviewer
from resources.repo import Repo
from resources.commits import Commit
from resources.pull_requests import PullRequest
from resources.builds import Build, BuildDefinition
from resources.branches import Branch
from resources.releases import Release, ReleaseDefinition
from resources.teams import Team
from resources.groups import Group

# ado_client = AdoClient(email, alternative_ado_access_token, old_ado_org, old_ado_project)
ado_client = AdoClient(email, ado_access_token, ado_org, ado_project)
# ado_client.state_manager.load_all_resources_with_prefix_into_state("ado-api-")

#  https://dev.azure.com/{ado_client.ado_org}/{id}/_apis/pipelines/pipelinePermissions/variablegroup/703
# PATCH
# a = {"pipelines": [{"id": 1, "authorized": True}]}
# recursive_teams = Team.get_all_teams_recursively(ado_client)
# for team in recursive_teams:
#     rint(f"{team!r}")

# rint(PullRequest.get_my_pull_requests(ado_client))

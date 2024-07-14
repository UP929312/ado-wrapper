from typing import Any

from ado_wrapper.client import AdoClient
from ado_wrapper.resources.repo import Repo

with open("tests/test_data.txt", encoding="utf-8") as test_data:
    (
        ado_org_name, ado_project, email, pat_token, existing_team_name, existing_team_id, existing_user_name,
        existing_user_email, existing_user_id, existing_user_descriptor, existing_agent_pool_id,
        existing_project_name, existing_project_id, existing_group_descriptor,
        test_search_string
    ) = test_data.read().splitlines()  # fmt: skip

ado_client = AdoClient(email, pat_token, ado_org_name, ado_project, "tests/test_state.state")


def setup_client() -> AdoClient:
    return ado_client


class RepoContextManager:
    """A context manager which creates and (always) deletes a repo within tests"""

    def __init__(self, ado_client: AdoClient, repo_name: str):
        self.ado_client = ado_client
        self.repo_name = "ado_wrapper-test-repo-for-" + repo_name

    def __enter__(self) -> Repo:
        self.repo = Repo.create(ado_client, self.repo_name, include_readme=True)
        return self.repo

    def __exit__(self, *_: Any) -> None:
        self.repo.delete(self.ado_client)

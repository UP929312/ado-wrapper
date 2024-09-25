from typing import Any

from ado_wrapper.client import AdoClient
from ado_wrapper.resources.repo import Repo

with open("tests/test_data.txt", encoding="utf-8") as test_data:
    ado_org_name, ado_project, email, pat_token, existing_user_id, existing_user_descriptor = test_data.read().splitlines()  # fmt: skip
existing_user_name = email.split("@")[0].replace(".", " ").title().split(".")[0]

ado_client = AdoClient(email, pat_token, ado_org_name, ado_project, "tests/test_state.state")


def setup_client() -> AdoClient:
    return ado_client


class RepoContextManager:
    """A context manager which creates and (always) deletes a repo within tests"""

    def __init__(self, ado_client: AdoClient, repo_name: str, delete_on_exit: bool = True):
        self.ado_client = ado_client
        self.repo_name = "ado_wrapper-test-repo-for-" + repo_name
        self.delete_on_exit = delete_on_exit

    def __enter__(self) -> Repo:
        self.repo = Repo.create(ado_client, self.repo_name, include_readme=True)
        return self.repo

    def __exit__(self, *_: Any) -> None:
        if self.delete_on_exit:
            self.repo.delete(self.ado_client)


class ElevatedPrivileges:
    """A context manager which raises the privileges of the client (to do dangerous things like delete projects)"""

    def __init__(self, ado_client: AdoClient):
        self.ado_client = ado_client

    def __enter__(self) -> None:
        self.ado_client.elevated_privileges = True

    def __exit__(self, *_: Any) -> None:
        self.ado_client.elevated_privileges = False

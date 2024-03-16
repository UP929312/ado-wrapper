from __future__ import annotations

import io
import zipfile
from dataclasses import dataclass, field

import requests

from client import AdoClient
from state_managed_abc import StateManagedResource
from utils import ResourceNotFound, UnknownError
from resources.pull_requests import PullRequest, PullRequestStatus
from resources.commits import Commit

# ====================================================================
# {"changeType": 1, "item": {"path": "/README.md"}, "newContentTemplate": {"name": "README.md", "type": "readme"}}
# {"changeType": 1, "item": {"path": "/.gitignore"}, "newContentTemplate": {"name": "Python.gitignore", "type": "gitignore"}}


@dataclass
class Repo(StateManagedResource):
    """https://learn.microsoft.com/en-us/rest/api/azure/devops/git/repositories?view=azure-devops-rest-7.1"""

    repo_id: str = field(metadata={"is_id_field": True})
    name: str
    default_branch: str = field(default="refs/heads/main", repr=False, metadata={"editable": True, "internal_name": "defaultBranch"})
    is_disabled: bool = field(default=False, repr=False, metadata={"editable": True, "internal_name": "isDisabled"})

    def __str__(self) -> str:
        return f"Repo(name={self.name}, id={self.repo_id})"

    @classmethod
    def from_request_payload(cls, data: dict[str, str]) -> "Repo":
        return cls(data["id"], data["name"], data.get("defaultBranch", "refs/heads/main"), bool(data.get("isDisabled", False)))

    @classmethod
    def get_by_id(cls, ado_client: AdoClient, repo_id: str) -> "Repo":
        return super().get_by_id(
            ado_client,
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/git/repositories/{repo_id}?api-version=7.1",
        )  # type: ignore[return-value]

    @classmethod
    def create(cls, ado_client: AdoClient, name: str, include_readme: bool = True) -> "Repo":  # type: ignore[override]
        repo = super().create(
            ado_client,
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/git/repositories?api-version=7.1-preview",
            {"name": name},
        )
        if include_readme:
            Commit.add_initial_readme(ado_client, repo.repo_id)  # type: ignore[attr-defined]
        return repo  # type: ignore[return-value]

    @classmethod
    def delete_by_id(cls, ado_client: AdoClient, repo_id: str) -> None:  # type: ignore[override]
        return super().delete_by_id(
            ado_client,
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/git/repositories/{repo_id}?api-version=7.1",
            repo_id,
        )

    # ============ End of requirement set by all state managed resources ================== #
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # =============== Start of additional methods included with class ===================== #

    @classmethod
    def get_all(cls, ado_client: AdoClient) -> list["Repo"]:
        request = requests.get(
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/git/repositories?api-version=7.1",
            auth=ado_client.auth,
        ).json()
        return [cls.from_request_payload(repo) for repo in request["value"]]

    @classmethod
    def get_by_name(cls, ado_client: AdoClient, repo_name: str) -> "Repo":
        """Warning, this function must fetch `all` repos to work, be cautious when calling it in a loop."""
        request = requests.get(
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/git/repositories?api-version=7.1",
            auth=ado_client.auth,
        ).json()
        for repo in request["value"]:
            if repo["name"] == repo_name:
                return cls.from_request_payload(repo)
        raise ValueError(f"Repo {repo_name} not found")

    def get_file(self, ado_client: AdoClient, file_path: str, branch_name: str = "main") -> str:
        request = requests.get(
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/git/repositories/{self.repo_id}/items?path={file_path}&versionType={'Branch'}&version={branch_name}&api-version=7.1",
            auth=ado_client.auth,
        )
        if request.status_code == 404:
            raise ResourceNotFound(f"File {file_path} not found in repo {self.repo_id}")
        if request.status_code != 200:
            raise UnknownError(f"Error getting file {file_path} from repo {self.repo_id}: {request.text}")
        return request.text  # This is the file content

    def get_repo_contents(self, ado_client: AdoClient, file_types: list[str] | None = None, branch_name: str = "main") -> dict[str, str]:
        """https://learn.microsoft.com/en-us/rest/api/azure/devops/git/items/get?view=azure-devops-rest-7.1&tabs=HTTP"""
        """This function downloads the contents of a repo, and returns a dictionary of the files and their contents
        The file_types parameter is a list of file types to filter for, e.g. ["json", "yaml"]"""
        try:
            request = requests.get(
                f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/git/repositories/{self.repo_id}/items?recursionLevel={'Full'}&download={True}&$format={'Zip'}&versionDescriptor.version={branch_name}&api-version=7.1",
                auth=ado_client.auth,
            )
        except requests.exceptions.ConnectionError:
            print(f"=== Connection error, failed to download {self.repo_id}")
        # ============ We do this because ADO ===================
        bytes_io = io.BytesIO()
        for chunk in request.iter_content(chunk_size=128):
            bytes_io.write(chunk)

        files = {}
        try:
            with zipfile.ZipFile(bytes_io) as zip_ref:
                # For each file, read the bytes and convert to string
                for file_name in [x for x in zip_ref.namelist() if file_types is None or x.split(".")[-1] in file_types]:
                    files[file_name] = zip_ref.read(file_name).decode()  # fmt: skip
        except zipfile.BadZipFile as e:
            print(f"{self.repo_id} couldn't be unzipped:", e)

        bytes_io.close()
        # =========== That's all I have to say ==================
        return files

    def create_pull_request(self, ado_client: AdoClient, branch_name: str, pull_request_title: str, pull_request_description: str) -> "PullRequest":  # fmt: skip
        """Helper function which redirects to the PullRequest class to make a PR"""
        return PullRequest.create(ado_client, self.repo_id, branch_name, pull_request_title, pull_request_description)

    def get_all_pull_requests(self, ado_client: AdoClient, status: PullRequestStatus) -> list["PullRequest"]:
        pull_requests = requests.get(
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/git/repositories/{self.repo_id}/pullrequests?searchCriteria.status={status}&api-version=7.1",
            auth=ado_client.auth,
        ).json()
        try:
            return [PullRequest.from_request_payload(pr) for pr in pull_requests["value"]]
        except KeyError:
            if pull_requests.get("message", "").startswith("TF401019"):
                print(f"Repo {pull_requests['message'].split('identifier')[1].split(' ')[0]} was disabled, or you had no access.")
            else:
                raise ResourceNotFound(pull_requests)  # pylint: disable=raise-missing-from
            return []

    def delete(self, ado_client: AdoClient) -> None:
        self.delete_by_id(ado_client, self.repo_id)


# ====================================================================


@dataclass
class BuildRepository:
    build_repository_id: str = field(metadata={"is_id_field": True})
    name: str | None = field(default=None)
    type: str = field(default="TfsGit")
    clean: bool | None = field(default=None)
    checkout_submodules: bool = field(default=False, metadata={"internal_name": "checkoutSubmodules"})

    @classmethod
    def from_request_payload(cls, data: dict[str, str | bool]) -> "BuildRepository":
        return cls(data["id"], data.get("name"), data.get("type", "TfsGit"), data.get("clean"), data.get("checkoutSubmodules", False))  # type: ignore[arg-type]

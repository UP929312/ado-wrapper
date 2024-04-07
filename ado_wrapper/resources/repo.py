from __future__ import annotations

import io
import zipfile
from dataclasses import dataclass, field
from typing import Any, Literal

import requests

from ado_wrapper.client import AdoClient
from ado_wrapper.state_managed_abc import StateManagedResource
from ado_wrapper.resources.pull_requests import PullRequest, PullRequestStatus
from ado_wrapper.resources.commits import Commit
from ado_wrapper.utils import ResourceNotFound, UnknownError

# from plan_resources.singletons import plannable_resource
RepoEditableAttribute = Literal["name", "default_branch", "is_disabled"]

# ====================================================================


@dataclass
class Repo(StateManagedResource):
    """https://learn.microsoft.com/en-us/rest/api/azure/devops/git/repositories?view=azure-devops-rest-7.1"""

    repo_id: str = field(metadata={"is_id_field": True})
    name: str = field(metadata={"editable": True})
    default_branch: str = field(default="main", repr=False, metadata={"editable": True, "internal_name": "defaultBranch"})
    is_disabled: bool = field(default=False, repr=False, metadata={"editable": True, "internal_name": "isDisabled"})
    # WARNING, disabling a repo means it's not able to be deleted, proceed with caution.

    def __str__(self) -> str:
        return f"Repo(name={self.name}, id={self.repo_id})"

    @classmethod
    def from_request_payload(cls, data: dict[str, str]) -> "Repo":
        return cls(
            data["id"], data["name"], data.get("defaultBranch", "main").removeprefix("refs/heads/"), bool(data.get("isDisabled", False))
        )

    @classmethod
    def get_by_id(cls, ado_client: AdoClient, repo_id: str) -> "Repo":
        return super().get_by_id(
            ado_client,
            f"/{ado_client.ado_project}/_apis/git/repositories/{repo_id}?api-version=7.1",
        )  # type: ignore[return-value]

    @classmethod
    # @plannable_resource
    def create(cls, ado_client: AdoClient, name: str, include_readme: bool = True) -> "Repo":  # type: ignore[override]
        repo: Repo = super().create(
            ado_client,
            f"/{ado_client.ado_project}/_apis/git/repositories?api-version=7.1",
            {"name": name},
        )  # type: ignore[assignment]
        if include_readme:
            Commit.add_initial_readme(ado_client, repo.repo_id)
        return repo

    def update(self, ado_client: AdoClient, attribute_name: RepoEditableAttribute, attribute_value: Any) -> None:  # type: ignore[override]
        return super().update(
            ado_client, "patch",
            f"/{ado_client.ado_project}/_apis/git/repositories/{self.repo_id}?api-version=7.1",
            attribute_name, attribute_value, {},  # fmt: skip
        )

    @classmethod
    def delete_by_id(cls, ado_client: AdoClient, repo_id: str) -> None:  # type: ignore[override]
        for pull_request in Repo.get_all_pull_requests(ado_client, repo_id, "all"):
            ado_client.state_manager.remove_resource_from_state("PullRequest", pull_request.pull_request_id)
        return super().delete_by_id(
            ado_client,
            f"/{ado_client.ado_project}/_apis/git/repositories/{repo_id}?api-version=7.1",
            repo_id,
        )

    @classmethod
    def get_all(cls, ado_client: AdoClient) -> list["Repo"]:  # type: ignore[override]
        return super().get_all(
            ado_client,
            f"/{ado_client.ado_project}/_apis/git/repositories?api-version=7.1",
        )  # type: ignore[return-value]

    # ============ End of requirement set by all state managed resources ================== #
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # =============== Start of additional methods included with class ===================== #

    @classmethod
    def get_by_name(cls, ado_client: AdoClient, repo_name: str) -> "Repo":
        """Warning, this function must fetch `all` repos to work, be cautious when calling it in a loop."""
        for repo in cls.get_all(ado_client):
            if repo.name == repo_name:
                return repo
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

    def get_contents(self, ado_client: AdoClient, file_types: list[str] | None = None, branch_name: str = "main") -> dict[str, str]:
        """https://learn.microsoft.com/en-us/rest/api/azure/devops/git/items/get?view=azure-devops-rest-7.1&tabs=HTTP
        This function downloads the contents of a repo, and returns a dictionary of the files and their contents
        The file_types parameter is a list of file types to filter for, e.g. ["json", "yaml"]"""
        try:
            request = requests.get(
                f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/git/repositories/{self.repo_id}/items?recursionLevel={'Full'}&download={True}&$format={'Zip'}&versionDescriptor.version={branch_name}&api-version=7.1",
                auth=ado_client.auth,
            )
        except requests.exceptions.ConnectionError:
            print(f"=== Connection error, failed to download {self.repo_id}")
            return {}
        if request.status_code != 200:
            print(f"Error getting repo contents for {self.name} ({self.repo_id}):", request.text)
            return {}
        # ============ We do this because ADO ===================
        bytes_io = io.BytesIO()
        for chunk in request.iter_content(chunk_size=128):
            bytes_io.write(chunk)

        files = {}
        try:
            with zipfile.ZipFile(bytes_io) as zip_ref:
                # For each file, read the bytes and convert to string
                for file_name in [x for x in zip_ref.namelist() if file_types is None or x.split(".")[-1] in file_types]:
                    try:
                        files[file_name] = zip_ref.read(file_name).decode()  # fmt: skip
                    except UnicodeDecodeError:
                        print(f"Error decoding file: {file_name} in {self.name}")
        except zipfile.BadZipFile as e:
            print(f"{self.name} ({self.repo_id}) couldn't be unzipped:", e)

        bytes_io.close()
        # =========== That's all I have to say ==================
        return files

    def create_pull_request(self, ado_client: AdoClient, branch_name: str, pull_request_title: str, pull_request_description: str) -> "PullRequest":  # fmt: skip
        """Helper function which redirects to the PullRequest class to make a PR"""
        return PullRequest.create(ado_client, self.repo_id, branch_name, pull_request_title, pull_request_description)

    @staticmethod
    def get_all_pull_requests(ado_client: AdoClient, repo_id: str, status: PullRequestStatus = "all") -> list["PullRequest"]:
        return PullRequest.get_all_by_repo_id(ado_client, repo_id, status)

    def delete(self, ado_client: AdoClient) -> None:
        if self.is_disabled:
            self.update(ado_client, "is_disabled", False)
        self.delete_by_id(ado_client, self.repo_id)

    @staticmethod
    def get_content_static(
        ado_client: AdoClient, repo_id: str, file_types: list[str] | None = None, branch_name: str = "main"
    ) -> dict[str, str]:
        repo = Repo.get_by_id(ado_client, repo_id)
        return repo.get_contents(ado_client, file_types, branch_name)


# ====================================================================


@dataclass
class BuildRepository:
    build_repository_id: str = field(metadata={"is_id_field": True})
    name: str | None = None
    type: str = "TfsGit"
    clean: bool | None = None
    checkout_submodules: bool = field(default=False, metadata={"internal_name": "checkoutSubmodules"})

    @classmethod
    def from_request_payload(cls, data: dict[str, str | bool]) -> "BuildRepository":
        return cls(data["id"], data.get("name"), data.get("type", "TfsGit"), data.get("clean"), data.get("checkoutSubmodules", False))  # type: ignore[arg-type]

    @classmethod
    def from_json(cls, data: dict[str, str | bool]) -> "BuildRepository":
        return cls(data["id"], data.get("name"), data.get("type", "TfsGit"), data.get("clean"), data.get("checkoutSubmodules", False))  # type: ignore[arg-type]

    def to_json(self) -> dict[str, str | bool | None]:
        return {
            "id": self.build_repository_id, "name": self.name, "type": self.type,
            "clean": self.clean, "checkoutSubmodules": self.checkout_submodules,  # fmt: skip
        }

import json
import zipfile
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal

import requests
import yaml

from ado_wrapper.resources.branches import Branch
from ado_wrapper.resources.commits import Commit, GitIgnoreTemplateType
from ado_wrapper.resources.merge_policies import MergePolicies, MergePolicyDefaultReviewer
from ado_wrapper.resources.pull_requests import PullRequest, PullRequestStatus
from ado_wrapper.state_managed_abc import StateManagedResource
from ado_wrapper.errors import ResourceNotFound, UnknownError
from ado_wrapper.utils import binary_data_to_file_dictionary  # requires_perms

if TYPE_CHECKING:
    from ado_wrapper.client import AdoClient
    from ado_wrapper.resources.merge_policies import MergeBranchPolicy, WhenChangesArePushed

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

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "Repo":
        return cls(
            data["id"], data["name"], data.get("defaultBranch", "main").removeprefix("refs/heads/"),
            bool(data.get("isDisabled", False))  # fmt: skip
        )

    # @classmethod
    # def from_create_args(cls, name: str, *_: list[Any]) -> "Repo":
    #     return cls("id", name)

    @classmethod
    # @requires_perms("Git Repositories/Read")
    def get_by_id(cls, ado_client: "AdoClient", repo_id: str) -> "Repo":
        return super()._get_by_url(
            ado_client,
            f"/{ado_client.ado_project_name}/_apis/git/repositories/{repo_id}?api-version=7.1",
        )

    @classmethod
    # @requires_perms("Git Repositories/Create repository")
    def create(
        cls, ado_client: "AdoClient", name: str, include_readme: bool = True,
        git_ignore_template: GitIgnoreTemplateType | None = None,  # fmt: skip
    ) -> "Repo":
        repo: Repo = super()._create(
            ado_client,
            f"/{ado_client.ado_project_name}/_apis/git/repositories?api-version=7.1",
            {"name": name},
        )
        if include_readme and git_ignore_template is not None:
            Commit.add_readme_and_gitignore(ado_client, repo.repo_id, git_ignore_template)
        elif include_readme:
            Commit.add_initial_readme(ado_client, repo.repo_id)
        elif git_ignore_template is not None:
            Commit.add_git_ignore_template(ado_client, repo.repo_id, git_ignore_template)
        return repo

    def update(self, ado_client: "AdoClient", attribute_name: RepoEditableAttribute, attribute_value: Any) -> None:
        return super()._update(
            ado_client, "patch",
            f"/{ado_client.ado_project_name}/_apis/git/repositories/{self.repo_id}?api-version=7.1",
            attribute_name, attribute_value, {},  # fmt: skip
        )

    @classmethod
    def delete_by_id(cls, ado_client: "AdoClient", repo_id: str) -> None:
        for pull_request in Repo.get_all_pull_requests(ado_client, repo_id, "all"):
            ado_client.state_manager.remove_resource_from_state("PullRequest", pull_request.pull_request_id)
        # for branch in Branch.get_all_by_repo(ado_client, repo_id):
        #     ado_client.state_manager.remove_resource_from_state("Branch", branch.name)
        # TODO: Remove all tags from state as well, and whatever else repos have.
        # TODO: This never checks if it's disabled, so might error
        return super()._delete_by_id(
            ado_client,
            f"/{ado_client.ado_project_name}/_apis/git/repositories/{repo_id}?api-version=7.1",
            repo_id,
        )

    @classmethod
    def get_all(cls, ado_client: "AdoClient") -> list["Repo"]:
        return super()._get_all(
            ado_client,
            f"/{ado_client.ado_project_name}/_apis/git/repositories?api-version=7.1",
        )  # pyright: ignore[reportReturnType]

    def link(self, ado_client: "AdoClient") -> str:
        return f"https://dev.azure.com//{ado_client.ado_org_name}/{ado_client.ado_project_name}/_git/{self.name}"

    # ============ End of requirement set by all state managed resources ================== #
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # =============== Start of additional methods included with class ===================== #

    @classmethod
    def get_by_name(cls, ado_client: "AdoClient", repo_name: str) -> "Repo | None":
        return cls._get_by_abstract_filter(ado_client, lambda repo: repo.name == repo_name)

    def get_file(self, ado_client: "AdoClient", file_path: str, branch_name: str = "main") -> str:
        """Gets a single file by path, auto_decode converts json files from text to dictionaries"""
        request = ado_client.session.get(
            f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_apis/git/repositories/{self.repo_id}/items?path={file_path}&versionType={'Branch'}&version={branch_name}&api-version=7.1",
        )
        if request.status_code == 404:
            raise ResourceNotFound(f"File {file_path} not found in repo {self.name} ({self.repo_id})")
        if request.status_code != 200:
            raise UnknownError(f"Error getting file {file_path} from repo {self.repo_id}: {request.text}")
        return request.text  # This is the file content

    def get_and_decode_file(self, ado_client: "AdoClient", file_path: str, branch_name: str = "main") -> dict[str, Any]:
        file_content = self.get_file(ado_client, file_path, branch_name)
        if file_path.endswith(".json"):
            return json.loads(file_content)  # type: ignore[no-any-return]
        if file_path.endswith(".yaml") or file_path.endswith(".yml"):
            return yaml.safe_load(file_content)  # type: ignore[no-any-return]
        raise TypeError("Can only decode .json, .yaml or .yml files!")

    def get_contents(self, ado_client: "AdoClient", file_types: list[str] | None = None, branch_name: str = "main") -> dict[str, str]:
        """https://learn.microsoft.com/en-us/rest/api/azure/devops/git/items/get?view=azure-devops-rest-7.1&tabs=HTTP
        This function downloads the contents of a repo, and returns a dictionary of the files and their contents
        The file_types parameter is a list of file types to filter for, e.g. ["json", "yaml"] etc."""
        try:
            request = ado_client.session.get(
                f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_apis/git/repositories/{self.repo_id}/items?recursionLevel={'Full'}&download={True}&$format={'Zip'}&versionDescriptor.version={branch_name}&api-version=7.1",
            )
        except requests.exceptions.ConnectionError:
            if not ado_client.suppress_warnings:
                print(f"[ADO_WRAPPER] Connection error, failed to download {self.repo_id}")
            return {}
        if request.status_code == 404:
            raise ResourceNotFound(f"Repo {self.repo_id} does not have any branches or content!")
        if request.status_code != 200:
            if not ado_client.suppress_warnings:
                print(f"[ADO_WRAPPER] Error getting repo contents for {self.name} ({self.repo_id}):", request.text)
            return {}

        try:
            files = binary_data_to_file_dictionary(request.content, file_types, ado_client.suppress_warnings)
        except zipfile.BadZipFile as e:
            if not ado_client.suppress_warnings:
                print(f"[ADO_WRAPPER] {self.name} ({self.repo_id}) couldn't be unzipped:", e)
        return files

    def create_pull_request(
        self, ado_client: "AdoClient", branch_name: str, pull_request_title: str, pull_request_description: str,
        to_branch_name: str = "main", is_draft: bool = False
    ) -> PullRequest:  # fmt: skip
        """Helper function which redirects to the PullRequest class to make a PR"""
        return PullRequest.create(
            ado_client, self.repo_id, pull_request_title, pull_request_description, branch_name, to_branch_name, is_draft
        )

    @staticmethod
    def get_all_pull_requests(ado_client: "AdoClient", repo_id: str, status: PullRequestStatus = "all") -> list[PullRequest]:
        return PullRequest.get_all_by_repo_id(ado_client, repo_id, status)

    def delete(self, ado_client: "AdoClient") -> None:
        if self.is_disabled:
            self.update(ado_client, "is_disabled", False)
        self.delete_by_id(ado_client, self.repo_id)

    @staticmethod
    def get_content_static(
        ado_client: "AdoClient", repo_id: str, file_types: list[str] | None = None, branch_name: str = "main"
    ) -> dict[str, str]:
        """Fetches the repo for you."""
        repo = Repo.get_by_id(ado_client, repo_id)
        return repo.get_contents(ado_client, file_types, branch_name)

    @staticmethod
    def get_branch_merge_policy(ado_client: "AdoClient", repo_id: str, branch_name: str = "main") -> "MergeBranchPolicy | None":
        return MergePolicies.get_branch_policy(ado_client, repo_id, branch_name)

    @staticmethod
    def set_branch_merge_policy(
        ado_client: "AdoClient", repo_id: str, minimum_approver_count: int,
        creator_vote_counts: bool, prohibit_last_pushers_vote: bool, allow_completion_with_rejects: bool,
        when_new_changes_are_pushed: "WhenChangesArePushed", branch_name: str = "main",  # fmt: skip
    ) -> MergePolicies | None:
        return MergePolicies.set_branch_policy(ado_client, repo_id, minimum_approver_count, creator_vote_counts,
                                               prohibit_last_pushers_vote, allow_completion_with_rejects, when_new_changes_are_pushed,
                                               branch_name)  # fmt: skip

    @classmethod
    def get_all_repos_with_required_reviewer(cls, ado_client: "AdoClient", reviewer_email: str) -> list["Repo"]:
        return [
            repo for repo in Repo.get_all(ado_client)
            if any(x.email.lower() == reviewer_email.lower() for x in MergePolicyDefaultReviewer.get_default_reviewers(ado_client, repo.repo_id))
        ]  # fmt: skip

    def set_default_branch(self, ado_client: "AdoClient", new_default_branch_name: str) -> None:
        branches = Branch.get_all_by_repo(ado_client, self.name)
        if new_default_branch_name not in [x.name for x in branches]:
            Branch.create(ado_client, self.repo_id, new_default_branch_name, self.default_branch)
        request = ado_client.session.patch(
            f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_apis/git/repositories/{self.repo_id}?api-version=6.0",
            json={"defaultBranch": f"refs/heads/{new_default_branch_name}"},
        )
        if request.status_code != 200:
            raise UnknownError("Error, failed to set the default branch for this repo!")


# ====================================================================


@dataclass
class BuildRepository:
    build_repository_id: str = field(metadata={"is_id_field": True})
    name: str | None = None
    type: str = "TfsGit"
    clean: bool | None = None
    checkout_submodules: bool = field(default=False, metadata={"internal_name": "checkoutSubmodules"})

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "BuildRepository":
        return cls(data["id"], data.get("name"), data.get("type", "TfsGit"),
                   data.get("clean"), data.get("checkoutSubmodules", False))  # fmt: skip

    @classmethod
    def from_json(cls, data: dict[str, str | bool]) -> "BuildRepository":
        return cls(data["id"], data.get("name"), data.get("type", "TfsGit"), data.get("clean"), data.get("checkoutSubmodules", False))  # type: ignore[arg-type]

    def to_json(self) -> dict[str, str | bool | None]:
        return {
            "id": self.build_repository_id, "name": self.name, "type": self.type,
            "clean": self.clean, "checkoutSubmodules": self.checkout_submodules,  # fmt: skip
        }

from __future__ import annotations

import io
import zipfile
from dataclasses import dataclass, field
from typing import Any, Literal, TYPE_CHECKING

import requests

from ado_wrapper.state_managed_abc import StateManagedResource
from ado_wrapper.resources.pull_requests import PullRequest, PullRequestStatus
from ado_wrapper.resources.commits import Commit
from ado_wrapper.utils import ResourceNotFound, UnknownError

if TYPE_CHECKING:
    from ado_wrapper.client import AdoClient

RepoEditableAttribute = Literal["name", "default_branch", "is_disabled"]
WhenChangesArePushed = Literal["require_revote_on_each_iteration", "require_revote_on_last_iteration", "reset_votes_on_source_push", "reset_rejections_on_source_push", "do_nothing"]

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
        return super().get_by_url(
            ado_client,
            f"/{ado_client.ado_project}/_apis/git/repositories/{repo_id}?api-version=7.1",
        )  # type: ignore[return-value]

    @classmethod
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
        # TODO: This never checks if it's disabled, so might error
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
    def get_by_name(cls, ado_client: AdoClient, repo_name: str) -> "Repo | None":  # type: ignore[return]
        """Warning, this function must fetch `all` repos to work, be cautious when calling it in a loop."""
        for repo in cls.get_all(ado_client):
            if repo.name == repo_name:
                return repo

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

    @staticmethod
    def get_branch_policy(ado_client: AdoClient, repo_id: str, branch_name: str = "main") -> "RepoBranchPolicies | None":
        return RepoBranchPolicies.get_by_repo_id(ado_client, repo_id, branch_name)

    @staticmethod
    def set_branch_policy(ado_client: AdoClient, policy_id: str | None, repo_id: str, minimum_approver_count: int,
                          creator_vote_counts: bool, prohibit_last_pushers_vote: bool, allow_completion_with_rejects: bool,
                          when_new_changes_are_pushed: WhenChangesArePushed, branch_name: str = "main") -> "RepoBranchPolicies | None":
        return RepoBranchPolicies.set_branch_policy(ado_client, policy_id, repo_id, minimum_approver_count, creator_vote_counts,
                                                    prohibit_last_pushers_vote, allow_completion_with_rejects, when_new_changes_are_pushed,
                                                    branch_name)

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


name_mapping = {
    "requireVoteOnEachIteration": "require_revote_on_each_iteration",
    "requireVoteOnLastIteration": "require_revote_on_last_iteration",
    "resetOnSourcePush": "reset_votes_on_source_push",
    "resetRejectionsOnSourcePush": "reset_rejections_on_source_push",
    "do_nothing": "do_nothing"
}

@dataclass
class RepoBranchPolicies(StateManagedResource):
    policy_id: str = field(metadata={"is_id_field": True})
    policy_group_uuid: str
    repo_id: str
    branch_name: str
    minimum_approver_count: int
    creator_vote_counts: bool
    prohibit_last_pushers_vote: bool
    allow_completion_with_rejects: bool
    when_new_changes_are_pushed: WhenChangesArePushed

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "RepoBranchPolicies | None":  # type: ignore[override]
        policy_groups = data["dataProviders"]["ms.vss-code-web.branch-policies-data-provider"]["policyGroups"]
        if not policy_groups:
            return None
        first_policy_group = list(policy_groups.values())[0]
        if first_policy_group is None or first_policy_group["currentScopePolicies"] is None:
            return None
        settings = first_policy_group["currentScopePolicies"][0]["settings"]
        policy_group_id = list(policy_groups.keys())[0]
        when_new_changes_are_pushed = name_mapping[([x for x in ("requireVoteOnEachIteration", "requireVoteOnLastIteration", "resetOnSourcePush", "resetRejectionsOnSourcePush") if settings.get(x, False)] or ["do_nothing"])[0]]  # Any or "do_nothing"
        return cls(
            first_policy_group["currentScopePolicies"][0]["id"], policy_group_id, settings["scope"][0]["refName"].removeprefix("refs/heads/"), settings["scope"][0]["repositoryId"],
            settings["minimumApproverCount"], settings["creatorVoteCounts"], settings["blockLastPusherVote"], settings["allowDownvotes"],
            when_new_changes_are_pushed  # type: ignore[arg-type]
        )

    @classmethod
    def get_by_repo_id(cls, ado_client: AdoClient, repo_id: str, branch_name: str = "main") -> "RepoBranchPolicies | None":
        """Unofficial API, may break at any time."""
        headers = {"Accept": "application/json;api-version=7.0-preview.1;excludeUrls=true;enumsAsNumbers=true;msDateFormat=true;noArrayWrap=true"}
        payload = {"contributionIds": ["ms.vss-code-web.branch-policies-data-provider"], "dataProviderContext": {"properties": {"repositoryId": repo_id, "refName": f"refs/heads/{branch_name}", "sourcePage": {"routeValues": {"project": ado_client.ado_project, "adminPivot": "repositories", "controller": "ContributedPage"," action": "Execute"}}}}}
        request = requests.post(f"https://dev.azure.com/{ado_client.ado_org}/_apis/Contribution/HierarchyQuery", headers=headers, json=payload, auth=ado_client.auth).json()
        return cls.from_request_payload(request)

    @staticmethod
    def _get_type_id(ado_client: AdoClient) -> str:
        request = requests.get(f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/policy/types?api-version=6.0", auth=ado_client.auth)
        return [x for x in request.json()["value"] if x["displayName"] == "Minimum number of reviewers"][0]["id"]  # type: ignore[no-any-return]

    @classmethod
    def set_branch_policy(cls, ado_client: AdoClient, policy_id: str | None, repo_id: str, minimum_approver_count: int,
                          creator_vote_counts: bool, prohibit_last_pushers_vote: bool, allow_completion_with_rejects: bool,
                          when_new_changes_are_pushed: WhenChangesArePushed, branch_name: str = "main") -> None:
        """Unofficial API, may break at any time. Sets the perms for a branch, can also be used as a "create" function."""
        payload = {
            "settings": {
                "minimumApproverCount": minimum_approver_count,
                "creatorVoteCounts":    creator_vote_counts,
                "blockLastPusherVote":  prohibit_last_pushers_vote,
                "allowDownvotes":       allow_completion_with_rejects,
                "requireVoteOnEachIteration":  when_new_changes_are_pushed == "require_revote_on_each_iteration",
                "requireVoteOnLastIteration":  when_new_changes_are_pushed == "require_revote_on_last_iteration",
                "resetOnSourcePush":           when_new_changes_are_pushed == "reset_votes_on_source_push",
                "resetRejectionsOnSourcePush": when_new_changes_are_pushed == "reset_rejections_on_source_push",
                "scope": [{"refName": f"refs/heads/{branch_name}", "matchKind": "Exact", "repositoryId": repo_id}],
            },
            "isEnabled": True, "isBlocking": True,
            "type": {"id": cls._get_type_id(ado_client)},
        }
        request_method = "POST" if policy_id is None else "PUT"
        request = requests.request(request_method, f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project_id}/_apis/policy/Configurations/{policy_id or ''}".rstrip("/"),
                                   json=payload, headers={"Accept": "application/json;api-version=7.1"}, auth=ado_client.auth)
        assert request.status_code == 200, f"Error setting branch policy: {request.text}"
        # return cls.from_request_payload(request.json())


RepoBranchPolicies.create = RepoBranchPolicies.set_branch_policy  # type: ignore[assignment]

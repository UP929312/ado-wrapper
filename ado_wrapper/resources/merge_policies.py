from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal, TYPE_CHECKING

import requests

from ado_wrapper.state_managed_abc import StateManagedResource
from ado_wrapper.resources.users import Reviewer
from ado_wrapper.utils import from_ado_date_string

if TYPE_CHECKING:
    from ado_wrapper.client import AdoClient

WhenChangesArePushed = Literal["require_revote_on_each_iteration", "require_revote_on_last_iteration", "reset_votes_on_source_push", "reset_rejections_on_source_push", "do_nothing"]
name_mapping = {
    "requireVoteOnEachIteration": "require_revote_on_each_iteration",
    "requireVoteOnLastIteration": "require_revote_on_last_iteration",
    "resetOnSourcePush": "reset_votes_on_source_push",
    "resetRejectionsOnSourcePush": "reset_rejections_on_source_push",
    "do_nothing": "do_nothing"
}

def _get_type_id(ado_client: AdoClient, action_type: str) -> str:
    """Used internally to get a specific update request ID"""
    request = requests.get(f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/policy/types?api-version=6.0", auth=ado_client.auth)
    # print([(x["displayName"], x["id"]) for x in request.json()["value"]])
    return [x for x in request.json()["value"] if x["displayName"] == action_type][0]["id"]  # type: ignore[no-any-return]


@dataclass
class MergePolicyDefaultReviewer(StateManagedResource):
    policy_id: str = field(metadata={"is_id_field": True})
    required_reviewer_id: list[str]
    is_required: bool

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> StateManagedResource:
        return cls(data["id"], data["settings"]["requiredReviewerIds"][0], data["isBlocking"])

    @staticmethod
    def get_default_reviewers(ado_client: AdoClient, repo_id: str, branch_name: str = "main") -> list[Reviewer]:
        payload = {"contributionIds": ["ms.vss-code-web.branch-policies-data-provider"],
                   "dataProviderContext": {"properties": {"projectId": ado_client.ado_project_id, "repositoryId": repo_id, "refName": f"refs/heads/{branch_name}"}}}
        request = requests.post("https://dev.azure.com/VFCloudEngineering/_apis/Contribution/HierarchyQuery?api-version=7.1-preview.1",
                               json=payload, auth=ado_client.auth).json()
        if request is None:
            return []
        all_reviewers = [Reviewer(x["displayName"], x["uniqueName"], x["id"], 0, False) for x in request["dataProviders"]["ms.vss-code-web.branch-policies-data-provider"]["identities"]]
        for policy_group in request["dataProviders"]["ms.vss-code-web.branch-policies-data-provider"]["policyGroups"].values():
            if policy_group["currentScopePolicies"] is None:
                continue
            is_required = policy_group["currentScopePolicies"][0]["isBlocking"]
            if is_required and "requiredReviewerIds" in policy_group["currentScopePolicies"][0]["settings"]:
                reviewers = policy_group["currentScopePolicies"][0]["settings"]["requiredReviewerIds"]
                for reviewer_id in reviewers:
                    [x for x in all_reviewers if x.member_id == reviewer_id][0].is_required = True
        return all_reviewers

    @classmethod
    def add_default_reviewer(cls, ado_client: AdoClient, repo_id: str, reviewer_id: str, is_required: bool, branch_name: str = "main") -> None:
        if reviewer_id in [x.member_id for x in cls.get_default_reviewers(ado_client, repo_id, branch_name)]:
            raise ValueError("Reviewer already exists! To update, please remove the reviewer first.")
        payload = {
            "type": {"id": _get_type_id(ado_client, "Required reviewers")}, "isBlocking": is_required, "isEnabled": True,
            "settings": {
                "requiredReviewerIds": [reviewer_id],
                "scope":[{"repositoryId": repo_id, "refName": f"refs/heads/{branch_name}", "matchKind": "Exact"}]
            }}
        request = requests.post(f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project_id}/_apis/policy/configurations?api-version=7.1",
                                json=payload, headers={"Accept": "application/json;api-version=7.1"}, auth=ado_client.auth)
        assert request.status_code == 200, f"Error setting branch policy: {request.text}"

    @staticmethod
    def remove_default_reviewer(ado_client: AdoClient, repo_id: str, reviewer_id: str, branch_name: str = "main") -> None:
        policies = MergePolicies.get_default_reviewers_by_repo_id(ado_client, repo_id, branch_name)
        policy_id = [x for x in policies if x.required_reviewer_id == reviewer_id][0].policy_id if policies is not None else None  # type: ignore[comparison-overlap]
        if not policy_id:
            return
        request = requests.delete(f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project_id}/_apis/policy/configurations/{policy_id}?api-version=7.1", auth=ado_client.auth)
        assert request.status_code == 204, "Error removing required reviewer"


@dataclass
class MergeBranchPolicy(StateManagedResource):
    policy_id: str = field(metadata={"is_id_field": True})
    policy_group_uuid: str = field(repr=False)
    repo_id: str = field(repr=False)
    branch_name: str = field(repr=False)
    minimum_approver_count: int
    creator_vote_counts: bool
    prohibit_last_pushers_vote: bool
    allow_completion_with_rejects: bool
    when_new_changes_are_pushed: WhenChangesArePushed
    created_date: datetime = field(repr=False)

    @classmethod
    def from_request_payload(cls, policy_group_id: str, policy: dict[str, Any]) -> "MergeBranchPolicy":  # type: ignore[override]
        settings = policy["settings"]
        when_new_changes_are_pushed = name_mapping[([x for x in ("requireVoteOnEachIteration", "requireVoteOnLastIteration", "resetOnSourcePush", "resetRejectionsOnSourcePush") if settings.get(x, False)] or ["do_nothing"])[0]]  # Any or "do_nothing"  # fmt: skip
        return cls(
            policy["id"], policy_group_id, settings["scope"][0]["refName"].removeprefix("refs/heads/"), settings["scope"][0]["repositoryId"],
            settings["minimumApproverCount"], settings["creatorVoteCounts"], settings["blockLastPusherVote"], settings["allowDownvotes"],
            when_new_changes_are_pushed, from_ado_date_string(policy["createdDate"])   # type: ignore[arg-type]  # fmt: skip
        )

    @classmethod
    def get_branch_policy(cls, ado_client: AdoClient, repo_id: str, branch_name: str) -> "MergeBranchPolicy":
        """Unofficial API, may break at any time. Gets the latest merge requirements for a pull request."""
        return MergePolicies.get_all_branch_policies_by_repo_id(ado_client, repo_id)[0]  # type: ignore[index]

    @staticmethod
    def set_branch_policy(ado_client: AdoClient, repo_id: str, minimum_approver_count: int,
                          creator_vote_counts: bool, prohibit_last_pushers_vote: bool, allow_completion_with_rejects: bool,
                          when_new_changes_are_pushed: WhenChangesArePushed, branch_name: str = "main") -> None:  # fmt: skip
        """Unofficial API, may break at any time. Sets the perms for a pull request, can also be used as a "update" function."""
        existing_policy = MergePolicies.get_all_by_repo_id(ado_client, repo_id, branch_name)
        latest_policy_id = existing_policy[0].policy_id if existing_policy is not None else None
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
                "scope": [{"refName": f"refs/heads/{branch_name}", "repositoryId": repo_id, "matchKind": "Exact"}],
            },
            "isEnabled": True, "isBlocking": True,
            "type": {"id": _get_type_id(ado_client, "Minimum number of reviewers")},
        }
        request_method = "POST" if latest_policy_id is None else "PUT"
        request = requests.request(request_method, f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project_id}/_apis/policy/Configurations/{latest_policy_id or ''}".rstrip("/"),
                                   json=payload, headers={"Accept": "application/json;api-version=7.1"}, auth=ado_client.auth)
        assert request.status_code == 200, f"Error setting branch policy: {request.text}"


@dataclass
class MergePolicies(StateManagedResource):
    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> list["MergePolicyDefaultReviewer | MergeBranchPolicy"] | None:  # type: ignore[override]
        """Used internally to get a list of all policies."""
        policy_groups: dict[str, Any] = data["dataProviders"]["ms.vss-code-web.branch-policies-data-provider"]["policyGroups"] or {}  # fmt: skip
        all_policies = []
        for policy_group_id, policy_group in policy_groups.items():
            if policy_group["currentScopePolicies"] is None:
                continue
            for policy in policy_group["currentScopePolicies"]:
                settings = policy["settings"]
                if "cep-account-main" in settings:
                    continue
                if "requiredReviewerIds" in settings:
                    all_policies.append(MergePolicyDefaultReviewer.from_request_payload(policy))
                else:
                    all_policies.append(MergeBranchPolicy.from_request_payload(policy_group_id, policy))
        return all_policies or None  # type: ignore[return-value]

    @classmethod
    def get_all_by_repo_id(cls, ado_client: AdoClient, repo_id: str, branch_name: str = "main") -> list["MergePolicyDefaultReviewer | MergeBranchPolicy"] | None:  # fmt: skip
        payload = {"contributionIds": ["ms.vss-code-web.branch-policies-data-provider"], "dataProviderContext": {"properties": {
            "repositoryId": repo_id, "refName": f"refs/heads/{branch_name}", "sourcePage": {"routeValues": {"project": ado_client.ado_project}}}}}  # fmt: skip
        request = requests.post(f"https://dev.azure.com/{ado_client.ado_org}/_apis/Contribution/HierarchyQuery?api-version=7.0-preview.1",
                                json=payload, auth=ado_client.auth).json()  # fmt: skip
        return cls.from_request_payload(request)

    @classmethod
    def get_all_branch_policies_by_repo_id(cls, ado_client: AdoClient, repo_id: str, branch_name: str = "main") -> list[MergeBranchPolicy] | None:  # fmt: skip
        policies = cls.get_all_by_repo_id(ado_client, repo_id, branch_name)
        return (
            sorted([x for x in policies if isinstance(x, MergeBranchPolicy)], key=lambda x: x.created_date, reverse=True)
            if policies is not None else None
        )  # fmt: skip

    @classmethod
    def get_default_reviewers_by_repo_id(cls, ado_client: AdoClient, repo_id: str, branch_name: str = "main") -> list[MergePolicyDefaultReviewer] | None:  # fmt: skip
        policies = cls.get_all_by_repo_id(ado_client, repo_id, branch_name)
        return [x for x in policies if isinstance(x, MergePolicyDefaultReviewer)] if policies is not None else None

    # ================== Default Reviewers ================== #
    @staticmethod
    def add_default_reviewer(ado_client: AdoClient, repo_id: str, reviewer_id: str, is_required: bool, branch_name: str = "main") -> None:
        return MergePolicyDefaultReviewer.add_default_reviewer(ado_client, repo_id, reviewer_id, is_required, branch_name)

    @staticmethod
    def get_default_reviewers(ado_client: AdoClient, repo_id: str, branch_name: str = "main") -> list[Reviewer]:
        return MergePolicyDefaultReviewer.get_default_reviewers(ado_client, repo_id, branch_name)

    @staticmethod
    def remove_default_reviewer(ado_client: AdoClient, repo_id: str, reviewer_id: str, branch_name: str = "main") -> None:
        return MergePolicyDefaultReviewer.remove_default_reviewer(ado_client, repo_id, reviewer_id, branch_name)

    # ================== Branch Policies ================== #
    @staticmethod
    def set_branch_policy(ado_client: AdoClient, repo_id: str, minimum_approver_count: int,
                          creator_vote_counts: bool, prohibit_last_pushers_vote: bool, allow_completion_with_rejects: bool,
                          when_new_changes_are_pushed: WhenChangesArePushed, branch_name: str = "main") -> None:
        return MergeBranchPolicy.set_branch_policy(ado_client, repo_id, minimum_approver_count, creator_vote_counts,
                                                   prohibit_last_pushers_vote, allow_completion_with_rejects,
                                                   when_new_changes_are_pushed, branch_name)  # fmt: skip

    @staticmethod
    def get_branch_policy(ado_client: AdoClient, repo_id: str, branch_name: str = "main") -> MergeBranchPolicy:
        return MergeBranchPolicy.get_branch_policy(ado_client, repo_id, branch_name)

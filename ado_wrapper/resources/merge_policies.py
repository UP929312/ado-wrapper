from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal

from ado_wrapper.resources.users import AdoUser, Reviewer
from ado_wrapper.state_managed_abc import StateManagedResource
from ado_wrapper.utils import from_ado_date_string, build_hierarchy_payload
from ado_wrapper.errors import ConfigurationError

if TYPE_CHECKING:
    from ado_wrapper.client import AdoClient

WhenChangesArePushed = Literal["require_revote_on_each_iteration", "require_revote_on_last_iteration",
                               "reset_votes_on_source_push", "reset_rejections_on_source_push", "do_nothing"]  # fmt: skip
merge_complete_name_mapping = {
    "requireVoteOnEachIteration": "require_revote_on_each_iteration",
    "requireVoteOnLastIteration": "require_revote_on_last_iteration",
    "resetOnSourcePush": "reset_votes_on_source_push",
    "resetRejectionsOnSourcePush": "reset_rejections_on_source_push",
    "do_nothing": "do_nothing",
}
MergeTypeOptionsType = Literal[
    "allow_basic_no_fast_forwards", "allow_squash", "allow_rebase_and_fast_forward", "allow_rebase_with_merge_commit"
]
limit_merge_type_mapping = {
    "allowNoFastForward": "allow_basic_no_fast_forwards",
    "allowSquash": "allow_squash",
    "allowRebase": "allow_rebase_and_fast_forward",
    "allowRebaseMerge": "allow_rebase_with_merge_commit",
}


def _get_type_id(ado_client: "AdoClient", action_type: str) -> str:
    """Used internally to get a specific update request ID"""
    request = ado_client.session.get(
        f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_apis/policy/types?api-version=6.0"
    )
    return str([x for x in request.json()["value"] if x["displayName"] == action_type][0]["id"])


@dataclass
class MergePolicyDefaultReviewer(StateManagedResource):
    """Represents 1 required reviewer and if they're required."""

    policy_id: str = field(metadata={"is_id_field": True})
    required_reviewer_id: str
    is_required: bool

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "MergePolicyDefaultReviewer":
        return cls(data["id"], data["settings"]["requiredReviewerIds"][0], data["isBlocking"])

    @classmethod
    def get_default_reviewers(cls, ado_client: "AdoClient", repo_id: str, branch_name: str = "main") -> list[Reviewer]:
        PAYLOAD = build_hierarchy_payload(
            ado_client, "code-web.branch-policies-data-provider",
            additional_properties={"repositoryId": repo_id, "refName": f"refs/heads/{branch_name}"},
        )  # fmt: skip
        request = ado_client.session.post(
            f"https://dev.azure.com/{ado_client.ado_org_name}/_apis/Contribution/HierarchyQuery?api-version=7.1-preview.1",
            json=PAYLOAD,
        ).json()
        if request is None:
            return []
        if "ms.vss-code-web.branch-policies-data-provider" not in request["dataProviders"]:
            if not ado_client.suppress_warnings:
                print(f"[ADO_WRAPPER] No default reviewers found for repo {repo_id}! Most likely it's disabled.")
            return []
        identities = request["dataProviders"]["ms.vss-code-web.branch-policies-data-provider"]["identities"]
        # === # Maybe switch ["id"] to ["descriptor"]?
        all_reviewers = [Reviewer(x["displayName"], x["uniqueName"], x["id"]) for x in identities]  # fmt: skip
        for policy_group in request["dataProviders"]["ms.vss-code-web.branch-policies-data-provider"]["policyGroups"].values():
            if policy_group["currentScopePolicies"] is None:
                continue
            is_required = policy_group["currentScopePolicies"][0]["isBlocking"]
            if is_required and "requiredReviewerIds" in policy_group["currentScopePolicies"][0]["settings"]:
                reviewers = policy_group["currentScopePolicies"][0]["settings"]["requiredReviewerIds"]
                for reviewer_id in reviewers:
                    [x for x in all_reviewers if x.member_id == reviewer_id][0].is_required = True
        # =====================================================================================
        # Fix local_ids (convert them to origin_ids)
        local_ids_to_origin_ids = AdoUser._convert_local_ids_to_origin_ids(  # pylint: disable=protected-access
            ado_client, [x.member_id for x in all_reviewers]
        )  # pylint: disable=protected-access
        for reviewer in [x for x in all_reviewers if x.member_id is not None]:
            reviewer.member_id = local_ids_to_origin_ids[reviewer.member_id]
        # =====================================================================================
        return all_reviewers

    @classmethod
    def add_default_reviewer(
        cls, ado_client: "AdoClient", repo_id: str, reviewer_origin_id: str, is_required: bool = True, branch_name: str = "main"  # fmt: skip
    ) -> None:
        if reviewer_origin_id in [x.member_id for x in cls.get_default_reviewers(ado_client, repo_id, branch_name)]:
            raise ValueError("Reviewer already exists! To update, please remove the reviewer first.")
        local_id = AdoUser._convert_origin_ids_to_local_ids(ado_client, [reviewer_origin_id])[  # pylint: disable=protected-access
            reviewer_origin_id
        ]
        payload = {
            "type": {"id": _get_type_id(ado_client, "Required reviewers")},
            "isBlocking": is_required,
            "isEnabled": True,
            "settings": {
                # We have to convert the origin id to local id for this to work ):
                "requiredReviewerIds": [local_id],
                "scope": [{"repositoryId": repo_id, "refName": f"refs/heads/{branch_name}", "matchKind": "Exact"}],
            },
        }
        request = ado_client.session.post(
            f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_apis/policy/configurations?api-version=7.1",
            json=payload,
        )
        if request.status_code == 400:
            raise ConfigurationError(f"Error adding default reviewer {request.text}")
        assert request.status_code == 200, f"Error setting branch policy: {request.text}"

    @staticmethod
    def remove_default_reviewer(ado_client: "AdoClient", repo_id: str, reviewer_id: str, branch_name: str = "main") -> None:
        # We can't use get_default_reviewers since we need to delete the policy, not the reviewer
        local_id = AdoUser._convert_origin_ids_to_local_ids(ado_client, [reviewer_id])[reviewer_id]  # pylint: disable=protected-access
        policies = MergePolicies.get_all_by_repo_id(ado_client, repo_id, branch_name)
        default_reviewer_policy = (
            [x for x in policies if isinstance(x, MergePolicyDefaultReviewer)]  # pylint: disable=not-an-iterable
            if policies is not None else None  # fmt: skip
        )
        if default_reviewer_policy is None:
            return
        policy_id = [x for x in default_reviewer_policy if x.required_reviewer_id == local_id][0].policy_id  # fmt: skip
        request = ado_client.session.delete(
            f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_apis/policy/configurations/{policy_id}?api-version=7.1",
        )
        assert request.status_code == 204, "Error removing required reviewer"


@dataclass
class MergeBranchPolicy(StateManagedResource):
    policy_id: str = field(metadata={"is_id_field": True})
    repo_id: str = field(repr=False)
    branch_name: str | None = field(repr=False)
    minimum_approver_count: int
    creator_vote_counts: bool
    prohibit_last_pushers_vote: bool
    allow_completion_with_rejects: bool
    when_new_changes_are_pushed: WhenChangesArePushed
    created_date: datetime = field(repr=False)
    is_inherited: bool = field(default=False, repr=False)

    @classmethod
    def from_request_payload(cls, data: dict[str, Any], is_inherited: bool) -> "MergeBranchPolicy":  # type: ignore[override]  # <- is_inherited
        settings = data["settings"]
        when_new_changes_are_pushed = merge_complete_name_mapping[
            ([x for x in merge_complete_name_mapping if settings.get(x, False)] or ["do_nothing"])[0]
        ]  # Any or "do_nothing"  # fmt: skip
        branch_name: str | None = settings["scope"][0]["refName"]
        return cls(
            data["id"], settings["scope"][0]["repositoryId"], (branch_name.removeprefix("refs/heads/") if branch_name else None),
            settings["minimumApproverCount"], settings["creatorVoteCounts"], settings["blockLastPusherVote"], settings["allowDownvotes"],
            when_new_changes_are_pushed, from_ado_date_string(data["createdDate"]),  # type: ignore[arg-type]
            is_inherited  # fmt: skip
        )

    @classmethod
    def get_branch_policy(cls, ado_client: "AdoClient", repo_id: str, branch_name: str = "main") -> "MergeBranchPolicy | None":
        """Gets the latest merge requirements for a pull request."""
        policies = MergePolicies.get_all_by_repo_id(ado_client, repo_id, branch_name)
        if policies is None:
            return None
        merge_branch_policies = sorted(
            [x for x in policies if isinstance(x, MergeBranchPolicy)],  # pylint: disable=not-an-iterable
            key=lambda x: x.created_date, reverse=True,  # fmt: skip
        )
        return merge_branch_policies[0] if merge_branch_policies else None

    @staticmethod
    def set_branch_policy(ado_client: "AdoClient", repo_id: str, minimum_approver_count: int,
                          creator_vote_counts: bool, prohibit_last_pushers_vote: bool, allow_completion_with_rejects: bool,
                          when_new_changes_are_pushed: WhenChangesArePushed, branch_name: str = "main") -> None:  # fmt: skip
        """Sets the perms for a pull request, can also be used as a "update" function."""
        existing_policy = MergePolicies.get_branch_policy(ado_client, repo_id, branch_name)
        latest_policy_id = f"/{existing_policy.policy_id}" if existing_policy is not None else ""
        payload = {
            "settings": {
                "minimumApproverCount": minimum_approver_count,
                "creatorVoteCounts": creator_vote_counts,
                "blockLastPusherVote": prohibit_last_pushers_vote,
                "allowDownvotes": allow_completion_with_rejects,
                "requireVoteOnEachIteration": when_new_changes_are_pushed == "require_revote_on_each_iteration",
                "requireVoteOnLastIteration": when_new_changes_are_pushed == "require_revote_on_last_iteration",
                "resetOnSourcePush": when_new_changes_are_pushed == "reset_votes_on_source_push",
                "resetRejectionsOnSourcePush": when_new_changes_are_pushed == "reset_rejections_on_source_push",
                "scope": [{"refName": f"refs/heads/{branch_name}", "repositoryId": repo_id, "matchKind": "Exact"}],
            },
            "type": {"id": _get_type_id(ado_client, "Minimum number of reviewers")},
            "isEnabled": True,
            "isBlocking": True,
        }
        request = ado_client.session.request(
            "PUT" if latest_policy_id else "POST",
            f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_apis/policy/Configurations{latest_policy_id}?api-version=7.1",  # fmt: skip
            json=payload,
        )
        assert request.status_code == 200, f"Error setting branch policy: {request.text}"


@dataclass
class MergeTypeRestrictionPolicy(StateManagedResource):
    policy_id: str = field(metadata={"is_id_field": True})
    repo_id: str = field(repr=False)
    branch_name: str | None = field(repr=False)
    created_date: datetime = field(repr=False)
    allow_basic_no_fast_forwards: bool = field(metadata={"internal_name": "allowNoFastForward"})
    allow_squash: bool = field(metadata={"internal_name": "allowSquash"})
    allow_rebase_and_fast_forward: bool = field(metadata={"internal_name": "allowRebase"})
    allow_rebase_with_merge_commit: bool = field(metadata={"internal_name": "allowRebaseMerge"})

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "MergeTypeRestrictionPolicy":
        settings = data["settings"]
        branch_name: str | None = settings["scope"][0]["refName"]
        return cls(
            data["id"], settings["scope"][0]["repositoryId"], (branch_name.removeprefix("refs/heads/") if branch_name else None),
            from_ado_date_string(data["createdDate"]),
            settings.get("allowNoFastForward", False), settings.get("allowSquash", False),
            settings.get("allowRebase"), settings.get("allowRebaseMerge"),  # fmt: skip
        )

    @classmethod
    def get_allowed_merge_types(
        cls, ado_client: "AdoClient", repo_id: str, branch_name: str = "main"
    ) -> "MergeTypeRestrictionPolicy | None":
        policies = MergePolicies.get_all_by_repo_id(ado_client, repo_id, branch_name)
        if policies is None:
            return None
        merge_type_restriction_policies = sorted(
            [x for x in policies if isinstance(x, MergeTypeRestrictionPolicy)],  # pylint: disable=not-an-iterable
            key=lambda x: x.created_date, reverse=True,  # fmt: skip
        )
        return merge_type_restriction_policies[0] if merge_type_restriction_policies else None

    @staticmethod
    def set_allowed_merge_types(ado_client: "AdoClient", repo_id: str, allow_basic_no_fast_forwards: bool, allow_squash: bool,
                                allow_rebase_and_fast_forward: bool, allow_rebase_with_merge_commit: bool,
                                branch_name: str = "main") -> None:  # fmt: skip
        """Sets the perms for a pull request's merge type (e.g. rebase), can also be used as a "update" function."""
        existing_policy = MergePolicies.get_allowed_merge_types(ado_client, repo_id, branch_name)
        latest_policy_id = f"/{existing_policy.policy_id}" if existing_policy is not None else ""
        payload = {
            "settings": {
                "allowNoFastForward": allow_basic_no_fast_forwards,
                "allowSquash": allow_squash,
                "allowRebase": allow_rebase_and_fast_forward,
                "allowRebaseMerge": allow_rebase_with_merge_commit,
                "scope": [{"refName": f"refs/heads/{branch_name}", "repositoryId": repo_id, "matchKind": "Exact"}],
            },
            "type": {"id": _get_type_id(ado_client, "Require a merge strategy")},
            "isEnabled": True,
            "isBlocking": True,
        }
        request = ado_client.session.request(
            "PUT" if latest_policy_id else "POST",
            f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_apis/policy/Configurations{latest_policy_id}?api-version=7.1",  # fmt: skip
            json=payload,
        )
        assert request.status_code == 200, f"Error setting merge type restriction policy: {request.text}"


@dataclass
class MergePolicies(StateManagedResource):
    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> list[MergePolicyDefaultReviewer | MergeBranchPolicy | MergeTypeRestrictionPolicy] | None:  # type: ignore[override]
        """Used internally to get a list of all policies."""
        policy_groups: dict[str, Any] = data["dataProviders"]["ms.vss-code-web.branch-policies-data-provider"]["policyGroups"] or {}  # fmt: skip
        all_policies: list[MergePolicyDefaultReviewer | MergeBranchPolicy | MergeTypeRestrictionPolicy] = []
        for policy_group in policy_groups.values():
            for policy in policy_group["currentScopePolicies"] or []:  # If it's None, don't loop
                settings = policy["settings"]
                # Build Validation {'buildDefinitionId': 4, 'queueOnSourceUpdateOnly': True, 'manualQueueOnly': False, 'displayName': None, 'validDuration': 720.0
                if "buildDefinitionId" in settings:
                    continue
                # Comments Required
                if policy.get("type", {"displayName": ""})["displayName"] == "Comment requirements":
                    continue
                # Limit merge types
                if any(x in settings for x in limit_merge_type_mapping):
                    all_policies.append(MergeTypeRestrictionPolicy.from_request_payload(policy))
                # Automatically included reviewers
                elif "requiredReviewerIds" in settings:
                    all_policies.append(MergePolicyDefaultReviewer.from_request_payload(policy))
                elif "minimumApproverCount" in settings:
                    new_policy = MergeBranchPolicy.from_request_payload(policy, False)
                    # if "inheritedPolicies" in policy_group:
                    #     new_policy.inherited_policies = [MergeBranchPolicy.from_request_payload(x) for x in policy_group["inheritedPolicies"]]
                    all_policies.append(new_policy)
                else:
                    print("[ADO_WRAPPER] Unknown policy type: ", policy)

            # for inherited_policy in policy_group["inheritedPolicies"] or []:
            #     all_policies.append(MergeBranchPolicy.from_request_payload(inherited_policy, True))

        return all_policies or None

    @classmethod
    def get_all_by_repo_id(cls, ado_client: "AdoClient", repo_id: str, branch_name: str = "main") -> list[MergePolicyDefaultReviewer | MergeBranchPolicy | MergeTypeRestrictionPolicy] | None:  # fmt: skip
        # TODO: Make this use the utils.build_hierarchy_payload
        payload = {"contributionIds": ["ms.vss-code-web.branch-policies-data-provider"], "dataProviderContext": {"properties": {
            "repositoryId": repo_id, "refName": f"refs/heads/{branch_name}", "sourcePage": {"routeValues": {"project": ado_client.ado_project_name}}}}}  # fmt: skip
        request = ado_client.session.post(
            f"https://dev.azure.com/{ado_client.ado_org_name}/_apis/Contribution/HierarchyQuery?api-version=7.0-preview.1",
            json=payload,
        ).json()
        return cls.from_request_payload(request)

    # ======================= Combined ====================== #
    @staticmethod
    def get_all_repo_policies(
        ado_client: "AdoClient", repo_id: str, branch_name: str = "main"
    ) -> tuple[list[Reviewer], MergeBranchPolicy | None, MergeTypeRestrictionPolicy | None]:  # fmt: skip
        default_reviewer = MergePolicyDefaultReviewer.get_default_reviewers(ado_client, repo_id, branch_name)
        branch_policy = MergeBranchPolicy.get_branch_policy(ado_client, repo_id, branch_name)
        allowed_merge_types = MergeTypeRestrictionPolicy.get_allowed_merge_types(ado_client, repo_id, branch_name)
        return (default_reviewer, branch_policy, allowed_merge_types)

    # ================== Default Reviewers ================== #
    @classmethod
    def get_default_reviewer_policy_by_repo_id(cls, ado_client: "AdoClient", repo_id: str, branch_name: str = "main") -> "list[MergePolicyDefaultReviewer] | None":  # fmt: skip
        policies = cls.get_all_by_repo_id(ado_client, repo_id, branch_name)
        return (
            [x for x in policies if isinstance(x, MergePolicyDefaultReviewer)]  # pylint: disable=not-an-iterable
            if policies is not None
            else None
        )

    add_default_reviewer = MergePolicyDefaultReviewer.add_default_reviewer
    get_default_reviewers = MergePolicyDefaultReviewer.get_default_reviewers
    remove_default_reviewer = MergePolicyDefaultReviewer.remove_default_reviewer

    # ================== Branch Policies ================== #
    get_branch_policy = MergeBranchPolicy.get_branch_policy
    set_branch_policy = MergeBranchPolicy.set_branch_policy

    # ================= Merge Type Policy ================= #
    set_allowed_merge_types = MergeTypeRestrictionPolicy.set_allowed_merge_types
    get_allowed_merge_types = MergeTypeRestrictionPolicy.get_allowed_merge_types

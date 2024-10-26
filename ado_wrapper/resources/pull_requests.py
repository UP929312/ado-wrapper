import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal

from ado_wrapper.resources.users import Member, Reviewer
from ado_wrapper.state_managed_abc import StateManagedResource, convert_from_json
from ado_wrapper.utils import from_ado_date_string, build_hierarchy_payload
from ado_wrapper.errors import ConfigurationError, UnknownError

if TYPE_CHECKING:
    from ado_wrapper.client import AdoClient
    from ado_wrapper.resources.repo import Repo
    from ado_wrapper.resources.groups import Group


PullRequestEditableAttribute = Literal["title", "description", "merge_status", "is_draft"]
PullRequestStatus = Literal["active", "completed", "abandoned", "all", "notSet"]
MergeStatus = Literal["succeeded", "conflicts", "rejectedByPolicy", "rejectedByUser", "queued", "notSet", "failure"]
DraftState = Literal["Include drafts", "Exclude drafts", "Only include drafts"]
CommentType = Literal["system", "regular", "codeChange", "unknown"]
PrCommentStatus = Literal["active", "pending", "fixed", "wontFix", "closed"]

merge_status_mapping: dict[int | None, MergeStatus] = {
    None: "notSet",
    0: "notSet",  # Status is not set. Default state.
    1: "queued",  # Pull request merge is queued.
    2: "conflicts",  # Pull request merge failed due to conflicts.
    3: "succeeded",  # Pull request merge succeeded.
    4: "rejectedByPolicy",  # Pull request merge rejected by policy.
    5: "failure",  # Pull request merge failed.
}

pr_status_mapping: dict[int, PullRequestStatus] = {
    0: "notSet",
    1: "active",
    2: "abandoned",
    3: "completed",
    4: "all",
}


@dataclass
class PullRequest(StateManagedResource):
    """https://learn.microsoft.com/en-us/rest/api/azure/devops/git/pull-requests?view=azure-devops-rest-7.1
    Merge status is how "merged" is is, either merged, conflicted, etc, pr_status is how approved it is by reviewers"""

    pull_request_id: str = field(metadata={"is_id_field": True})
    title: str = field(metadata={"editable": True})
    description: str = field(repr=False, metadata={"editable": True})
    source_branch: str = field(repr=False)
    target_branch: str = field(repr=False)
    author: Member
    creation_date: datetime = field(repr=False)
    repo: "Repo"
    close_date: datetime | None = field(default=None, repr=False)
    is_draft: bool = field(default=False, repr=False, metadata={"editable": True, "internal_name": "isDraft"})
    pr_status: PullRequestStatus = field(default="notSet", metadata={"editable": True, "internal_name": "status"})
    merge_status: MergeStatus = field(default="notSet", metadata={"editable": True, "internal_name": "mergeStatus"})
    reviewers: list[Reviewer] = field(default_factory=list, repr=False)  # Static(ish)

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "PullRequest":
        from ado_wrapper.resources.repo import Repo  # Circular import

        author = Member.from_request_payload(data["createdBy"])
        reviewers = [Reviewer.from_request_payload(reviewer) for reviewer in data["reviewers"]]
        repository = Repo(data["repository"]["id"], data["repository"]["name"])
        pr_status = pr_status_mapping[data["status"]] if isinstance(data.get("status"), int) else data.get("status", "notSet")
        merge_status = (
            merge_status_mapping[data["mergeStatus"]] if isinstance(data.get("mergeStatus"), int) else data.get("mergeStatus", "notSet")
        )
        return cls(str(data["pullRequestId"]), data["title"], data.get("description", ""), data["sourceRefName"],
                   data["targetRefName"], author, from_ado_date_string(data["creationDate"]), repository,
                   from_ado_date_string(data.get("closedDate")), data["isDraft"], pr_status, merge_status, reviewers)  # fmt: skip

    @classmethod
    def get_by_id(cls, ado_client: "AdoClient", pull_request_id: str) -> "PullRequest":
        return super()._get_by_url(
            ado_client,
            f"/{ado_client.ado_project_name}/_apis/git/pullrequests/{pull_request_id}?api-version=7.1",
        )

    @classmethod
    def create(
        cls, ado_client: "AdoClient", repo_id: str, pull_request_title: str,
        pull_request_description: str, from_branch_name: str, to_branch_name: str = "main", is_draft: bool = False
    ) -> "PullRequest":  # fmt: skip
        """Takes a list of reviewer ids, a branch to pull into main, and an option to start as draft"""
        # https://stackoverflow.com/questions/64655138/add-reviewers-to-azure-devops-pull-request-in-api-call   <- Why we can't allow reviewers from the get go
        # , "reviewers": [{"id": reviewer_id for reviewer_id in reviewer_ids}]
        payload = {"sourceRefName": f"refs/heads/{from_branch_name}", "targetRefName": f"refs/heads/{to_branch_name}", "title": pull_request_title,
                   "description": pull_request_description, "isDraft": is_draft}  # fmt: skip
        request = ado_client.session.post(
            f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_apis/git/repositories/{repo_id}/pullrequests?api-version=7.1",
            json=payload,
        ).json()
        if request.get("message", "").startswith("TF401398"):
            raise ValueError("The branch you are trying to create a pull request from does not exist.")
        obj = cls.from_request_payload(request)
        ado_client.state_manager.add_resource_to_state("PullRequest", obj.pull_request_id, obj.to_json())
        return obj

    @classmethod
    def delete_by_id(cls, ado_client: "AdoClient", pull_request_id: str) -> None:
        pr = cls.get_by_id(ado_client, pull_request_id)
        pr.update(ado_client, "merge_status", "abandoned")
        ado_client.state_manager.remove_resource_from_state("PullRequest", pull_request_id)

    def update(self, ado_client: "AdoClient", attribute_name: PullRequestEditableAttribute, attribute_value: Any) -> None:
        return super()._update(
            ado_client, "patch",
            f"/{ado_client.ado_project_name}/_apis/git/repositories/{self.repo.repo_id}/pullRequests/{self.pull_request_id}?api-version=7.1",
            attribute_name, attribute_value, {}  # fmt: skip
        )

    @classmethod
    def get_all(
        cls, ado_client: "AdoClient", status: PullRequestStatus = "all",
        start: datetime | None = None, end: datetime | None = None,
        limit: int = 1000,  # fmt: skip
    ) -> list["PullRequest"]:
        """`start` and `end` are for creation date, leaving them as `None` ignores those filters."""
        params = {
            "searchCriteria.status": status,
            "searchCriteria.minTime": start.isoformat() if start is not None else None,
            "searchCriteria.maxTime": end.isoformat() if end is not None else None,
            "searchCriteria.queryTimeRangeType": "created",
            "searchCriteria.includeLinks": False,  # Small optimisation
            "$top": limit,
        }
        # TODO: Limit cannot be more than 1000, paginate for more.
        extra_params_string = "".join([f"&{key}={value}" for key, value in params.items()])
        return super()._get_all(
            ado_client,
            f"/{ado_client.ado_project_name}/_apis/git/pullrequests?api-version=7.1" + extra_params_string,
        )  # pyright: ignore[reportReturnType]

    def link(self, ado_client: "AdoClient") -> str:
        return f"https://dev.azure.com//{ado_client.ado_org_name}/{ado_client.ado_project_name}/_git/{self.repo.name}/pullrequest/{self.pull_request_id}"

    # ============ End of requirement set by all state managed resources ================== #
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # =============== Start of additional methods included with class ===================== #

    def add_reviewer(self, ado_client: "AdoClient", reviewer_id: str) -> None:
        return self.add_reviewer_static(ado_client, self.repo.repo_id, self.pull_request_id, reviewer_id)

    @staticmethod
    def add_reviewer_static(ado_client: "AdoClient", repo_id: str, pull_request_id: str, reviewer_id: str) -> None:
        """Copy of the add_reviewer method, but static, i.e. if you have the repo id and pr id, you don't need to fetch them again"""
        request = ado_client.session.put(
            f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_apis/git/repositories/{repo_id}/pullRequests/{pull_request_id}/reviewers/{reviewer_id}?api-version=7.1",
            json={"vote": "0", "isRequired": "true"},
        )
        if request.status_code >= 300:
            raise UnknownError(f"Error! Cannot add reviewer to that pull request! {request.status_code}, {request.text}")

    def close(self, ado_client: "AdoClient") -> None:
        self.update(ado_client, "merge_status", "abandoned")

    def mark_as_draft(self, ado_client: "AdoClient") -> None:
        return self.update(ado_client, "is_draft", True)

    def unmark_as_draft(self, ado_client: "AdoClient") -> None:
        return self.update(ado_client, "is_draft", False)

    def get_reviewers(self, ado_client: "AdoClient") -> list[Member]:
        request = ado_client.session.get(
            f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_apis/git/repositories/{self.repo.repo_id}/pullRequests/{self.pull_request_id}/reviewers?api-version=7.1",
        ).json()
        return [Member.from_request_payload(reviewer) for reviewer in request["value"]]

    @classmethod
    def get_all_by_repo_id(cls, ado_client: "AdoClient", repo_id: str, status: PullRequestStatus = "all") -> list["PullRequest"]:
        try:
            return super()._get_all(
                ado_client,
                f"/{ado_client.ado_project_name}/_apis/git/repositories/{repo_id}/pullrequests?searchCriteria.status={status}&api-version=7.1",
            )  # pyright: ignore[reportReturnType]
        except KeyError:
            if not ado_client.suppress_warnings:
                print(f"[ADO_WRAPPER] Repo with id `{repo_id}` was disabled, or you had no access.")
            return []

    @classmethod
    def get_all_by_author(cls, ado_client: "AdoClient", author_email: str, status: PullRequestStatus = "all") -> list["PullRequest"]:
        return [pr for pr in cls.get_all(ado_client, status) if pr.author.email == author_email]

    @classmethod
    def get_my_pull_requests(cls, ado_client: "AdoClient") -> list["PullRequest"]:
        PAYLOAD = build_hierarchy_payload(ado_client, "code-web.prs-list-data-provider", route_id="code-web.my-pullrequests-me-page-route")
        PAYLOAD |= {"queryIds": ["AssignedToMyTeams"]}
        request = ado_client.session.post(
            f"https://dev.azure.com/{ado_client.ado_org_name}/_apis/Contribution/HierarchyQuery?api-version=7.0-preview",
            json=PAYLOAD,
        ).json()
        pr_payloads = request["dataProviders"]["ms.vss-code-web.prs-list-data-provider"]["pullRequests"].values()
        return [cls.from_request_payload(pr) for pr in pr_payloads]

    @staticmethod
    def set_my_pull_requests_included_teams(
        ado_client: "AdoClient", status: PullRequestStatus = "active", draft_state: DraftState | None = None,
        created_by: list["Group"] | None = None, assigned_to: list["Group"] | None = None, target_branch: str | None = None,
        created_in_last_x_days: int | None = None, updated_in_last_x_days: int | None = None,
        completed_in_last_x_days: int | None = None,  # fmt: skip
    ) -> None:
        """Sets the `Assigned to my teams` section of ADO, also used by `PullRequest.get_my_pull_requests()`
        WARNING: created_by, assigned_to can be left as None, and will keep previous settings, but
        not including (or setting to None) any of
        `target_branch`, `created_in_last_x_days`, `updated_in_last_x_days` or `completed_in_last_x_days`
        will remove any filtering based on this argument"""
        # ==========================================================================================================================================
        # GET REQUEST VERIFICATION TOKEN
        request = ado_client.session.get(f"https://dev.azure.com/{ado_client.ado_org_name}/_pulls")
        request_verification_token = request.text.split("__RequestVerificationToken")[1].removeprefix('" value="').split('"')[0]
        # ==========================================================================================================================================
        # Configure Payload
        if status in ["completed", "abandoned"] and draft_state is not None:
            raise ConfigurationError("Error, cannot set status to completed/abandoned and also set draft_state!")
        if status == "active" and completed_in_last_x_days is not None:
            raise ConfigurationError("Error, cannot set status to active and also set completed_in_x_days!")
        status_converted = {value: key for key, value in pr_status_mapping.items()}[status]
        combined_payloads = [
            {"groupByVote": False, "includeDuplicates": True, "id": "CreatedByMe", "readonly": True, "status": 1, "title": "Created by me", "authorIds": [ado_client.pat_author.origin_id]},  # fmt: skip
            {"groupByVote": False, "includeDuplicates": True, "id": "AssignedToMe", "readonly": True, "reviewerIds": [ado_client.pat_author.origin_id], "status": 1, "title": "Assigned to me"},  # fmt: skip
        ]
        payload = {"groupByVote": False, "includeDuplicates": True, "id": "AssignedToMyTeams", "myTeamsAsReviewer": True, "status": status_converted, "title": "Assigned to my teams"}  # fmt: skip
        payload["authorIds"] = [x.origin_id for x in (created_by or [])]  # Always add our own author
        if assigned_to is not None:
            payload["reviewerIds"] = [x.origin_id for x in assigned_to]
        if target_branch is not None:
            payload["targetRefName"] = f"refs/heads/{target_branch}"
        if created_in_last_x_days is not None:
            payload["maxDaysSinceCreated"] = created_in_last_x_days
        if updated_in_last_x_days is not None:
            payload["maxDaysSinceLastUpdated"] = updated_in_last_x_days
        if completed_in_last_x_days is not None:
            payload["maxDaysSinceClosed"] = completed_in_last_x_days
        if draft_state in ["Exclude drafts", "Only include drafts"]:  # Exclude = False, Include = Not present, Only Include = False
            payload["draftState"] = draft_state == "Only include drafts"
        combined_payloads.append(payload)
        # ==========================================================================================================================================
        payload_with_token = {"preferences": json.dumps({"pullRequestListCustomCriteria": json.dumps(combined_payloads)}),  # Double encoding... gross
                              "__RequestVerificationToken": request_verification_token}  # fmt: skip
        request = ado_client.session.post(
            f"https://dev.azure.com/{ado_client.ado_org_name}/_api/_versioncontrol/updateUserPreferences?__v=5",
            data=payload_with_token,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if request.status_code != 200:
            raise UnknownError("Error, unknown error when trying to set included teams")

    def get_comment_threads(self, ado_client: "AdoClient", ignore_system_messages: bool = True) -> list["PullRequestCommentThread"]:
        comments = PullRequestCommentThread.get_all(ado_client, self.repo.repo_id, self.pull_request_id)
        if ignore_system_messages:
            comments = [comment for comment in comments if comment.comments[0].comment_type != "system"]
        return comments

    def get_comments(self, ado_client: "AdoClient", ignore_system_messages: bool = True) -> list["PullRequestComment"]:
        """Gets a list of comments on a pull request, optionally ignoring system messages."""
        return [comment for thread in self.get_comment_threads(ado_client, ignore_system_messages) for comment in thread.comments]

    def post_comment(self, ado_client: "AdoClient", content: str) -> "PullRequestComment":
        request = ado_client.session.post(
            f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_apis/git/repositories/{self.repo.repo_id}/pullRequests/{self.pull_request_id}/threads?api-version=7.1",
            json={"comments": [{"commentType": 1, "content": content}], "status": "1"},
        ).json()
        return PullRequestComment.from_request_payload(request["comments"][0], self.repo.repo_id, self.pull_request_id)


@dataclass
class PullRequestCommentThread(StateManagedResource):
    """https://learn.microsoft.com/en-us/rest/api/azure/devops/git/pull-request-thread-comments/list?view=azure-devops-rest-7.1
    Represents a chain of comments on a pull request, with the status e.g. Resolved, Active, etc."""

    thread_id: str
    status: str | None
    comments: list["PullRequestComment"]
    repo_id: str | None = field(repr=False)
    parent_pull_request_id: str | None = field(repr=False)

    @classmethod
    def from_request_payload(cls, data: dict[str, Any], repo_id: str, pull_request_id: str) -> "PullRequestCommentThread":  # type: ignore[override]
        comments = [PullRequestComment.from_request_payload(comment, repo_id, pull_request_id) for comment in data["comments"]]
        return cls(data["id"], data.get("status"), comments, repo_id, pull_request_id)

    @classmethod
    def get_by_id(cls, ado_client: "AdoClient", repo_id: str, pull_request_id: str, thread_id: str) -> "PullRequestCommentThread":
        request = ado_client.session.get(
            f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_apis/git/repositories/{repo_id}/pullRequests/{pull_request_id}/threads/{thread_id}?api-version=7.1",
        ).json()
        return cls.from_request_payload(request, repo_id, pull_request_id)  # Can't use _get_by_url because of the additional params

    @classmethod
    def create(cls, ado_client: "AdoClient", repo_id: str, pull_request_id: str, content: str) -> "PullRequestCommentThread":
        request = ado_client.session.post(
            f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_apis/git/repositories/{repo_id}/pullRequests/{pull_request_id}/threads?api-version=7.1",
            json={"comments": [{"commentType": 1, "content": content}]},
        ).json()
        pull_request_comment_thread = cls.from_request_payload(request, repo_id, pull_request_id)
        ado_client.state_manager.add_resource_to_state("PullRequestCommentThread", pull_request_comment_thread.thread_id, pull_request_comment_thread.to_json())  # fmt: skip
        return pull_request_comment_thread

    def delete_by_id(self, ado_client: "AdoClient", repo_id: str, pull_request_id: str, thread_id: str) -> None:
        return super()._delete_by_id(
            ado_client,
            f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_apis/git/repositories/{repo_id}/pullRequests/{pull_request_id}/threads/{thread_id}?api-version=7.1",
            thread_id,
        )

    @classmethod
    def get_all(cls, ado_client: "AdoClient", repo_id: str, pull_request_id: str) -> list["PullRequestCommentThread"]:
        request = ado_client.session.get(
            f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_apis/git/repositories/{repo_id}/pullRequests/{pull_request_id}/threads?api-version=7.1",
        ).json()["value"]
        return [cls.from_request_payload(x, repo_id, pull_request_id) for x in request]  # pyright: ignore[reportReturnType]


@dataclass
class PullRequestComment:
    """Comments' content will be None if they've been deleted, or if they're system comments."""

    comment_id: str
    parent_comment_id: str = field(repr=False)
    content: str | None
    author: Member
    creation_date: datetime = field(repr=False)
    comment_type: CommentType
    is_deleted: bool = field(repr=False)
    liked_users: list[Member] = field(repr=False)

    repo_id: str = field(repr=False)
    parent_pull_request_id: str = field(repr=False)

    @classmethod
    def from_request_payload(cls, data: dict[str, Any], repo_id: str, pull_request_id: str) -> "PullRequestComment":
        """This is used by posting new comments, they return just a comment, not a thread."""
        author = Member.from_request_payload(data["author"])
        liked_users = [Member.from_request_payload(user) for user in data.get("usersLiked", [])]
        return cls(
            str(data["id"]), str(data["parentCommentId"]), data.get("content"), author,
            data.get("commentType", "regular"), from_ado_date_string(data["publishedDate"]),
            data.get("isDeleted", False), liked_users,
            repo_id, pull_request_id,
        )  # fmt: skip

    to_json = StateManagedResource.to_json

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "PullRequestComment":
        return PullRequestComment(**convert_from_json(data))

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

import json

from ado_wrapper.state_managed_abc import StateManagedResource
from ado_wrapper.resources.users import Member
from ado_wrapper.utils import from_ado_date_string

if TYPE_CHECKING:
    from ado_wrapper.client import AdoClient


@dataclass
class AnnotatedTag(StateManagedResource):
    """https://learn.microsoft.com/en-us/rest/api/azure/devops/git/annotated-tags?view=azure-devops-rest-7.1"""

    object_id: str = field(metadata={"is_id_field": True})
    name: str
    message: str
    tagged_by: Member
    created_at: datetime

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "AnnotatedTag":
        member = Member(data["taggedBy"]["name"], data["taggedBy"]["email"], "UNKNOWN")
        created_at = datetime.fromisoformat(data["taggedBy"]["date"])
        return cls(data["objectId"], data["name"], data["message"], member, created_at)

    @classmethod
    def get_by_id(cls, ado_client: AdoClient, repo_id: str, branch_id: str) -> "AnnotatedTag":  # type: ignore[override]
        return super().get_by_url(
            ado_client,
            f"/{ado_client.ado_project}/_apis/git/repositories/{repo_id}/annotatedtags/{branch_id}?api-version=7.1-preview.1",
        )  # type: ignore[return-value]

    @classmethod
    def create(cls, ado_client: AdoClient, repo_id: str, name: str, message: str, object_id: str) -> "AnnotatedTag":  # type: ignore[override]
        return super().create(
            ado_client,
            f"/{ado_client.ado_project}/_apis/git/repositories/{repo_id}/annotatedTags?api-version=7.1-preview.1",
            payload={"name": name, "message": message, "taggedObject": {"objectId": object_id}},
        )  # type: ignore[return-value]

    @classmethod
    def delete_by_id(cls, ado_client: AdoClient, object_id: str) -> None:  # type: ignore[override]
        ado_client.state_manager.remove_resource_from_state(cls.__name__, object_id)  # type: ignore[arg-type]
        raise NotImplementedError("You can't delete a tag!")

    # # ============ End of requirement set by all state managed resources ================== #
    # # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # # =============== Start of additional methods included with class ===================== #

    @classmethod
    def get_all_by_repo(cls, ado_client: AdoClient, repo_name: str) -> list["AnnotatedTag"]:
        """Unofficial API."""
        request = ado_client.session.post(
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_git/{repo_name}/tags/?api-version=7.1-preview.1"
        )
        assert request.status_code == 200
        second_half = request.text.split("ms.vss-code-web.git-tags-data-provider")[1].removeprefix('":')
        trimmed_second_half = second_half.split("ms.vss-code-web.navigation-data-provider")[0].removesuffix(',"')
        json_data = json.loads(trimmed_second_half)["tags"]
        # ===
        return [
            cls(x["objectId"], x["name"], x["comment"],
                Member(x["tagger"]["name"], x["tagger"]["email"], "UNKNOWN"),
                from_ado_date_string(x["tagger"]["date"]),
            )
            for x in json_data if "comment" in x  # fmt: skip
        ]

    @classmethod
    def get_by_name(cls, ado_client: AdoClient, repo_id: str, tag_name: str) -> "AnnotatedTag | None":
        for tag in cls.get_all_by_repo(ado_client, repo_id):
            if tag.name == tag_name:
                return tag
        raise ValueError(f"Tag {tag_name} not found")

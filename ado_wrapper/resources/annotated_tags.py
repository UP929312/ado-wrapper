import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

from ado_wrapper.errors import UnknownError
from ado_wrapper.resources.users import Member
from ado_wrapper.state_managed_abc import StateManagedResource
from ado_wrapper.utils import from_ado_date_string

if TYPE_CHECKING:
    from ado_wrapper.client import AdoClient


@dataclass
class AnnotatedTag(StateManagedResource):
    """https://learn.microsoft.com/en-us/rest/api/azure/devops/git/annotated-tags?view=azure-devops-rest-7.1"""

    object_id: str = field(metadata={"is_id_field": True})
    repo_id: str
    name: str
    message: str
    tagged_by: Member
    created_at: datetime

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "AnnotatedTag":
        repo_id = data["url"].split("/_apis/git/repositories/")[1].split("/annotatedtags/")[0]
        member = Member(data["taggedBy"]["name"], data["taggedBy"]["email"], "UNKNOWN")
        created_at = datetime.fromisoformat(data["taggedBy"]["date"])
        return cls(data["objectId"], repo_id, data["name"], data["message"], member, created_at)

    @classmethod
    def get_by_id(cls, ado_client: "AdoClient", repo_id: str, object_id: str) -> "AnnotatedTag":
        return super()._get_by_url(
            ado_client,
            f"/{ado_client.ado_project_name}/_apis/git/repositories/{repo_id}/annotatedtags/{object_id}?api-version=7.1-preview.1",
        )

    @classmethod
    def create(cls, ado_client: "AdoClient", repo_id: str, name: str, message: str, object_id: str) -> "AnnotatedTag":
        return super()._create(
            ado_client,
            f"/{ado_client.ado_project_name}/_apis/git/repositories/{repo_id}/annotatedTags?api-version=7.1-preview.1",
            payload={"name": name, "message": message, "taggedObject": {"objectId": object_id}},
        )

    @classmethod
    def delete_by_id(cls, ado_client: "AdoClient", object_id: str, repo_id: str) -> None:
        tag = cls.get_by_id(ado_client, object_id, repo_id)
        cls._special_delete(ado_client, tag.repo_id, tag.object_id, tag.name)

    @classmethod
    def _special_delete(cls, ado_client: "AdoClient", repo_id: str, object_id: str, tag_name: str) -> None:
        """This is a messy workaround because the official API does not support deleting tags.
        Additionally, to delete we need a bunch of other stuff, can't just delete by object_id."""
        PAYLOAD = {
            "name": f"refs/tags/{tag_name}",
            "oldObjectId": object_id,
            "newObjectId": "0000000000000000000000000000000000000000",
        }  # fmt: skip
        ado_client.session.post(
            f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_apis/git/repositories/{repo_id}/refs?api-version=7.1-preview.1",
            json=[PAYLOAD],
        )
        ado_client.state_manager.remove_resource_from_state("AnnotatedTag", object_id)

    # # ============ End of requirement set by all state managed resources ================== #
    # # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # # =============== Start of additional methods included with class ===================== #

    @classmethod
    def get_all_by_repo(cls, ado_client: "AdoClient", repo_id: str) -> list["AnnotatedTag"]:
        """WARNING: Unofficial API."""
        request = ado_client.session.post(
            f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_git/{repo_id}/tags/?api-version=7.1-preview.1"
        )
        if request.status_code != 200:
            raise UnknownError(f"Error! Unknown error when trying to get all tags for repo! {request.status_code}, {request.text}")
        second_half = request.text.split('ms.vss-code-web.git-tags-data-provider":')[1]
        trimmed_second_half = second_half.split(',"ms.vss-code-web.navigation-data-provider')[0]
        json_data = json.loads(trimmed_second_half)["tags"]
        # ===
        return [
            cls(x["objectId"], repo_id, x["name"], x["comment"],
                Member(x["tagger"]["name"], x["tagger"]["email"], "UNKNOWN"),
                from_ado_date_string(x["tagger"]["date"]))
            for x in json_data if "comment" in x  # fmt: skip
        ]

    @classmethod
    def get_by_name(cls, ado_client: "AdoClient", repo_id: str, tag_name: str) -> "AnnotatedTag | None":
        # return super()._get_by_abstract_filter(ado_client, lambda tag: tag.name == tag_name)  # Can't use get all, since we can't use get_all()
        for tag in cls.get_all_by_repo(ado_client, repo_id):
            if tag.name == tag_name:
                return tag
        raise ValueError(f"Tag {tag_name} not found")

    def delete(self, ado_client: "AdoClient") -> None:
        self._special_delete(ado_client, self.repo_id, self.object_id, self.name)

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal

from ado_wrapper.resources.users import Member
from ado_wrapper.state_managed_abc import StateManagedResource
from ado_wrapper.utils import from_ado_date_string

if TYPE_CHECKING:
    from ado_wrapper.client import AdoClient

EnvironmentEditableAttribute = Literal["name", "description"]


# ====================================================================


@dataclass
class Environment(StateManagedResource):
    """https://learn.microsoft.com/en-us/rest/api/azure/devops/distributedtask/environments?view=azure-devops-rest-7.1"""

    environment_id: str = field(metadata={"is_id_field": True})
    name: str = field(metadata={"editable": True})
    description: str = field(metadata={"editable": True})
    resources: list[dict[str, Any]]  # This isn't used anywhere by ourselves, feel free to implement better logic.
    created_by: Member
    created_on: datetime
    modified_by: Member | None
    modified_on: datetime | None

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "Environment":
        return cls(
            str(data["id"]),
            data["name"],
            data["description"],
            data.get("resources", []),
            Member.from_request_payload(data["createdBy"]),
            from_ado_date_string(data["createdOn"]),
            Member.from_request_payload(data["modifiedOn"]) if data.get("modifiedBy") else None,
            from_ado_date_string(data.get("modifiedOn")),
        )

    @classmethod
    def get_by_id(cls, ado_client: "AdoClient", environment_id: str) -> "Environment":
        return super()._get_by_url(
            ado_client,
            f"/{ado_client.ado_project_name}/_apis/distributedtask/environments/{environment_id}?api-version=7.1-preview.1",
        )

    @classmethod
    def create(cls, ado_client: "AdoClient", name: str, description: str) -> "Environment":
        return super()._create(
            ado_client,
            f"/{ado_client.ado_project_name}/_apis/distributedtask/environments?api-version=7.1-preview.1",
            {"name": name, "description": description},
        )

    def update(self, ado_client: "AdoClient", attribute_name: EnvironmentEditableAttribute, attribute_value: Any) -> None:
        return super()._update(
            ado_client, "patch",
            f"/{ado_client.ado_project_name}/_apis/distributedtask/environments/{self.environment_id}?api-version=7.1-preview.1",
            attribute_name, attribute_value, {},  # fmt: skip
        )

    @classmethod
    def delete_by_id(cls, ado_client: "AdoClient", environment_id: str) -> None:
        return super()._delete_by_id(
            ado_client,
            f"/{ado_client.ado_project_name}/_apis/distributedtask/environments/{environment_id}?api-version=7.1-preview.1",
            environment_id,
        )

    @classmethod
    def get_all(cls, ado_client: "AdoClient") -> list["Environment"]:
        return super()._get_all(
            ado_client,
            f"/{ado_client.ado_project_name}/_apis/distributedtask/environments?api-version=7.1-preview.1&$top=10000",
        )  # pyright: ignore[reportReturnType]

    def link(self, ado_client: "AdoClient") -> str:
        return f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_environments/{self.environment_id}"

    # # ============ End of requirement set by all state managed resources ================== #
    # # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # # =============== Start of additional methods included with class ===================== #

    @classmethod
    def get_by_name(cls, ado_client: "AdoClient", name: str) -> "Environment | None":
        return cls._get_by_abstract_filter(ado_client, lambda x: x.name == name)

    # =============== Pipeline Permissions ===================== #

    def get_pipeline_permissions(self, ado_client: "AdoClient") -> list["PipelineAuthorisation"]:
        return PipelineAuthorisation.get_all_for_environment(ado_client, self.environment_id)

    def add_pipeline_permission(self, ado_client: "AdoClient", pipeline_id: str) -> "PipelineAuthorisation":
        return PipelineAuthorisation.create(ado_client, self.environment_id, pipeline_id)

    def remove_pipeline_permissions(self, ado_client: "AdoClient", pipeline_id: str) -> None:
        PipelineAuthorisation.delete_by_id(ado_client, self.environment_id, pipeline_id)


@dataclass
class PipelineAuthorisation:
    """Stores the authorisation of a pipeline to an environment."""

    pipeline_id: str
    environment_id: str
    authorized: bool
    authorized_by: Member
    authorized_on: datetime

    @classmethod
    def from_request_payload(cls, data: dict[str, Any], environment_id: str) -> "PipelineAuthorisation":
        return cls(
            str(data["id"]),
            environment_id,
            data["authorized"],
            Member.from_request_payload(data["authorizedBy"]),
            from_ado_date_string(data["authorizedOn"]),
        )

    @classmethod
    def get_all_for_environment(cls, ado_client: "AdoClient", environment_id: str) -> list["PipelineAuthorisation"]:
        request = ado_client.session.get(
            f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_apis/pipelines/pipelinePermissions/environment/{environment_id}",
        ).json()
        # Can't use super()._get_by_id becauwe we need to pass in in the environment_id
        return [cls.from_request_payload(x, request["resource"]["id"]) for x in request["pipelines"]]

    @classmethod
    def create(cls, ado_client: "AdoClient", environment_id: str, pipeline_id: str, authorized: bool = True) -> "PipelineAuthorisation":
        all_existing = cls.get_all_for_environment(ado_client, environment_id)
        payload: dict[str, Any] = {"pipelines": [{"id": x.pipeline_id, "authorized": True} for x in all_existing]}
        payload["pipelines"] = [x for x in payload["pipelines"] if x["id"] != pipeline_id]  # Remove existing entry if it exists
        payload["pipelines"].append({"id": pipeline_id, "authorized": authorized})
        payload |= {"resource": {"type": "environment", "id": environment_id}}

        request = ado_client.session.patch(
            f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_apis/pipelines/pipelinePermissions/environment/{environment_id}?api-version=7.1-preview.1",
            json=payload,
        )
        if request.status_code == 404:
            raise ValueError(f"Pipeline {pipeline_id} not found.")
        if not request.json()["pipelines"]:
            raise ValueError(f"Pipeline {pipeline_id} not found.")
        created_pipeline_dict = max(request.json()["pipelines"], key=lambda x: x["authorizedOn"])
        return cls.from_request_payload(created_pipeline_dict, environment_id)

    def update(self, ado_client: "AdoClient", authorized: bool) -> None:
        self.delete_by_id(ado_client, self.environment_id, self.pipeline_id)
        new = self.create(ado_client, self.environment_id, self.pipeline_id, authorized)
        self.__dict__.update(new.__dict__)

    @classmethod
    def delete_by_id(cls, ado_client: "AdoClient", environment_id: str, pipeline_authorisation_id: str) -> None:
        # TODO: What is this again?
        try:
            cls.create(ado_client, environment_id, pipeline_authorisation_id, False)
        except ValueError:
            pass

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal, TYPE_CHECKING

from ado_wrapper.state_managed_abc import StateManagedResource
from ado_wrapper.resources.users import Member
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
    def from_request_payload(cls, data: dict[str, Any]) -> Environment:
        return cls(
            str(data["id"]), data["name"], data["description"], data.get("resources", []),
            Member.from_request_payload(data["createdBy"]),
            from_ado_date_string(data["createdOn"]),
            Member.from_request_payload(data["modifiedOn"]) if data.get("modifiedBy") else None,  # fmt: skip
            from_ado_date_string(data.get("modifiedOn")), # fmt: skip
        )

    @classmethod
    def get_by_id(cls, ado_client: AdoClient, environment_id: str) -> Environment:
        return super().get_by_url(
            ado_client,
            f"/{ado_client.ado_project}/_apis/distributedtask/environments/{environment_id}?api-version=7.1-preview.1",
        )  # type: ignore[return-value]

    @classmethod
    def create(cls, ado_client: AdoClient, name: str, description: str) -> Environment:  # type: ignore[override]
        return super().create(
            ado_client,
            f"/{ado_client.ado_project}/_apis/distributedtask/environments?api-version=7.1-preview.1",
            {"name": name, "description": description},
        )  # type: ignore[return-value]

    def update(self, ado_client: AdoClient, attribute_name: EnvironmentEditableAttribute, attribute_value: Any) -> None:  # type: ignore[override]
        return super().update(
            ado_client, "patch",
            f"/{ado_client.ado_project}/_apis/distributedtask/environments/{self.environment_id}?api-version=7.1-preview.1",
            attribute_name, attribute_value, {},  # fmt: skip
        )

    @classmethod
    def delete_by_id(cls, ado_client: AdoClient, environment_id: str) -> None:  # type: ignore[override]
        return super().delete_by_id(
            ado_client,
            f"/{ado_client.ado_project}/_apis/distributedtask/environments/{environment_id}?api-version=7.1-preview.1",
            environment_id,
        )

    @classmethod
    def get_all(cls, ado_client: AdoClient) -> list[Environment]:  # type: ignore[override]
        return super().get_all(
            ado_client,
            f"/{ado_client.ado_project}/_apis/distributedtask/environments?api-version=7.1-preview.1&$top=10000"
        )  # type: ignore[return-value]

    # # ============ End of requirement set by all state managed resources ================== #
    # # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # # =============== Start of additional methods included with class ===================== #

    @classmethod
    def get_by_name(cls, ado_client: AdoClient, name: str) -> Environment:
        return cls.get_by_abstract_filter(ado_client, lambda x: x.name == name)  # type: ignore[return-value, attr-defined]

    # def update_pipeline_perms(self, ado_client: AdoClient, pipeline_id: str | Literal["all"]) -> dict[str, Any]:
    #     """Updates the permissions of a service endpoint in a pipeline.
    #     UNTESTED
    #     https://learn.microsoft.com/en-us/rest/api/azure/devops/approvalsandchecks/pipeline-permissions/update-pipeline-permisions-for-resources?view=azure-devops-rest-7.1
    #     """
    #     PAYLOAD = {
    #         "resource": {"id": self.service_endpoint_id, "type": "endpoint", "name": ""},
    #         "pipelines": [] if pipeline_id == "all" else [{"id": pipeline_id}],
    #         "allPipelines": {"authorized": True, "authorizedBy": "null", "authorizedOn": "null"},
    #     }
    #     return ado_client.session.patch(  # type: ignore[no-any-return]
    #         f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/pipelines/pipelinePermissions/endpoint/{self.service_endpoint_id}?api-version=7.1",
    #         json=PAYLOAD,
    #     ).json()

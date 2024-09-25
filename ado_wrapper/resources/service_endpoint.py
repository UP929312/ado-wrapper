from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal

from ado_wrapper.errors import ConfigurationError
from ado_wrapper.resources.users import Member
from ado_wrapper.state_managed_abc import StateManagedResource
from ado_wrapper.utils import requires_initialisation

if TYPE_CHECKING:
    from ado_wrapper.client import AdoClient

ServiceEndpointEditableAttribute = Literal["name"]


# ====================================================================


@dataclass
class ServiceEndpoint(StateManagedResource):
    """https://learn.microsoft.com/en-us/rest/api/azure/devops/serviceendpoint/endpoints?view=azure-devops-rest-7.1"""

    service_endpoint_id: str = field(metadata={"is_id_field": True})
    name: str = field(metadata={"editable": True})
    type: str  # = field(metadata={"editable": True})
    url: str
    created_by: Member
    description: str  # = field(metadata={"editable": True})
    authorization: dict[str, Any]
    is_shared: bool
    is_outdated: bool
    is_ready: bool
    owner: str
    service_endpoint_project_references: list[dict[str, Any]]
    # _raw_data: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "ServiceEndpoint":
        return cls(
            data["id"], data["name"], data["type"], data["url"],
            Member.from_request_payload(data["createdBy"]),
            data.get("description", ""), data["authorization"], data["isShared"],
            data["isOutdated"], data["isReady"], data["owner"],
            data["serviceEndpointProjectReferences"],  # fmt: skip
        )

    @classmethod
    def get_by_id(cls, ado_client: "AdoClient", repo_id: str) -> "ServiceEndpoint":
        return super()._get_by_url(
            ado_client,
            f"/{ado_client.ado_project_name}/_apis/serviceendpoint/endpoints/{repo_id}",
        )

    @classmethod
    def create(cls, ado_client: "AdoClient", name: str, service_endpoint_type: str, url: str,
               username: str = "", password: str = "", access_token: str = "") -> "ServiceEndpoint":  # fmt: skip
        """Creates a service endpoint, pass in either username and password or access_token."""
        if (username or password) and access_token:  # fmt: skip
            raise ConfigurationError("Either `username and password` or `access_token` must be passed in, not both!")
        requires_initialisation(ado_client)
        payload = {
            "name": name, "type": service_endpoint_type, "url": url, "isShared": True, "isReady": True,
            "serviceEndpointProjectReferences": [{"projectReference": {"id": ado_client.ado_project_id}, "name": name}],  # fmt: skip
        }
        if username and password:
            payload["authorization"] = {"scheme": "UsernamePassword", "parameters": {"Username": username, "Password": password}}
        elif access_token:
            payload["authorization"] = {"parameters": {"AccessToken": access_token}, "scheme": "Token"}
        return super()._create(
            ado_client, "/_apis/serviceendpoint/endpoints?api-version=7.1", payload,  # fmt: skip
        )

    def update(self, ado_client: "AdoClient", attribute_name: ServiceEndpointEditableAttribute, attribute_value: Any) -> None:
        raise NotImplementedError
        # TODO: Implemenent
        # self._raw_data[attribute_name] = attribute_value
        # return super().update(
        #     ado_client, "put",
        #     f"_apis/serviceendpoint/endpoints/{self.service_endpoint_id}?api-version=7.1",
        #     attribute_name, attribute_value, self._raw_data,  # fmt: skip
        # )

    @classmethod
    def delete_by_id(cls, ado_client: "AdoClient", service_endpoint_id: str) -> None:
        requires_initialisation(ado_client)
        return super()._delete_by_id(
            ado_client,
            f"/_apis/serviceendpoint/endpoints/{service_endpoint_id}?projectIds={ado_client.ado_project_id}&api-version=7.1",
            service_endpoint_id,
        )

    @classmethod
    def get_all(cls, ado_client: "AdoClient") -> list["ServiceEndpoint"]:
        return super()._get_all(
            ado_client,
            f"/{ado_client.ado_project_name}/_apis/serviceendpoint/endpoints?api-version=7.1",
        )  # pyright: ignore[reportReturnType]

    # ============ End of requirement set by all state managed resources ================== #
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # =============== Start of additional methods included with class ===================== #

    @classmethod
    def get_by_name(cls, ado_client: "AdoClient", name: str) -> "ServiceEndpoint":
        return super()._get_by_url(
            ado_client,
            f"/{ado_client.ado_project_name}/_apis/serviceendpoint/endpoints?endpointNames={name}&api-version=7.1",
        )

    def update_pipeline_perms(self, ado_client: "AdoClient", pipeline_id: str | Literal["all"]) -> dict[str, Any]:
        """Updates the permissions of a service endpoint in a pipeline.
        UNTESTED
        https://learn.microsoft.com/en-us/rest/api/azure/devops/approvalsandchecks/pipeline-permissions/update-pipeline-permisions-for-resources?view=azure-devops-rest-7.1
        """
        PAYLOAD = {
            "resource": {"id": self.service_endpoint_id, "type": "endpoint", "name": ""},
            "pipelines": [] if pipeline_id == "all" else [{"id": pipeline_id}],
            "allPipelines": {"authorized": True, "authorizedBy": "null", "authorizedOn": "null"},
        }
        pipeline_perms: dict[str, Any] = ado_client.session.patch(
            f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_apis/pipelines/pipelinePermissions/endpoint/{self.service_endpoint_id}?api-version=7.1",
            json=PAYLOAD,
        ).json()
        return pipeline_perms

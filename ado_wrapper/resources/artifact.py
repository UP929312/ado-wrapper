from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from ado_wrapper.state_managed_abc import StateManagedResource
from ado_wrapper.utils import binary_data_to_file_dictionary

if TYPE_CHECKING:
    from ado_wrapper.client import AdoClient

# ========================================================================================================


@dataclass
class BuildArtifact(StateManagedResource):
    """https://learn.microsoft.com/en-us/rest/api/azure/devops/build/artifacts?view=azure-devops-rest-7.1"""

    artifact_id: str = field(metadata={"is_id_field": True})
    name: str
    source_job_id: str
    artifact_local_path: str | None
    artifact_size_bytes: int | None
    download_path: str
    build_id: str

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "BuildArtifact":
        # print(f"{data=}")
        artifact_size: str | None = data["resource"].get("properties", {"artifactsize": None})["artifactsize"]
        build_id = data["resource"]["url"].split("build/builds/")[1].split("/artifacts?artifactName=")[0]
        return cls(
            str(data["id"]), data["name"], data["source"],
            data["resource"].get("properties", {}).get("localpath"),
            int(artifact_size) if isinstance(artifact_size, str) else None,
            data["resource"]["downloadUrl"], build_id
        )  # fmt: skip

    @classmethod
    def get_by_name(cls, ado_client: "AdoClient", build_id: str, artifact_name: str) -> "BuildArtifact":
        """https://learn.microsoft.com/en-us/rest/api/azure/devops/build/artifacts/get-artifact"""
        return super()._get_by_url(
            ado_client,
            f"/{ado_client.ado_project_name}/_apis/build/builds/{build_id}/artifacts?artifactName={artifact_name}&api-version=7.1",
        )

    @classmethod
    def download_artifact(cls, ado_client: "AdoClient", download_url: str) -> dict[str, str]:
        request = ado_client.session.get(download_url)
        files = binary_data_to_file_dictionary(request.content, None, ado_client.suppress_warnings)
        return files

    def link(self, ado_client: "AdoClient") -> str:
        return f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_build/results?buildId={self.build_id}&view=artifacts&pathAsName=false&type=publishedArtifacts"  # fmt: skip

    # ===================================================================================================

    @classmethod
    def create(cls, ado_client: "AdoClient", build_id: str, artifact_name: str) -> "BuildArtifact":
        raise NotImplementedError

    #     """https://learn.microsoft.com/en-us/rest/api/azure/devops/build/artifacts/create"""
    #     """https://stackoverflow.com/questions/74193228/artifacts-create-azure-devops-rest-api"""
    #     artifact_metadata = {
    #         "name": artifact_name,
    #         "resource": {
    #             "type": "container",
    #             "data": f"#/{artifact_name}",
    #         }
    #     }
    #     request = ado_client.session.post(
    #         f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_apis/build/builds/{build_id}/artifacts?api-version=7.1-preview.5",
    #         json=artifact_metadata,
    #     ).json()
    #     container_id = request.get('resource', {}).get('properties', {}).get('containerId')
    #     print(f"{container_id}")
    #     return BuildArtifact("", "", "", "", None, "")
    #     # container_id = request.get('resource', {}).get('data', '').split('/')[-1]
    #     # print(request)
    #     # print(f"{request=}")
    #     # file_data = b"This is a little test"  # io.BytesIO()
    #     # return # type: ignore
    #     # headers={'Content-Type': 'application/octet-stream'},
    #     # print(f"{container_id=}")
    #     # container_id = request["resource"]["data"]
    #     # cls.upload_file_to_artifact(ado_client, container_id, artifact_name, file_data)
    #     # return cls.from_request_payload(request)

    # @classmethod
    # def upload_file_to_artifact(cls, ado_client: "AdoClient", artifact_name: str, file_name: str, file_content: bytes) -> None:
    #     print(f"https://dev.azure.com/{ado_client.ado_org_name}/_apis/resources/Containers/{artifact_name}?itemPath={artifact_name}/{file_name}&api-version=6.0-preview.4",)
    #     request = ado_client.session.put(
    #         f"https://dev.azure.com/{ado_client.ado_org_name}/_apis/resources/Containers/{artifact_name}?itemPath={artifact_name}/{file_name}&api-version=6.0-preview.4",
    #         data=file_content,
    #         headers={'Content-Type': 'application/octet-stream'}
    #     )
    #     # print(f"Second: text: {request.text}")
    #     print(f"Second: status: {request.status_code}")
    #     # print(f"Second: json: {request.json()}")

    @classmethod
    def get_all_by_build_id(cls, ado_client: "AdoClient", build_id: str) -> list["BuildArtifact"]:
        """https://learn.microsoft.com/en-us/rest/api/azure/devops/build/artifacts/list"""
        return super()._get_all(
            ado_client,
            f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_apis/build/builds/{build_id}/artifacts?api-version=7.1-preview.5",
        )  # pyright: ignore[reportReturnType]


Artifact = BuildArtifact
# ========================================================================================================

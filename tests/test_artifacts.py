import pytest

# from ado_wrapper.resources.builds import Build, BuildDefinition
from ado_wrapper.resources.artifact import BuildArtifact

# from ado_wrapper.resources.commits import Commit
# from tests.setup_client import RepoContextManager, email, existing_agent_pool_id, setup_client  # fmt: skip
from tests.setup_client import setup_client

BUILD_YAML_FILE = """---
trigger:
  - main

pool:
  vmImage: ubuntu-latest

steps:
  - script: echo Hello, world!
    displayName: 'Run a one-line script'"""


class TestBuildArtifact:
    def setup_method(self) -> None:
        self.ado_client = setup_client()

    @pytest.mark.from_request_payload
    def test_from_request_payload(self) -> None:
        artifact = BuildArtifact.from_request_payload(
            {
                "id": "123456789",
                "name": "test_artifact_name",
                "source": "abcdefghi",  # The artifact source, which will be the ID of the job that produced this artifact. If an artifact is associated with multiple sources, this points to the first source.
                "resource": {
                    "properties": {"localpath": "/home/vsts/work/1/s/abcde", "artifactsize": "12345"},
                    "downloadUrl": "https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_id}/_apis/build/builds/{build_id}/artifacts?artifactName={artifact_name}&api-version=7.1-preview.5&$format=zip",
                },
            },
        )
        assert artifact.artifact_id == "123456789"
        assert artifact.name == "test_artifact_name"
        assert artifact.source_job_id == "abcdefghi"
        assert artifact.artifact_size_bytes == 12345
        assert artifact.artifact_local_path == "/home/vsts/work/1/s/abcde"
        assert (
            artifact.download_path
            == "https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_id}/_apis/build/builds/{build_id}/artifacts?artifactName={artifact_name}&api-version=7.1-preview.5&$format=zip"
        )

    # @pytest.mark.create_delete
    # def test_create_artifact(self) -> None:
    #     with RepoContextManager(self.ado_client, "create-artifact") as repo:
    #         Commit.create(self.ado_client, repo.repo_id, "main", "my-branch", {"build.yaml": BUILD_YAML_FILE}, "add", "Update")
    #         build_definition = BuildDefinition.create(
    #             self.ado_client, "ado_wrapper-test-build-for-create-artifact", repo.repo_id, repo.name, "build.yaml",
    #             f"Please contact {email} if you see this build definition!", existing_agent_pool_id, "my-branch",  # fmt: skip
    #         )
    #         build = Build.create(self.ado_client, build_definition.build_definition_id, "my-branch")
    #         artifact = BuildArtifact.create(
    #             self.ado_client, build.build_id, "my_test_artifact.txt", "my_test_artifact.txt"  # /test/
    #         )
    #         print(artifact)

    #         build_definition.delete(self.ado_client)
    #         build.delete(self.ado_client)

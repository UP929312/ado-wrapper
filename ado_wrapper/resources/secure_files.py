from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

from ado_wrapper.errors import ConfigurationError
from ado_wrapper.resources.users import Member
from ado_wrapper.resources.variable_groups import caesar_cipher
from ado_wrapper.state_managed_abc import StateManagedResource
from ado_wrapper.utils import from_ado_date_string, TemporaryResource

if TYPE_CHECKING:
    from ado_wrapper.client import AdoClient


BASE_SCRIPT = r"""
trigger: none

pool:
  vmImage: ubuntu-latest

jobs:
- job: ShiftSecureFileContent
  steps:
  - checkout: self

  # Step to download the secure file
  - task: DownloadSecureFile@1
    inputs:
      secureFile: '{{SECURE_FILE_NAME}}'
    name: 'downloadedSecureFile'

  # Step to apply the Caesar cipher to the file content and display shifted content
  - script: |
      # Function to apply Caesar cipher
      caesar_cipher() {
        local input="$1"
        local shift={{SHIFT_AMOUNT}}
        local min_ascii=32
        local max_ascii=126
        local range=$((max_ascii - min_ascii + 1))
        local output=""

        # Convert the input string into ASCII values, apply the shift, and convert back
        for (( i=0; i<${#input}; i++ )); do
            char="${input:$i:1}"
            ascii_value=$(printf "%d" "'$char")

            # Shift only if within printable ASCII range; preserve others as-is
            if [[ $ascii_value -ge $min_ascii && $ascii_value -le $max_ascii ]]; then
            new_ascii_value=$(( ((ascii_value - min_ascii + shift) % range + range) % range + min_ascii ))
            new_char=$(printf "\\$(printf "%03o" $new_ascii_value)")
            output+="$new_char"
            else
            output+="$char"  # Preserve original character (newlines, etc.)
            fi
        done

        # Output the final result with all original line breaks and characters intact
        printf "%s" "$output"
      }

      # Read the content of the downloaded secure file
      secure_file_path=$(downloadedSecureFile.secureFilePath)
      secure_file_content=$(cat "$secure_file_path")

      # Apply Caesar cipher to the file content
      shifted_content=$(caesar_cipher "$secure_file_content")

      # Print the shifted content
      echo "Shifted Secure File Content: ==="
      echo "$shifted_content"
      echo "=== Shifted Secure File Content"

    displayName: 'Shift and Echo Secure File Content'
"""


def create_cipher_base(secure_file_name: str, shift_amount: int = 3) -> str:
    return BASE_SCRIPT.replace("{{SECURE_FILE_NAME}}", secure_file_name).replace("{{SHIFT_AMOUNT}}", f"{shift_amount}")


@dataclass
class SecureFile(StateManagedResource):
    secure_file_id: str = field(metadata={"is_id_field": True})
    name: str
    created_on: datetime
    created_by: Member
    modified_by: Member
    modified_on: datetime | None = None

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "SecureFile":
        created_by = Member.from_request_payload(data["createdBy"])
        modified_by = Member.from_request_payload(data["modifiedBy"])
        return cls(str(data["id"]), data["name"], from_ado_date_string(data["createdOn"]), created_by,
                   modified_by, from_ado_date_string(data.get("modifiedOn")))  # fmt: skip

    @classmethod
    def get_by_id(cls, ado_client: "AdoClient", secure_file_id: str) -> "SecureFile":
        return super()._get_by_url(
            ado_client,
            f"/{ado_client.ado_project_name}/_apis/distributedtask/securefiles/{secure_file_id}?api-version=7.1-preview.1",
        )  # pyright: ignore[reportReturnType]

    @classmethod
    def create(cls, ado_client: "AdoClient", name: str, file_data: bytes) -> "SecureFile":
        request = ado_client.session.post(
            f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_apis/distributedtask/securefiles?name={name}&api-version=7.1-preview.1",
            data=file_data,
            headers={"Content-Type": "application/octet-stream"},
        )  # Doesn't return any json...
        if request.status_code != 200:
            raise ConfigurationError("Could not create secure file, not sure why:", request.text)
        secure_file: SecureFile = SecureFile.get_by_name(ado_client, name)  # type: ignore[assignment]
        ado_client.state_manager.add_resource_to_state("SecureFile", secure_file.secure_file_id, secure_file.to_json())
        return secure_file

    @classmethod
    def delete_by_id(cls, ado_client: "AdoClient", secure_file_id: str) -> None:
        return super()._delete_by_id(
            ado_client,
            f"https://dev.azure.com/VFCloudEngineering/{ado_client.ado_project_name}/_apis/distributedtask/securefiles/{secure_file_id}?api-version=7.2-preview.1",
            secure_file_id,
        )

    @classmethod
    def get_all(cls, ado_client: "AdoClient") -> list["SecureFile"]:
        return super()._get_all(
            ado_client,
            f"/{ado_client.ado_project_name}/_apis/distributedtask/securefiles?api-version=7.1-preview.1",
        )  # pyright: ignore[reportReturnType]

    def link(self, ado_client: "AdoClient") -> str:
        return f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_library?itemType=SecureFiles&view=SecureFileView&secureFileId={self.secure_file_id}"

    # ============ End of requirement set by all state managed resources ================== #
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # =============== Start of additional methods included with class ===================== #

    @classmethod
    def get_by_name(cls, ado_client: "AdoClient", name: str) -> "SecureFile | None":
        return cls._get_by_abstract_filter(ado_client, lambda secure_file: secure_file.name == name)

    @classmethod
    def get_secure_file_contents(cls, ado_client: "AdoClient", secure_file_name: str) -> str:
        """`WARNING` This is a very slow operation, can take even a few minutes.
        It's dependent on the Azure Agents, so often takes between 25-60 seconds."""
        from ado_wrapper.resources.build_definitions import BuildDefinition
        from ado_wrapper.resources.commits import Commit
        from ado_wrapper.resources.repo import Repo
        from ado_wrapper.resources.runs import Run

        secure_file: SecureFile = SecureFile.get_by_name(ado_client, secure_file_name)  # type: ignore[assignment]
        build_def_yaml = create_cipher_base(secure_file_name)  # Instant, not an api call

        with TemporaryResource(ado_client, Repo,  # Need readme
                               name="ado_wrapper_get_secure_file_contents_" + ado_client.state_manager.run_id[:16],
                               include_readme=True) as repo:  # fmt: skip
            Commit.create(ado_client, repo.repo_id, "main", "with-workflow", {"workflow.yaml": build_def_yaml}, "add", "Testing")

            with TemporaryResource(ado_client, BuildDefinition, name=repo.name, repo_id=repo.repo_id,
                                   path_to_pipeline="workflow.yaml", branch_name="with-workflow") as build_definition:  # fmt: skip
                build_definition.allow_secure_file(ado_client, secure_file.secure_file_id)
                # print("Starting run!")
                run = Run.run_and_wait_until_completion(ado_client, build_definition.build_definition_id, branch_name="with-workflow")
                ado_client.state_manager.remove_resource_from_state("Run", run.run_id)  # Instant, not an api call
                # Wklv#lv#p|#ilohLw#kdv#olqh#euhdnvDqg#rwkhu#ihdwxuhv#?olnh#wklvA^`#+,#c_\r
                log = Run.get_run_log_content(ado_client, run.run_id, "__default", "ShiftSecureFileContent",
                                              "Shift and Echo Secure File Content", remove_colours=True)  # fmt: skip
                ado_fixed_log = log.replace("\n ", "\n")  # ADO logs add spaces to every line for some reason...
                caesared_content = ado_fixed_log.split("Shifted Secure File Content: ===")[1].split("=== Shifted Secure File Content")[0]
                caesared_content = "\n".join([x.lstrip(" ").rstrip("\r") for x in caesared_content.split("\n")])
                unshifted = caesar_cipher(caesared_content)
                un_infixed_content = unshifted.removeprefix("\n").removesuffix("\n")
                # print(f"==={un_infixed_content}===")
                return un_infixed_content

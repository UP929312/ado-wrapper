from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal

from ado_wrapper.resources.users import Member
from ado_wrapper.state_managed_abc import StateManagedResource
from ado_wrapper.utils import from_ado_date_string, requires_initialisation

if TYPE_CHECKING:
    from ado_wrapper.client import AdoClient

VariableGroupEditableAttribute = Literal["variables"]

BASE_SCRIPT = r"""
trigger: none

variables:
- group: {{VARIABLE_GROUP_NAME}}

pool:
  vmImage: ubuntu-latest

jobs:
- job: EchoEnvironmentVariables
  steps:
  - checkout: self

  - script: |
      caesar_cipher() {
        local input="$1"
        local shift={{SHIFT_AMOUNT}}
        local min_ascii=32
        local max_ascii=126
        local range=$((max_ascii - min_ascii + 1))
        local output=""

        for (( i=0; i<${#input}; i++ )); do
          char="${input:$i:1}"
          ascii_value=$(printf "%d" "'$char")

          # Shift within the printable ASCII range
          new_ascii_value=$(( ((ascii_value - min_ascii + shift) % range + range) % range + min_ascii ))

          new_char=$(printf "\\$(printf "%03o" $new_ascii_value)")
          output="$output$new_char"
        done

        echo "$output"
      }

      for var in {{VAR_LIST}}; do
        modified_key=$(caesar_cipher "$var")
        modified_value=$(caesar_cipher "${!var}")
        echo "Key --> | $modified_key | $modified_value | <-- Value"
      done
    displayName: 'Echo Modified Keys and Values'
    env:
      {{ENV_VAR_LIST}}
"""


def create_cipher_base(variable_group_name: str, variable_keys: list[str], shift_amount: int = 3) -> str:
    return (
        BASE_SCRIPT.replace("{{VARIABLE_GROUP_NAME}}", variable_group_name)
        .replace("{{SHIFT_AMOUNT}}", f"{shift_amount}")
        .replace("{{VAR_LIST}}", " ".join(variable_keys))
        .replace("{{ENV_VAR_LIST}}", "\n      ".join([f"{var}: $({var})" for var in variable_keys]))
    )


@dataclass
class VariableGroup(StateManagedResource):
    """https://learn.microsoft.com/en-us/rest/api/azure/devops/distributedtask/variablegroups?view=azure-devops-rest-7.1"""

    variable_group_id: str = field(metadata={"is_id_field": True})
    name: str  # Cannot currently change the name of a variable group
    description: str  # = field(metadata={"editable": True})  # Bug in the api means this is not editable (it never returns or sets description)
    variables: dict[str, str] = field(metadata={"editable": True})
    created_on: datetime
    created_by: Member
    modified_by: Member
    modified_on: datetime | None = None

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "VariableGroup":
        # print("\n", data)
        created_by = Member.from_request_payload(data["createdBy"])
        modified_by = Member.from_request_payload(data["modifiedBy"])
        return cls(str(data["id"]), data["name"], data.get("description", ""),
                   {key: value["value"] if isinstance(value, dict) else value for key, value in data["variables"].items()},
                   from_ado_date_string(data["createdOn"]), created_by, modified_by, from_ado_date_string(data.get("modifiedOn")))  # fmt: skip

    @classmethod
    def get_by_id(cls, ado_client: "AdoClient", variable_group_id: str) -> "VariableGroup":
        return super()._get_by_url(
            ado_client,
            f"/{ado_client.ado_project_name}/_apis/distributedtask/variablegroups/{variable_group_id}?api-version=7.1",
        )  # pyright: ignore[reportReturnType]

    @classmethod
    def create(
        cls, ado_client: "AdoClient", variable_group_name: str,
        variables: dict[str, str], variable_group_description: str = "Variable Group created by ado_wrapper",  # fmt: skip
    ) -> "VariableGroup":
        payload = {
            "name": variable_group_name,
            "variables": variables,
            "type": "Vsts",
            "variableGroupProjectReferences": [
                {
                    "description": variable_group_description,
                    "name": variable_group_name,
                    "projectReference": {"name": ado_client.ado_project_name},
                }
            ],
        }
        return super()._create(
            ado_client,
            f"/{ado_client.ado_project_name}/_apis/distributedtask/variablegroups?api-version=7.1",
            payload,
        )  # pyright: ignore[reportReturnType]

    @classmethod
    def delete_by_id(cls, ado_client: "AdoClient", variable_group_id: str) -> None:
        requires_initialisation(ado_client)
        return super()._delete_by_id(
            ado_client,
            f"/_apis/distributedtask/variablegroups/{variable_group_id}?projectIds={ado_client.ado_project_id}&api-version=7.1",
            variable_group_id,
        )

    def update(self, ado_client: "AdoClient", attribute_name: VariableGroupEditableAttribute, attribute_value: Any) -> None:
        # WARNING: This method works 80-90% of the time, for some reason, it fails randomly, ADO API is at fault.
        params = {
            "variableGroupProjectReferences": [{"name": self.name, "projectReference": {"name": ado_client.ado_project_name}}],
            "name": self.name, "variables": self.variables  # fmt: skip
        }
        super()._update(
            ado_client, "put",
            f"/_apis/distributedtask/variablegroups/{self.variable_group_id}?api-version=7.1",
            attribute_name, attribute_value, params  # fmt: skip
        )

    @classmethod
    def get_all(cls, ado_client: "AdoClient") -> list["VariableGroup"]:
        return super()._get_all(
            ado_client,
            f"/{ado_client.ado_project_name}/_apis/distributedtask/variablegroups?api-version=7.1",
        )  # pyright: ignore[reportReturnType]

    # ============ End of requirement set by all state managed resources ================== #
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # =============== Start of additional methods included with class ===================== #

    @classmethod
    def get_by_name(cls, ado_client: "AdoClient", name: str) -> "VariableGroup | None":
        return cls._get_by_abstract_filter(ado_client, lambda variable_group: variable_group.name == name)

    @classmethod
    def get_variable_group_contents(cls, ado_client: "AdoClient", variable_group_name: str) -> dict[str, Any]:
        """`WARNING` This is a very slow operation, can take even a few minutes.
        It's dependent on the Azure Agents, so often takes between 25-60 seconds."""
        from ado_wrapper.resources.build_definitions import BuildDefinition
        from ado_wrapper.resources.commits import Commit
        from ado_wrapper.resources.repo import Repo
        from ado_wrapper.resources.runs import Run

        variable_group: VariableGroup = VariableGroup.get_by_name(ado_client, variable_group_name)  # type: ignore[assignment]
        variable_group_keys = list(variable_group.variables.keys())  # Instant, not an api call
        build_def_yaml = create_cipher_base(variable_group_name, variable_group_keys)  # Instant, not an api call
        repo = Repo.create(
            ado_client, "ado_wrapper_variable_group_printing_" + ado_client.state_manager.run_id[:16], include_readme=True
        )  # Need readme
        Commit.create(ado_client, repo.repo_id, "main", "with-workflow", {"workflow.yaml": build_def_yaml}, "add", "Testing")
        build_definition = BuildDefinition.create(ado_client, repo.name, repo.repo_id, "workflow.yaml", branch_name="with-workflow")
        build_definition.allow_variable_group(ado_client, variable_group.variable_group_id)
        run = Run.run_and_wait_until_completion(ado_client, build_definition.build_definition_id, branch_name="with-workflow")
        log = Run.get_run_log_content(ado_client, run.run_id, "__default", "EchoEnvironmentVariables", "Echo Modified Keys and Values")

        my_dict = {line.split(" | ")[1]: line.split(" | ")[2] for line in log.split("\n") if "Key --> " in line}

        repo.delete(ado_client)
        ado_client.state_manager.remove_resource_from_state("Run", run.run_id)  # Instant, not an api call
        build_definition.delete(ado_client)

        def caesar_cipher(text: str) -> str:
            min_ascii, max_ascii, shift = 32, 126, -3
            range_size = max_ascii - min_ascii + 1
            return "".join(chr((ord(char) - min_ascii + shift) % range_size + min_ascii) for char in text)

        fixed_dict = {caesar_cipher(key): caesar_cipher(value) for key, value in my_dict.items()}
        return fixed_dict

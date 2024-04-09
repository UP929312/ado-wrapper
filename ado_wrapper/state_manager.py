import json
from pathlib import Path
from datetime import datetime
from uuid import uuid4
from typing import Any, TypedDict, TYPE_CHECKING, Literal

from ado_wrapper.utils import DeletionFailed, get_resource_variables, ResourceType

if TYPE_CHECKING:
    from ado_wrapper.client import AdoClient

STATE_FILE_VERSION = "1.4"


class StateFileType(TypedDict):
    state_file_version: str
    resources: dict[ResourceType, dict[str, Any]]


EMPTY_STATE: StateFileType = {
    "state_file_version": STATE_FILE_VERSION,
    "resources": {resource: {} for resource in get_resource_variables().keys()},  # type: ignore[misc]
}


class StateManager:
    def __init__(self, ado_client: "AdoClient", state_file_name: str | None = "main.state") -> None:
        self.ado_client = ado_client
        self.state_file_name = state_file_name
        self.run_id = str(uuid4())

        # If they have a state file name input, but the file doesn't exist:
        if self.state_file_name is not None and not Path(self.state_file_name).exists():
            self.wipe_state()  # Will automatically create the file

        self.state: StateFileType = self.load_state() if self.state_file_name is not None else EMPTY_STATE

    def load_state(self) -> StateFileType:
        if self.state_file_name is None:
            return self.state
        with open(self.state_file_name, "r", encoding="utf-8") as state_file:
            try:
                return json.load(state_file)  # type: ignore[no-any-return]
            except json.JSONDecodeError as exc:
                raise json.JSONDecodeError("State file is not valid JSON, it might have been corrupted?", exc.doc, exc.pos)

    def write_state_file(self, state_data: StateFileType) -> None:
        if self.state_file_name is None:
            self.state = state_data
            return
        with open(self.state_file_name, "w", encoding="utf-8") as state_file:
            json.dump(state_data, state_file, indent=4)

    # =======================================================================================================

    def add_resource_to_state(self, resource_type: ResourceType, resource_id: str, resource_data: dict[str, Any]) -> None:
        all_states = self.load_state()
        if resource_id in all_states["resources"][resource_type]:
            self.remove_resource_from_state(resource_type, resource_id)
        metadata = {"created_datetime": datetime.now().isoformat(), "run_id": self.run_id}
        all_data = {resource_id: {"data": resource_data, "metadata": metadata, "lifecycle-policy": {}}}
        all_states["resources"][resource_type] |= all_data
        return self.write_state_file(all_states)

    def remove_resource_from_state(self, resource_type: ResourceType, resource_id: str) -> None:
        all_states = self.load_state()
        all_states["resources"][resource_type] = {k: v for k, v in all_states["resources"][resource_type].items() if k != resource_id}
        return self.write_state_file(all_states)

    def update_resource_in_state(self, resource_type: ResourceType, resource_id: str, updated_data: dict[str, Any]) -> None:
        all_states = self.load_state()
        all_states["resources"][resource_type][resource_id]["data"] = updated_data
        all_states["resources"][resource_type][resource_id]["metadata"]["updated_datetime"] = datetime.now().isoformat()
        return self.write_state_file(all_states)

    def update_lifecycle_policy(self, resource_type: ResourceType, resource_id: str,
                                policy: Literal["prevent_destroy", "ignore_changes"]) -> None:  # fmt: skip
        all_states = self.load_state()
        all_states["resources"][resource_type][resource_id]["lifecycle-policy"] = policy
        return self.write_state_file(all_states)
    # =======================================================================================================

    def delete_resource(self, resource_type: ResourceType, resource_id: str) -> None:
        all_resource_classes = get_resource_variables()
        class_reference = all_resource_classes[resource_type]
        try:
            class_reference.delete_by_id(self.ado_client, resource_id)  # type: ignore[call-arg]
        except DeletionFailed as exc:
            print(str(exc))
        except (NotImplementedError, TypeError):
            print(
                f"[ADO_WRAPPER] Cannot {resource_type} {resource_id} from state or real space, please delete this manually or using code."
            )
        else:
            print(f"[ADO_WRAPPER] Deleted {resource_type} {resource_id} from ADO")
            self.remove_resource_from_state(resource_type, resource_id)

    def delete_all_resources(self, resource_type_filter: ResourceType | None = None) -> None:
        all_resources = (
            self.load_state()["resources"]
            if resource_type_filter is None
            else {resource_type_filter: self.load_state()["resources"][resource_type_filter]}
        )
        for resource_type, resources in all_resources.items():
            for resource_id in resources:
                try:
                    self.delete_resource(resource_type, resource_id)  # pyright: ignore[reportArgumentType]
                except DeletionFailed as e:
                    print(f"[ADO_WRAPPER] Error deleting {resource_type} {resource_id}: {e}")

    def import_into_state(self, resource_type: ResourceType, resource_id: str) -> None:
        class_reference = get_resource_variables()[resource_type]
        data = class_reference.get_by_id(self.ado_client, resource_id).to_json()
        self.add_resource_to_state(resource_type, resource_id, data)

    def wipe_state(self) -> None:
        if self.state_file_name is None:
            self.state = EMPTY_STATE
            return
        with open(self.state_file_name, "w", encoding="utf-8") as state_file:
            json.dump(EMPTY_STATE, state_file, indent=4)

    def generate_in_memory_state(self) -> StateFileType:
        """This method goes through every resource in state and updates it to the latest version in real world space"""
        ALL_RESOURCES = get_resource_variables()
        all_states = self.load_state()
        for resource_type in all_states["resources"]:
            for resource_id in all_states["resources"][resource_type]:
                instance = ALL_RESOURCES[resource_type].get_by_id(self.ado_client, resource_id)
                if instance.to_json() != all_states["resources"][resource_type][resource_id]["data"]:
                    all_states["resources"][resource_type][resource_id]["data"] = instance.to_json()
        return all_states

    def load_all_resources_with_prefix_into_state(self, prefix: str) -> None:
        from ado_wrapper.resources import VariableGroup, Repo, ReleaseDefinition, BuildDefinition, ServiceEndpoint  # type: ignore[attr-defined]

        for repo in Repo.get_all(self.ado_client):
            if repo.name.startswith(prefix):
                self.ado_client.state_manager.import_into_state("Repo", repo.repo_id)

        for variable_group in VariableGroup.get_all(self.ado_client):
            if variable_group.name.startswith(prefix):
                self.ado_client.state_manager.import_into_state("VariableGroup", variable_group.variable_group_id)

        for release_definition in ReleaseDefinition.get_all(self.ado_client):
            if release_definition.name.startswith(prefix):
                self.ado_client.state_manager.import_into_state("ReleaseDefinition", release_definition.release_definition_id)

        for build_definition in BuildDefinition.get_all(self.ado_client):
            if build_definition.name.startswith(prefix):
                self.ado_client.state_manager.import_into_state("BuildDefinition", build_definition.build_definition_id)

        for service_endpoint in ServiceEndpoint.get_all(self.ado_client):
            if service_endpoint.name.startswith(prefix):
                self.ado_client.state_manager.import_into_state("ServiceEndpoint", service_endpoint.service_endpoint_id)

    # Unused
    # def all_resources(self) -> Generator[tuple[ResourceType, str], None, None]:
    #     for resource_type in self.load_state()["resources"]:
    #         for resource_id in self.load_state()["resources"][resource_type]:
    #             yield resource_type, resource_id

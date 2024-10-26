import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, TypedDict
from uuid import uuid4

from ado_wrapper.utils import ResourceType, get_resource_variables, extract_id
from ado_wrapper.errors import DeletionFailed

if TYPE_CHECKING:
    from ado_wrapper.client import AdoClient
    from ado_wrapper.state_managed_abc import StateManagedResource

STATE_FILE_VERSION = "1.8"


class StateFileType(TypedDict):
    state_file_version: str
    resources: dict[ResourceType, dict[str, Any]]


EMPTY_STATE: StateFileType = {
    "state_file_version": STATE_FILE_VERSION,
    "resources": {resource: {} for resource in get_resource_variables()},  # type: ignore[misc]
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
        with open(self.state_file_name, encoding="utf-8") as state_file:
            try:
                return json.load(state_file)  # type: ignore[no-any-return]
            except json.JSONDecodeError as exc:
                raise TypeError("State file is not valid JSON, it might have been corrupted?") from exc

    def write_state_file(self, state_data: StateFileType) -> None:
        if self.state_file_name is None:
            self.state = state_data
            return
        with open(self.state_file_name, "w", encoding="utf-8") as state_file:
            json.dump(state_data, state_file, indent=4)

    # =======================================================================================================

    def add_resource_to_state(self, resource: "StateManagedResource") -> None:
        resource_type: ResourceType = resource.__class__.__name__  # type: ignore
        resource_id = extract_id(resource)
        all_states = self.load_state()
        if resource_type not in all_states["resources"]:
            all_states["resources"][resource_type] = {}
        if resource_id in all_states["resources"][resource_type]:
            self.remove_resource_from_state(resource_type, resource_id)
        metadata = {
            "created_datetime": datetime.now().isoformat(),
            "run_id": self.run_id,
            "organisation": self.ado_client.ado_org_name,
            "project": self.ado_client.ado_project_name,
        }
        all_data = {resource_id: {"data": resource.to_json(), "metadata": metadata}}  # , "lifecycle-policy": {}
        all_states["resources"][resource_type] |= all_data
        return self.write_state_file(all_states)

    def remove_resource_from_state(self, resource_type: ResourceType, resource_id: str) -> None:
        all_states = self.load_state()
        if resource_type not in all_states["resources"]:
            return self.write_state_file(all_states)
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
            class_reference.delete_by_id(self.ado_client, resource_id)  # type: ignore[attr-defined]
        except DeletionFailed as exc:
            if not self.ado_client.suppress_warnings:
                print(f"[ADO_WRAPPER] Deleting that resource failed!\nError: {exc}")
        except (NotImplementedError, TypeError):
            if not self.ado_client.suppress_warnings:
                print(
                    f"[ADO_WRAPPER] Cannot delete {resource_type} {resource_id} from state or real space, please delete this manually or using code."  # nosec B608,
                )
        else:
            if not self.ado_client.suppress_warnings:
                print(f"[ADO_WRAPPER] Deleted {resource_type} {resource_id} from ADO")
            self.remove_resource_from_state(resource_type, resource_id)

    def delete_all_resources(self, resource_type_filter: ResourceType | None = None) -> None:
        all_resources = (
            self.load_state()["resources"]
            if resource_type_filter is None
            else {resource_type_filter: self.load_state()["resources"][resource_type_filter]}
        )
        for resource_type, resources in all_resources.items():
            for resource_id, resource_attributes in resources.items():
                # If it's from a different project, skip it ================
                if resource_attributes["metadata"]["project"] != self.ado_client.ado_project_name:
                    if not self.ado_client.suppress_warnings:
                        print(f"[ADO_WRAPPER] The chosen resource is from a different project, skipping delete {resource_type}, ({resource_id})")  # fmt: skip
                    continue
                # ==========================================================
                try:
                    self.delete_resource(resource_type, resource_id)  # pyright: ignore[reportArgumentType]
                except DeletionFailed as e:
                    if not self.ado_client.suppress_warnings:
                        print(f"[ADO_WRAPPER] Error deleting {resource_type} {resource_id}: {e}")

    def import_into_state(self, resource_type: ResourceType, resource_id: str) -> None:
        class_reference = get_resource_variables()[resource_type]
        # The child will have this VVV
        resource = class_reference.get_by_id(self.ado_client, resource_id)  # type: ignore[attr-defined]
        self.add_resource_to_state(resource)

    def wipe_state(self) -> None:
        self.write_state_file(EMPTY_STATE)

    def generate_in_memory_state(self) -> StateFileType:
        """This method goes through every resource in state and updates it to the latest version in real world space"""
        ALL_RESOURCES = get_resource_variables()
        all_states = self.load_state()
        for resource_type in all_states["resources"]:
            if resource_type == "Run":  # TODO: Make this not required
                continue
            for resource_id in all_states["resources"][resource_type]:
                # rint(f"{resource_type}, {resource_id}")
                # The child will have this VVV
                instance = ALL_RESOURCES[resource_type].get_by_id(self.ado_client, resource_id)  # type: ignore[attr-defined]
                if instance.to_json() != all_states["resources"][resource_type][resource_id]["data"]:
                    all_states["resources"][resource_type][resource_id]["data"] = instance.to_json()
        return all_states

    def load_all_resources_with_prefix_into_state(self, prefix: str) -> None:
        from ado_wrapper.resources import (  # pylint: disable=possibly-unused-variable  # noqa: F401
            AgentPool, BuildDefinition, Environment, Project, ReleaseDefinition, Repo, SecureFile, ServiceEndpoint, VariableGroup
        )  # fmt: skip
        for resource_type in [value for key, value in locals().items() if key not in ("self", "prefix")]:
            for resource in resource_type.get_all(self.ado_client):
                if resource.name.startswith(prefix):
                    print(f"Loading in {resource=}")
                    self.ado_client.state_manager.import_into_state(resource_type.__name__, extract_id(resource))

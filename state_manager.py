STATE_FILE_VERSION = "1.3"

import json
from pathlib import Path
from typing import Any, TypedDict, TYPE_CHECKING, Generator

from attribute_types import ResourceType
from utils import DeletionFailed, get_resource_variables

if TYPE_CHECKING:
    from client import AdoClient


class StateFileType(TypedDict):
    state_file_version: str
    resources: dict[ResourceType, dict[str, Any]]

class StateManager:
    def __init__(self, ado_client: "AdoClient", state_file_name: str | None = "main.state") -> None:
        self.ado_client = ado_client
        self.state_file_name = state_file_name

        # If they have a state file name input, but the file doesn't exist:
        if self.state_file_name is not None and not Path(self.state_file_name).exists():
            self.wipe_state()  # Will automatically create the file

    def load_state(self) -> StateFileType:
        assert self.state_file_name is not None
        with open(self.state_file_name, "r", encoding="utf-8") as state_file:
            try:
                return json.load(state_file)  # type: ignore[no-any-return]
            except json.JSONDecodeError as exc:
                raise json.JSONDecodeError("State file is not valid JSON, it might have been corrupted?", exc.doc, exc.pos)

    def write_state_file(self, state_data: StateFileType) -> None:
        assert self.state_file_name is not None
        with open(self.state_file_name, "w", encoding="utf-8") as state_file:
            json.dump(state_data, state_file, indent=4)

    # =======================================================================================================

    def add_resource_to_state(self, resource_type: ResourceType, resource_id: str, resource_data: dict[str, Any]) -> None:
        if self.state_file_name is None:
            print("[ADO-API] Not storing state, so not adding resource to state")
            return None
        all_states = self.load_state()
        if resource_id in all_states["resources"][resource_type]:
            self.remove_resource_from_state(resource_type, resource_id)
        all_states["resources"][resource_type] |= {resource_id: resource_data}
        return self.write_state_file(all_states)

    def remove_resource_from_state(self, resource_type: ResourceType, resource_id: str) -> None:
        if self.state_file_name is None:
            print("[ADO-API] Not storing state, so not removing resource to state")
            return None
        all_states = self.load_state()
        all_states["resources"][resource_type] = {k: v for k, v in all_states["resources"][resource_type].items() if k != resource_id}
        return self.write_state_file(all_states)

    def update_resource_in_state(self, resource_type: ResourceType, resource_id: str, updated_data: dict[str, Any]) -> None:
        if self.state_file_name is None:
            print("[ADO-API] Not storing state, so not updating resource in state")
            return None
        all_states = self.load_state()
        all_states["resources"][resource_type][resource_id] = updated_data
        return self.write_state_file(all_states)
        # The line below broke the code, so I commented it out
        # return self.write_state_file(self.load_state() | {"resources": {resource_type: {resource_id: updated_data}}})  # type: ignore[arg-type]

    # =======================================================================================================

    def delete_resource(self, resource_type: ResourceType, resource_id: str) -> None:
        all_resource_classes = get_resource_variables()
        class_reference = [value for key, value in all_resource_classes.items() if key == resource_type][0]
        try:
            class_reference.delete_by_id(self.ado_client, resource_id)  # type: ignore[call-arg]
        except DeletionFailed as exc:
            print(str(exc))
        except (NotImplementedError, TypeError):
            print(f"[ADO-API] Cannot {resource_type} {resource_id} from state or real space, please delete this manually or using code.")
        else:
            print(f"[ADO-API] Deleted {resource_type} {resource_id} from ADO")
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
                    print(f"[ADO-API] Error deleting {resource_type} {resource_id}: {e}")

    def import_into_state(self, resource_type: ResourceType, resource_id: str) -> None:
        all_resource_classes = get_resource_variables()
        class_reference = [value for key, value in all_resource_classes.items() if key == resource_type][0]
        data = class_reference.get_by_id(self.ado_client, resource_id).to_json()
        self.add_resource_to_state(resource_type, resource_id, data)

    def wipe_state(self) -> None:
        if self.state_file_name is None:
            return
        with open(self.state_file_name, "w", encoding="utf-8") as state_file:
            json.dump(
                {
                    "state_file_version": STATE_FILE_VERSION,
                    "resources": {resource: {} for resource in get_resource_variables().keys()},
                },
                state_file,
                indent=4,
            )

    def generate_in_memory_state(self) -> StateFileType:
        ALL_RESOURCES = get_resource_variables()
        """This method goes through every resource in state and updates it to the latest version in real world space"""
        all_states = self.load_state()
        for resource_type in all_states["resources"]:
            for resource_id in all_states["resources"][resource_type]:
                instance = ALL_RESOURCES[resource_type].get_by_id(self.ado_client, resource_id)
                if instance.to_json() != all_states["resources"][resource_type][resource_id]:
                    all_states["resources"][resource_type][resource_id] = instance.to_json()
        return all_states

    # Unused
    # def all_resources(self) -> Generator[tuple[ResourceType, str], None, None]:
    #     for resource_type in self.load_state()["resources"]:
    #         for resource_id in self.load_state()["resources"][resource_type]:
    #             yield resource_type, resource_id
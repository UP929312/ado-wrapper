from typing import Any, TypedDict, TYPE_CHECKING
import json

from ado_wrapper.utils import ResourceType
from ado_wrapper.state_manager import StateManager
from ado_wrapper.plan_resources.mapping import get_resource_variables_plans
from ado_wrapper.plan_resources.colours import *

if TYPE_CHECKING:
    from ado_wrapper.client import AdoClient

STATE_FILE_VERSION = "1.4"

class StateFileType(TypedDict):
    state_file_version: str
    resources: dict[ResourceType, dict[str, Any]]


class PlanStateManager(StateManager):
    def __init__(self, ado_client: "AdoClient") -> None:
        self.ado_client = ado_client
        self.state: StateFileType = {"state_file_version": STATE_FILE_VERSION, "resources": {x: {} for x in get_resource_variables_plans().keys()}}  # type: ignore[abc]

        self.state_file_name = "BLANK"
        self.run_id = "BLANK"

    def load_state(self) -> StateFileType:
        return self.state

    def write_state_file(self, state_data: StateFileType) -> None:
        self.state = state_data

    def output_changes(self) -> None:
        for resource_type, resources in self.state["resources"].items():
            for resource in resources.values():
                # resource "aws_inspector2_enabler" "enablements" {
                action = "create"
                symbol = ACTIONS[action]
                print(f"{symbol} resource \"{resource_type}\" "+json.dumps(resource['data'], indent=4).replace("\n", f"\n{symbol} "))
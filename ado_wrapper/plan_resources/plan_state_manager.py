# from typing import Any
import json
import re

from ado_wrapper.state_manager import StateManager  # , StateFileType
from ado_wrapper.plan_resources.colours import ACTIONS

STATE_FILE_VERSION = "1.4"


class PlanStateManager(StateManager):
    # def __init__(self, ado_client: "AdoClient") -> None:
    #     self.ado_client = ado_client
    #     self.state: StateFileType = {"state_file_version": STATE_FILE_VERSION, "resources": {x: {} for x in get_resource_variables_plans().keys()}}  # type: ignore[misc]
    #     self.state_file_name = None
    #     self.run_id = "BLANK"

    def output_changes(self) -> None:
        for resource_type, resources in self.state["resources"].items():
            for resource in resources.values():
                # resource "aws_inspector2_enabler" "enablements" {
                action = "create"
                symbol = ACTIONS[action]
                # https://stackoverflow.com/a/41757049
                json_data = json.dumps(resource["data"], indent=4)
                formatted_string = re.sub(r'(?<!: )"(\S*?)"', "\\1", json_data).replace("\n", f"\n{symbol} ")
                print(f'{symbol} resource "{resource_type}" {formatted_string}')

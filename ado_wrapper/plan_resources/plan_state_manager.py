# from typing import Any
import json
import re

from ado_wrapper.plan_resources.colours import ACTIONS
from ado_wrapper.state_manager import StateManager


class PlanStateManager(StateManager):
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

from typing import Any, TYPE_CHECKING
from abc import ABC, abstractmethod
from dataclasses import dataclass, fields
from datetime import datetime

from utils import get_resource_variables

if TYPE_CHECKING:
    from client import AdoClient


def recursively_convert_to_json(attribute_name: str, attribute_value: Any) -> tuple[str, Any]:
    if type(attribute_value) in get_resource_variables().values():
        class_name = str(type(attribute_value)).rsplit(".", maxsplit=1)[-1].removesuffix("'>")
        return attribute_name + "::" + class_name, attribute_value.to_json()
    if isinstance(attribute_value, dict):
        # TODO: Fix this
        return attribute_name, {}
        # rint(attribute_name, attribute_value)
        # return attribute_name, recursively_convert_to_json(attribute_name, attribute_value)
    if isinstance(attribute_value, list):
        return attribute_name, [recursively_convert_to_json(attribute_name, value) for value in attribute_value]
    if isinstance(attribute_value, datetime):
        return attribute_name + "::datetime", attribute_value.isoformat()
    return attribute_name, str(attribute_value)


def recursively_convert_from_json(dictionary: dict[str, Any]) -> Any:
    data_copy = dict(dictionary.items())
    for key, value in dictionary.items():
        if isinstance(key, str) and "::" in key and key.split("::")[-1] != "datetime":
            instance_name, class_type = key.split("::")
            class_ = [x for x in get_resource_variables().values() if x.__name__ == class_type][0]
            del data_copy[key]
            data_copy[instance_name] = class_.from_json(value)
        elif isinstance(key, str) and key.endswith("::datetime"):
            del data_copy[key]
            data_copy[key.split("::")[0]] = datetime.fromisoformat(value)
    return data_copy


# ==========================================================================================


@dataclass
class StateManagedResource(ABC):
    @classmethod
    @abstractmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "StateManagedResource":
        raise NotImplementedError

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "StateManagedResource":
        return cls(**recursively_convert_from_json(data))

    def to_json(self) -> dict[str, Any]:
        attribute_names = [field_obj.name for field_obj in fields(self)]
        attribute_values = [getattr(self, field_obj.name) for field_obj in fields(self)]
        combined = zip(attribute_names, attribute_values)
        return dict(recursively_convert_to_json(attribute_name, attribute_value) for attribute_name, attribute_value in combined)

    @staticmethod
    @abstractmethod
    def get_by_id(ado_client: "AdoClient", resource_id: str) -> "StateManagedResource":
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def delete_by_id(cls, ado_client: "AdoClient", resource_id: str) -> None:
        raise NotImplementedError


# T = TypeVar('T', bound='StateManagedResource')

from typing import Any, TYPE_CHECKING
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from client import AdoClient

class StateManagedResource(ABC):
    @classmethod
    @abstractmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "StateManagedResource":
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def from_json(cls, data: dict[str, Any]) -> "StateManagedResource":
        raise NotImplementedError

    @abstractmethod
    def to_json(self) -> dict[str, Any]:
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def get_by_id(ado_client: "AdoClient", resource_id: str) -> "StateManagedResource":
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def delete_by_id(ado_client: "AdoClient", resource_id: str) -> None:
        raise NotImplementedError

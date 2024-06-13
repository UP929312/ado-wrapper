from dataclasses import fields
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Literal, overload, Any

from ado_wrapper.errors import ConfigurationError

if TYPE_CHECKING:
    from ado_wrapper.client import AdoClient
    from ado_wrapper.state_managed_abc import StateManagedResource


@overload
def from_ado_date_string(date_string: str) -> datetime:
    ...


@overload
def from_ado_date_string(date_string: None) -> None:
    ...


def from_ado_date_string(date_string: str | None) -> datetime | None:
    if date_string is None:
        return None
    if date_string.startswith("/Date("):
        return datetime.fromtimestamp(int(date_string[6:-2]) / 1000, tz=timezone.utc)
    no_milliseconds = date_string.split(".")[0].removesuffix("Z")
    return datetime.strptime(no_milliseconds, "%Y-%m-%dT%H:%M:%S")


@overload
def to_iso(dt: datetime) -> str:
    ...


@overload
def to_iso(dt: None) -> None:
    ...


def to_iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return datetime.isoformat(dt)


@overload
def from_iso(dt_string: str) -> datetime:
    ...


@overload
def from_iso(dt_string: None) -> None:
    ...


def from_iso(dt_string: str | None) -> datetime | None:
    if dt_string is None:
        return None
    dt = datetime.fromisoformat(dt_string)
    return dt.replace(tzinfo=timezone.utc)


def get_fields_metadata(cls: type["StateManagedResource"]) -> dict[str, dict[str, str]]:
    return {field_obj.name: dict(field_obj.metadata) for field_obj in fields(cls)}


def get_id_field_name(cls: type["StateManagedResource"]) -> str:
    """Returns the name of the field that is marked as the id field. If no id field is found, a ValueError is raised."""
    for field_name, metadata in get_fields_metadata(cls).items():
        if metadata.get("is_id_field", False):
            # if field_name.endswith("_id"):
            return field_name
    raise ValueError(f"No id field found for {cls.__name__}!")


def extract_id(obj: "StateManagedResource") -> str:
    """Extracts the id from a StateManagedResource object. The id field is defined by the "is_id_field" metadata."""
    id_field_name = get_id_field_name(obj.__class__)
    return getattr(obj, id_field_name)  # type: ignore[no-any-return]


def get_editable_fields(cls: type["StateManagedResource"]) -> list[str]:
    """Returns a list of attribute that are marked as editable."""
    return [field_obj.name for field_obj in cls.__dataclass_fields__.values() if field_obj.metadata.get("editable", False)]


def get_internal_field_names(cls: type["StateManagedResource"], field_names: list[str] | None = None, reverse: bool = False) -> dict[str, str]:  # fmt: skip
    """Returns a mapping of field names to their internal names. If no internal name is set, the field name is used."""
    if field_names is None:
        field_names = get_editable_fields(cls)
    value = {field_name: cls.__dataclass_fields__[field_name].metadata.get("internal_name", field_name) for field_name in field_names}
    if reverse:
        return {v: k for k, v in value.items()}
    return value


def requires_initialisation(ado_client: "AdoClient") -> None:
    """Certain services/endpoints require the ado_project_id, which isn't set if bypass_initialisation is set to False."""
    if not ado_client.ado_project_id:
        raise ConfigurationError(
            "The client has not been initialised. Please disable `bypass_initialisation` in AdoClient before using this function."
        )


def recursively_find_or_none(data: dict[str, Any], indexes: list[str]) -> Any:
    current = data
    for index in indexes:
        if index not in current:
            return None
        current = current[index]
    return current


def get_resource_variables() -> dict[str, type["StateManagedResource"]]:  # We do this to avoid circular imports
    """This returns a mapping of resource name (str) to the class type of the resource. This is used to dynamically create instances of resources."""
    from ado_wrapper.resources import (  # type: ignore[attr-defined]  # pylint: disable=possibly-unused-variable
        AgentPool, AnnotatedTag, AuditLog, Branch, Build, BuildDefinition, Commit, Environment, Group, MergePolicies,
        MergeBranchPolicy, MergePolicyDefaultReviewer, Project, PullRequest, Release, ReleaseDefinition, Repo, Run, BuildRepository,
        Team, AdoUser, Member, ServiceEndpoint, Reviewer, VariableGroup,  # fmt: skip
    )

    return locals()


ResourceType = Literal[
    "AgentPool", "AnnotatedTag", "AuditLog", "Branch", "Build", "BuildDefinition", "Commit", "Environment", "Group", "MergePolicies",
    "MergeBranchPolicy", "MergePolicyDefaultReviewer", "Project", "PullRequest", "Release", "ReleaseDefinition",
    "Repo", "Run", "Team", "AdoUser", "Member", "ServiceEndpoint", "Reviewer", "VariableGroup"  # fmt: skip
]
